from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from  sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import requests
import sqlalchemy
from datetime import datetime
from weathertester import WeatherTime, Valuechecker, Weatheradd, Staticadd, Dynaadd, Base, Station, Update, History, Weather
import mysql.connector


import time

#Base= declarative_base()

#Create the sql alchemy engine, bind the base metadata and initalise a Session
engine = sqlalchemy.create_engine("mysql+mysqlconnector://admin:killthebrits@dbikes.cmf8vg83zpoy.eu-west-1.rds.amazonaws.com:3306/dbikes")
Session = sessionmaker(bind=engine)
session= Session()

#Dublin bikes API connection and transformation into Json format
name = "Dublin"
stations = "https://api.jcdecaux.com/vls/v1/stations/"
apikey= "e204a771852e7663127033b432b18dd9e0203d75"
r= requests.get(stations, params = {"apiKey":apikey, "contract":name})
rjson = r.json()

#Dublin weather API connection and transformation into Json format

weatherfile= "https://prodapi.metweb.ie/observations/dublin/today"
w= requests.get(weatherfile)
wjson=w.json()

# These use functions found in the weathertester file

for i in wjson: # for each dictionary within the json
    # Create weather object (which will fill in the row)
    row_w = Weatheradd(i, Weather())
    # add to the current session and commit
    session.add(row_w)
    session.commit()

for i in rjson:
    row_s = Staticadd(i,Station())
    session.add(row_s)
    session.commit()

    row_u = Dynaadd(i,Update())
    session.add(row_u)
    session.commit()

    row_h = Dynaadd(i,History(),1)
    session.add(row_h)
    session.commit()
session.close()
elog= open("errorlog.txt","x")
tlog= open("Actionlog.txt","x")
print("Database created")


