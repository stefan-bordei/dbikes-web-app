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
import json


logging.basicConfig(filename='dbikes_live.log', 
                    format='%(asctime)s [%(levelname)s] %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S%p',level=logging.INFO)

# connection info jcdecaux
APIKEY = dbinfo.JCD_API_KEY 
NAME = "Dublin"
STATION_URI = "https://api.jcdecaux.com/vls/v1/stations"

# connection info open weather
OW_APIKEY = dbinfo.OW_API_KEY
OW_NAME = "Dublin,IE"
OW_URI = "http://api.openweathermap.org/data/2.5/weather"

def get_data(uri=None, key=None, name=None):
    return requests.get(uri, params={"apiKey" : key, "contract" : name, "q" : name, "appid" : key}).json()


def map_dynamic_data(obj):        
    """
        Function to return a dictionary mapped from obj.
        Used for the dynamic table.
    """
    
    return {'Number' : obj['number'],
            'Status' : obj['status'],
            'AvailableBikeStands' : obj['available_bike_stands'],
            'AvailableBikes' : obj['available_bikes'],
            'LastUpdate' : (None if obj['last_update'] == None else datetime.datetime.fromtimestamp(int(obj['last_update'] / 1e3))),
            'RequestTime' : datetime.datetime.now()}


def map_weather_data(obj):        
    """
        Function to return a dictionary mapped from obj.
        Used for the weather table.
    """
    return { 'Id' : obj['id'],
             'Description' : obj['weather'][0]['description'],
             'Temperature' : obj['main']['temp'],
             'Temp_min' : obj['main']['temp_min'],
             'Temp_max' : obj['main']['temp_max'],
             'Humidity' : obj['main']['humidity'],
             'Wind_speed' : obj['visibility'], 
             'Visibility' : obj['wind']['speed'], 
             'LastUpdate' : datetime.datetime.now()}
                                     
                                     
# connection info DB
DB_NAME = dbinfo.DB_DBIKES_USER
DB_PASS = dbinfo.DB_DBIKES_PASS
DB_HOST = dbinfo.DB_DBIKES

Base = declarative_base()

    
class DynamicStationsLive(Base):
    """
        class constructor for the dynamicstations table.
    """

    __tablename__ = "dynamic_stations_live"
    id = Column(Integer, primary_key=True)
    Number = Column(Integer)
    Status = Column(String(128))
    AvailableBikeStands = Column(Integer)
    AvailableBikes = Column(Integer)
    LastUpdate = Column(DateTime)
    RequestTime = Column(DateTime)
    
    def update_table(self, obj):
        for elem in obj:
            self.Number = elem['number']
            self.Status = elem['status']
            self.AvailableBikeStands = elem['available_bike_stands']
            self.AvailableBikes = elem['available_bikes']
            self.LastUpdate = datetime.datetime.now()
            session.add(self)

    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Number='%s', Status='%s', AvailableBikeStands='%s', BikeStands='%s', LastUpdate='%s')>" \
                % (self.Id, self.Number, self.Status, self.AvailableBikeStands, self.BikeStands, self.LastUpdate)


class DynamicStations(Base):
    """
        Class constructor for the DynamicStations table.
    """

    __tablename__ = "dynamic_stations"
    Id = Column(Integer, primary_key=True)
    Number = Column(Integer)
    Status = Column(String(128))
    AvailableBikeStands = Column(Integer)
    AvailableBikes = Column(Integer)
    LastUpdate = Column(DateTime)
    RequestTime = Column(DateTime)

    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Number='%s', Status='%s', AvailableBikeStands='%s', BikeStands='%s', LastUpdate='%s')>" \
                % (self.Id, self.Number, self.Status, self.AvailableBikeStands, self.BikeStands, self.LastUpdate)

    
class WeatherData(Base):      
    """
        Class constructor for the WeatherData table.
    """
        
    __tablename__ = "weather_data"
    Id = Column(Float)
    Description = Column(String(128))
    Temperature = Column(String(128))
    Temp_min = Column(Float)
    Temp_max = Column(Float)
    Humidity = Column(Integer)
    Wind_speed = Column(Float)
    Visibility = Column(Float)
    LastUpdate = Column(DateTime, primary_key=True) 

    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Description='%s', Temperature='%s', Temp_min='%s', Temp_max='%s', BikeSHumidity='%s', Wind_speed='%s', LastUpdate='%s')>" \
                % (self.Id, self.Description, self.Temperature, self.Temp_min, self.Temp_max, self.BikeSHumidity, self.Wind_speed, self.LastUpdate)




# create engine and base
engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)    

# create tables if they don't exist.
DynamicStationsLive.__table__.create(bind=engine, checkfirst=True)
DynamicStations.__table__.create(bind=engine, checkfirst=True)
WeatherData.__table__.create(bind=engine, checkfirst=True)

# start a session 
Session = sessionmaker(bind=engine)
session = Session()


# dynamic stations and weather update
# update live stations table
# insert into dynamic stations table (Hystory table)
# insert into weather table
retry_count = 0
while True and retry_count < 10:
    try:
        # collect data from jcdecaux api and insert it into the dynamic table.
        bikes_json = get_data(STATION_URI, APIKEY, NAME)
        weather_json = get_data(OW_URI, OW_APIKEY, OW_NAME)
        dynamic_data = list(map(map_dynamic_data, bikes_json))
        logging.info(f"Inserting {len(dynamic_data)} dynamic updates")
        if dynamic_data:
            for data in dynamic_data:
                updater = session.query(DynamicStationsLive).filter(DynamicStationsLive.Number == data['Number']).first()
                if updater:
                    updater.Number = data['Number']
                    updater.Status = data['Status']
                    updater.AvailableBikeStands = data['AvailableBikeStands']
                    updater.AvailableBikes = data['AvailableBikes']
                    updater.LastUpdate = datetime.datetime.now()
                else:
                    session.add(DynamicStationsLive(**data))

                if not session.query(DynamicStations).filter(DynamicStations.Number == data['Number'], DynamicStations.LastUpdate == data['RequestTime']).first():
                    session.add(DynamicStations(**data))
                else:
                    logging.info(f"Avoiding duplicates!")
                    
        logging.info(f"Inserted {len(dynamic_data)} dynamic updates")
        logging.info(f"Inserted {len(dynamic_data)} live dynamic updates")
        logging.info(f"Inserting {len(weather_json)} weather updates")
        if weather_json:
            session.add(WeatherData(**map_weather_data(weather_json)))
        logging.info(f"Inserted {len(weather_json)} weather updates")
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

    except Exception as e:
        logging.error(f"Error while updating station data: {e}")
        retry_count += 1
        time.sleep(1*60)
        continue
