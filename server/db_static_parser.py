#!/usr/bin/python3

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
import dbinfo


logging.basicConfig(filename='dbikes_static.log', 
                    format='%(asctime)s [%(levelname)s] %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S%p',level=logging.INFO)


# connection info jcdecaux
APIKEY = dbinfo.JCD_API_KEY 
NAME = "Dublin"
STATION_URI = "https://api.jcdecaux.com/vls/v1/stations"


def get_data(uri=None, key=None, name=None):
    return requests.get(uri, params={"apiKey" : key, "contract" : name, "q" : name, "appid" : key}).json()


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
            'LastUpdate' : (None if obj['last_update'] == None else datetime.datetime.fromtimestamp(int(obj['last_update'] / 1e3))),
            'RequestTime' : datetime.datetime.now()}

def map_dynamic_data(obj):        
    """
        Function to return a dictionary mapped from obj.
        Used for the dynamic table.
    """
    
    return {'Number' : obj['number'],
            'Status' : obj['status'],
            'AvailableBikeStands' : obj['available_bike_stands'],
            'BikeStands' : obj['available_bikes'],
            'LastUpdate' : datetime.datetime.now() }


# connection info DB
DB_NAME = dbinfo.DB_DBIKES_USER
DB_PASS = dbinfo.DB_DBIKES_PASS
DB_HOST = dbinfo.DB_DBIKES

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
    RequestTime = Column(DateTime)
 
    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Number='%s', Name='%s', Address='%s', PosLat='%s', PosLng='%s', BikeStands='%s', LastUpdate='%s')>" \
                % (self.Id, self.Number, self.Name, self.Address, self.PosLat, self.PosLng, self.BikeStands, self.LastUpdate)
    
    
    

def main():
    # create engine and base
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)    

    # create tables if they don't exist.
    StaticStations.__table__.create(bind=engine, checkfirst=True)

    # start a session 
    Session = sessionmaker(bind=engine)
    session = Session()


    # store json data in 'bikes_json' and 'weather_json'.
    bikes_json = get_data(STATION_URI, APIKEY, NAME)

    # map static data from json file and insert it into the table.
    static_data = list(map(map_static_data, bikes_json))

    # get the targeted row from the table
    # update all values for the row
    # if the station number doesn't exist in the table add it
    logging.info("Logging static updates")       
    for data in static_data:
        updater = session.query(StaticStations).filter(StaticStations.Number==data['Number']).first()
        if updater:
            updater.Number = data['Number']
            updater.Name = data['Name']
            updater.Address = data['Address']
            updater.PosLat = data['PosLat']
            updater.PosLng = data['PosLng']
            updater.BikeStands = data['BikeStands']
            updater.LastUpdate = datetime.datetime.now()
        else:
            session.add(StaticStations(**data))
    logging.info(f"Updated {len(static_data)} fields")
    session.commit()

if __name__ == "__main__":
    main()
