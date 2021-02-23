from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, ConcreteBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import *
from sqlalchemy import exc
from datetime import datetime, timedelta
from random import randint
import logging
import requests
import datetime
import time
import os


logging.basicConfig(filename='dbikes.log', 
                    format='%(asctime)s [%(levelname)s] %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S%p',level=logging.INFO)

# connection info jcdecaux
APIKEY = os.environ.get('JCD_API_KEY') 
NAME = "Dublin"
STATION_URI = "https://api.jcdecaux.com/vls/v1/stations"

def get_data(uri=None, key=None, name=None):
    return requests.get(uri, params={"apiKey" : key, "contract" : name}).json()

def map_static_data(obj):
    """
        Function to return a dictionary mapped from obj.
        Used for the static table.
    """

    return {'Number' : obj['number'],
            'Name' : obj['name'],
            'Address' : obj['address'],
            'PosLat' : obj['position']['lat'],
            'PosLng' : obj['position']['lng'],
            'BikeStands' : obj['bike_stands'],   
            'LastUpdate' : datetime.datetime.fromtimestamp(int(obj['last_update'] / 1e3)) }

def map_dynamic_data(obj):        
    """
        Function to return a dictionary mapped from obj.
        Used for the dynamic table.
    """
    
    return {'Number' : obj['number'],
            'Status' : obj['status'],
            'AvailableBikeStands' : obj['available_bike_stands'],
            'BikeStands' : obj['available_bikes'],
            'LastUpdate' : datetime.datetime.fromtimestamp(int(obj['last_update'] / 1e3)) }



# connection info DB
DB_NAME = os.environ.get('DB_DBIKES_USER')
DB_PASS = os.environ.get('DB_DBIKES_PASS')
DB_HOST = os.environ.get('DB_DBIKES')

Base = declarative_base()

class StaticStations(Base):      
    """
        Class constructor for the StaticStations table.
    """
        
    __tablename__ = "static_stations"
    Id = Column(Integer, primary_key=True)
    Number = Column(Integer)
    Name = Column(String(128))
    Address = Column(String(128))
    PosLat = Column(Float)
    PosLng = Column(Float)
    BikeStands = Column(Integer)
    LastUpdate = Column(DateTime)

    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Number='%s', Name='%s', Address='%s', PosLat='%s', PosLng='%s', BikeStands='%s', LastUpdate='%s')>" \
                % (self.Id, self.Number, self.Name, self.Address, self.PosLat, self.PosLng, self.BikeStands, self.LastUpdate)
    
    
    
class DynamicStations(Base):
    """
        Class constructor for the DynamicStations table.
    """

    __tablename__ = "dynamic_stations"
    Id = Column(Integer, primary_key=True)
    Number = Column(Integer)
    Status = Column(String(128))
    AvailableBikeStands = Column(Integer)
    BikeStands = Column(Integer)
    LastUpdate = Column(DateTime)

    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Number='%s', Status='%s', AvailableBikeStands='%s', BikeStands='%s', LastUpdate='%s')>" \
                % (self.Id, self.Number, self.Status, self.AvailableBikeStands, self.BikeStands, self.LastUpdate)
        


    
def main():    
    # create engine and base
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)    
  
    # create tables if they don't exist.
    StaticStations.__table__.create(bind=engine, checkfirst=True)
    DynamicStations.__table__.create(bind=engine, checkfirst=True)
    
    # start a session 
    Session = sessionmaker(bind=engine)
    session = Session()

    
    # store json data in 'bikes_json'.
    bikes_json = get_data(STATION_URI, APIKEY, NAME)


    # map static data from json file and insert it into the table.
    static_data = list(map(map_static_data, bikes_json))
         
    # check if data already in table and add it if not. 
    # check is performed by number so only adds new stations to the table.
    # this will prevent having duplicates in our static table.
    logging.info("Check static updates")
    for data in static_data:        
        check = data['Number']
        if not session.query(StaticStations).filter_by(Number=f'{check}').first():
            logging.info(f"Update station number {check}")
            session.add(StaticStations(**data))
        session.commit()


    # dynamic data
    retry_count = 0
    while True and retry_count < 10:
        try:
            # collect data from jcdecaux api and insert it into the dynamic table.
            bikes_json = get_data(STATION_URI, APIKEY, NAME)
            dynamic_data = list(map(map_dynamic_data, bikes_json))
            logging.info(f"Insert {len(dynamic_data)} dynamic updates")
            if dynamic_data:
                for data in dynamic_data:
                    session.add(DynamicStations(**data))
                session.commit()
            time.sleep(5*60)

        except requests.exceptions.HTTPError as e:
            # exception on any response considered an error.
            logging.error(f"Error while retrieving station data: {e}")
            time.sleep(1*60)
            continue
            
        except exc.SQLAlchemyError as e:
            logging.error(f"Error while updating station data: {e}")
            retry_count += 1
            continue
        
            
if __name__ == "__main__":
    main()