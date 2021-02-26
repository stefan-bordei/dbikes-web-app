import requests
from datetime import datetime
from  sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from  sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import sqlalchemy

weather= "https://prodapi.metweb.ie/observations/phoenix-park/today"

w= requests.get(weather)

wjson=w.json()

Base= declarative_base()


class Station(Base):
    # This defines the table stations which will be used for the static data
    __tablename__="stations"

    child = relationship("Update",uselist=False,back_populates="parent")
    child2= relationship("History",uselist=False,back_populates="parent")
    id=Column("number", Integer, primary_key=True)
    name=Column("name", String(128))
    address=Column("address", String(128))
    bikeStands=Column("bike_stands", Integer)
    posLat=Column("pos_lat", Float)
    posLong=Column("pos_long", Float)
    bank=Column("banking",String(120))
    bonus=Column("bonus",String(120))

class Update(Base):
    #This defines the table availability which will be used for the dynamic data
    __tablename__="availability"

    parent = relationship("Station",back_populates="child")
    id=Column("number", Integer,ForeignKey("stations.number"), primary_key=True,)
    avail=Column("available", String(128))
    bikeStands=Column("bstands", Integer)
    availBikeStands=Column("available_bstands", Integer)
    availBikes=Column("available_bikes", Integer)
    update=Column("last_update", DateTime)

class History(Base):
    # This defines the history table, which will archive the availability data for future analysis
    __tablename__="history"
    parent = relationship("Station", back_populates="child2")
    id = Column("id",Integer,primary_key=True)
    statnum = Column("number", Integer,ForeignKey("stations.number"))
    avail = Column("available", String(128))
    bikeStands = Column("bstands", Integer)
    availBikeStands = Column("available_bstands", Integer)
    availBikes = Column("available_bikes", Integer)
    update = Column("last_update", DateTime)

class Weather(Base):
    # This defines the Weather table which is used for the weather
    __tablename__="weather"

    id= Column("datetime",DateTime,primary_key=True)
    name=Column("name",String(120))
    temp=Column("temperature",Integer)
    desc=Column("description",String(120))
    winSpeed=Column("windspeed",Integer)
    winGust=Column("windgust",Integer)
    cardWind=Column("cardwindir",String(120))
    winDir=Column("winddirect",Integer)
    humid=Column("humidity",Integer)
    rain=Column("rainfall",Float)
    pressure=Column("pressure",Integer)


engine = sqlalchemy.create_engine("mysql+mysqlconnector://admin:killthebrits@dbikes.cmf8vg83zpoy.eu-west-1.rds.amazonaws.com:3306/dbikes")
Base.metadata.create_all(bind=engine)


def WeatherTime(date,time):
    """ Takes the date and reportTime from a json object and returns a datetime object"""
    timeNew = time + ":00"
    correctDate = date +" "+ timeNew
    return datetime.strptime(correctDate, "%d-%m-%Y %H:%M:%S")


def Valuechecker(value):
    """Checks if the value is NA or a varient, used to avoid crashes"""
    badValues = ["NA","N/A","-"]
    if value in badValues:
        return None
    else:
        return value



def Weatheradd(dict,table):
    """Creates a Weather object from a dictionary"""
    orm= table
    orm.id = WeatherTime(dict["date"], dict["reportTime"])
    orm.name = dict["name"]
    orm.temp = Valuechecker(dict["temperature"])
    orm.desc = dict["weatherDescription"]
    orm.winSpeed = Valuechecker(dict["windSpeed"])
    orm.winGust = Valuechecker(dict["windGust"])
    orm.cardWind = Valuechecker(dict["cardinalWindDirection"])
    orm.winDir = Valuechecker(dict["windDirection"])
    orm.humid = Valuechecker(dict["humidity"])
    orm.rain = Valuechecker(dict["rainfall"])
    orm.pressure = Valuechecker(dict["pressure"])
    return orm

def Staticadd(dict,table):
    """Creates a staticadd object (row for static table) from a dictionary"""
    station=table
    station.id = dict["number"]
    station.name = dict["name"]
    station.address = dict["address"]
    station.bikeStands = dict["bike_stands"]
    station.posLat=dict["position"]["lat"]
    station.posLong=dict["position"]["lng"]
    station.bank=dict["banking"]
    station.bonus=dict["bonus"]
    return station

def Dynaadd(dict,table,hist=0):
    """Creates a Dynaad object (row for dynamic/update table) the hist variable idicates if this is for main or historical table"""
    if hist==0:
        update= table
        update.id = dict["number"]
        update.avail = dict["status"]
        update.bikeStands = dict["bike_stands"]
        update.availBikeStands = dict["available_bike_stands"]
        update.availBikes = dict["available_bikes"]
        if dict["last_update"] == None:
            update.update= None
        else:
            update.update = datetime.fromtimestamp(dict["last_update"] / 1000)
        return update
    else:
        history=table
        history.statnum = dict["number"]
        history.avail = dict["status"]
        history.bikeStands = dict["bike_stands"]
        history.availBikeStands = dict["available_bike_stands"]
        history.availBikes = dict["available_bikes"]
        if dict["last_update"] == None:
            history.update=None
        else:
            history.update = datetime.fromtimestamp(dict["last_update"] / 1000)
        return history



