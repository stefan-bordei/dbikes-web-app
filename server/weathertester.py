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
    id=Column("number", Integer, primary_key=True)
    name=Column("name", String(128))
    address=Column("address", String(128))
    bstands=Column("bike_stands", Integer)
    plat=Column("pos_lat", Float)
    plong=Column("pos_long", Float)
    bank=Column("banking",String(120))
    bonus=Column("bonus",String(120))

class Update(Base):
    #This defines the table availability which will be used for the dynamic data
    __tablename__="availability"

    parent = relationship("Station",back_populates="child")
    id=Column("number", Integer,ForeignKey("stations.number"), primary_key=True,)
    avail=Column("available", String(128))
    bstands=Column("bstands", Integer)
    abstands=Column("available_bstands", Integer)
    abikes=Column("available_bikes", Integer)
    update=Column("last_update", DateTime)

class History(Base):
    # This defines the history table, which will archive the availability data for future analysis
    __tablename__="history"

    id = Column("id",Integer,primary_key=True)
    statnum = Column("number", Integer,)
    avail = Column("available", String(128))
    bstands = Column("bstands", Integer)
    abstands = Column("available_bstands", Integer)
    abikes = Column("available_bikes", Integer)
    update = Column("last_update", DateTime)

class Weather(Base):
    # This defines the Weather table which is used for the weather
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


def WeatherTime(date,time):
    """ Takes the date and reportTime from a json object and returns a datetime object"""
    timenew = time + ":00"
    correctdate = date +" "+ timenew
    return datetime.strptime(correctdate, "%d-%m-%Y %H:%M:%S")


def Valuechecker(value):
    """Checks if the value is NA or a varient, used to avoid crashes"""
    badvalues = ["NA","N/A","-"]
    if value in badvalues:
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
    orm.wspeed = Valuechecker(dict["windSpeed"])
    orm.wGust = Valuechecker(dict["windGust"])
    orm.cwind = Valuechecker(dict["cardinalWindDirection"])
    orm.windir = Valuechecker(dict["windDirection"])
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
    station.bstands = dict["bike_stands"]
    station.plat=dict["position"]["lat"]
    station.plong=dict["position"]["lng"]
    station.bank=dict["banking"]
    station.bonus=dict["bonus"]
    return station

def Dynaadd(dict,table,hist=0):
    """Creates a Dynaad object (row for dynamic/update table) the hist variable idicates if this is for main or historical table"""
    if hist==0:
        update= table
        update.id = dict["number"]
        update.avail = dict["status"]
        update.bstands = dict["bike_stands"]
        update.abstands = dict["available_bike_stands"]
        update.abikes = dict["available_bikes"]
        if dict["last_update"] == None:
            update.update= None
        else:
            update.update = datetime.fromtimestamp(dict["last_update"] / 1000)
        return update
    else:
        history=table
        history.statnum = dict["number"]
        history.avail = dict["status"]
        history.bstands = dict["bike_stands"]
        history.abstands = dict["available_bike_stands"]
        history.abikes = dict["available_bikes"]
        if dict["last_update"] == None:
            history.update= None
        else:
            history.update = datetime.fromtimestamp(dict["last_update"] / 1000)
        return history



