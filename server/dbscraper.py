from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from  sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import requests
import sqlalchemy
from datetime import datetime
from weathertester import WeatherTime, Valuechecker, Weatheradd, Staticadd, Dynaadd
import mysql.connector



import time

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


#Create the sql alchemy engine, bind the base metadata and initalise a Session
engine = sqlalchemy.create_engine("mysql+mysqlconnector://admin:killthebrits@dbikes.cmf8vg83zpoy.eu-west-1.rds.amazonaws.com:3306/dbikes")
Base.metadata.create_all(bind=engine)
connection = engine.connect()
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

## Define a start time (time of first run) this will be used for the timer
starttime=time.time()

elog= open("errorlog.txt","x")
## Weekcount for static table and half hour for weather table
weekcount=0
halfhour=0
while True:
    # Reintilise the dublin bikes request and json (the json file would remain the same otherwise)
    try:
        r = requests.get(stations, params={"apiKey": apikey, "contract": name})
        rjson = r.json()
    except:
        e= open("errorlog.txt","w")
        e.write("Dublin Bikes Connection Error:"+ (time.time() - starttime))
        e.close()
        time.sleep(500 - ((time.time() - starttime) % 500))
    for i in rjson:
        # Update the rows with the new data
        updater = session.query(Update).get(i["number"])
        updater.avail = i["status"]
        updater.bstands = i["bike_stands"]
        updater.abstands = i["available_bike_stands"]
        updater.abikes = i["available_bikes"]
        # this if loop prevents a crash in the event of the last_update being blank
        if i["last_update"] == None:
            updater.update= None
        else:
            updater.update = datetime.fromtimestamp(i["last_update"] / 1000)
        session.add(updater)
        session.commit()
        row_hist=Dynaadd(i,History(),1)
        session.add(row_hist)
        session.commit()
        weekcount += 5
        halfhour += 1
    if weekcount >= 10080*7:
        try:
            r = requests.get(stations, params={"apiKey": apikey, "contract": name})
            rjson = r.json()
        except:
            e = open("errorlog.txt", "w")
            e.write("Dublin Bikes Connection Error: " + (time.time() - starttime))
            e.close()
            time.sleep(500 - ((time.time() - starttime) % 500))
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
    if halfhour >= 6:
        try:
            w = requests.get(weatherfile)
            wjson = w.json()
        except:
            e = open("errorlog.txt", "w")
            e.write("Dublin Bikes Connection Error:" + (time.time() - starttime))
            e.close()
            time.sleep(500 - ((time.time() - starttime) % 500))
        w = requests.get(weatherfile)
        wjson = w.json()
        for i in wjson:
            if (session.query(Weather).filter_by(id=WeatherTime(i["date"],i["reportTime"])).first()) == None:
                weatherup = Weatheradd(i,Weather())
                session.add(weatherup)
                session.commit()
        halfhour =0

    time.sleep(500 - ((time.time() - starttime) % 500))


