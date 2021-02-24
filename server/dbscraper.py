from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from  sqlalchemy.ext.declarative import declarative_base
import sqlalchemy
from sqlalchemy.orm import relationship, sessionmaker
import requests
import mysql.connector
import sqlalchemy
import json
from IPython.display import JSON
from datetime import datetime
from weathertester import WeatherTime, Valuechecker, Weatheradd, Staticadd, Dynaadd

import time

Base= declarative_base()

class Station(Base):
    __tablename__="stations"

    child = relationship("Update",uselist=False,back_populates="parent")
    id=Column("number", Integer, primary_key=True)
    name=Column("name", String(128))
    address=Column("address", String(128))
    bstands=Column("bike_stands", Integer)
    plat=Column("pos_lat", Float)
    plong=Column("pos_long", Float)
    bank=Column("banking",String(120))
    bonus=Column("bonus",String(120))

class Update(Base):
    __tablename__="availability"

    parent = relationship("Station",back_populates="child")
    id=Column("number", Integer,ForeignKey("stations.number"), primary_key=True,)
    avail=Column("available", String(128))
    bstands=Column("bstands", Integer)
    abstands=Column("available_bstands", Integer)
    abikes=Column("available_bikes", Integer)
    update=Column("last_update", DateTime)

class History(Base):
    __tablename__="history"

    id = Column("id",Integer,primary_key=True)
    statnum = Column("number", Integer,)
    avail = Column("available", String(128))
    bstands = Column("bstands", Integer)
    abstands = Column("available_bstands", Integer)
    abikes = Column("available_bikes", Integer)
    update = Column("last_update", DateTime)

class Weather(Base):
    __tablename__="weather"

    id= Column("datetime",DateTime,primary_key=True)
    name=Column("name",String(120))
    temp=Column("temperature",Integer)
    desc=Column("description",String(120))
    wspeed=Column("windspeed",Integer)
    wGust=Column("windgust",Integer)
    cwind=Column("cardwindir",String(120))
    windir=Column("winddirect",Integer)
    humid=Column("humidity",Integer)
    rain=Column("rainfall",Float)
    pressure=Column("pressure",Integer)



engine = sqlalchemy.create_engine("mysql+mysqlconnector://admin:killthebrits@dbikes.cmf8vg83zpoy.eu-west-1.rds.amazonaws.com:3306/dbikes")
Base.metadata.create_all(bind=engine)
connection = engine.connect()
Session = sessionmaker(bind=engine)
session= Session()

name = "Dublin"
stations = "https://api.jcdecaux.com/vls/v1/stations/"
apikey= "e204a771852e7663127033b432b18dd9e0203d75"

r= requests.get(stations, params = {"apiKey":apikey, "contract":name})
rjson = r.json()

weatherfile= "https://prodapi.metweb.ie/observations/dublin/today"
w= requests.get(weatherfile)
wjson=w.json()

for i in wjson:
    row_w = Weatheradd(i, Weather())
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

starttime=time.time()
weekcount=0
while True:
    for i in wjson:
        #if session.query(Weather).get(WeatherTime(i["date"],i["reportTime"])) != True:
        if (session.query(Weather).filter_by(id=WeatherTime(i["date"],i["reportTime"])).first()) == None:
            print("its fucking working")
            weatherup = Weatheradd(i,Weather())
            session.add(weatherup)
            session.commit()
    for i in rjson:
        updater = session.query(Update).get(i["number"])
        updater.avail = i["status"]
        updater.bstands = i["bike_stands"]
        updater.abstands = i["available_bike_stands"]
        updater.abikes = i["available_bikes"]
        updater.update = datetime.fromtimestamp(i["last_update"] / 1000)
        session.add(updater)
        session.commit()
        row_hist=Dynaadd(i,History(),1)
        session.add(row_hist)
        session.commit()
        weekcount += 1
        if weekcount == 10080*7:
            if (session.query(Station).filter_by(id=i["number"]).first()) == None:
                newstat=Staticadd(i,Station())
                session.add(newstat)
                session.commit()
            stationup = session.query(Station).get(i["number"])
            stationup.name = i["name"]
            stationup.address = i["address"]
            stationup.bstands = i["bike_stands"]
            stationup.plat = i["position"]["lat"]
            stationup.plong = i["position"]["lng"]
            session.add(stationup)
            session.commit()
            weekcount=0

    time.sleep(300 - ((time.time() - starttime) % 300))


