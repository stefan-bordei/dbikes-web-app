from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from  sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import requests
import sqlalchemy
from datetime import datetime
from weathertester import WeatherTime, Valuechecker, Weatheradd, Staticadd, Dynaadd, Base, Station, Update, History, Weather
import mysql.connector
import time



#Create the sql alchemy engine, bind the base metadata and initalise a Session
engine = sqlalchemy.create_engine("mysql+mysqlconnector://admin:killthebrits@dbikes.cmf8vg83zpoy.eu-west-1.rds.amazonaws.com:3306/dbikes")
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


elog= open("errorlog.txt","w")
tlog= open("Actionlog.txt","w")
## Weekcount for static table and half hour for weather table
weekcount=0
halfhour=0

while True:
    ## Define a start time (time of first run) this will be used for the timer
    starttime = time.time()
    # Reintilise the dublin bikes request and json (the json file would remain the same otherwise)
    try:
        r = requests.get(stations, params={"apiKey": apikey, "contract": name})
        rjson = r.json()
    except:
        elog.write("Dublin Bikes Connection Error:"+ (time.time() - starttime))
        time.sleep(500 - ((time.time() - starttime) % 500))
    for i in rjson:
        histcount=0
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

        ## this gets the last 200 entries in the table , to check for duplicates
        duplicates = session.query(History).order_by(History.id.desc()).limit(200)

        #this filters for duplicates (if the stationnumber and the last update are the same the entry isnt added)
        for j in duplicates:
            if i["number"] == j.statnum:
                # if the last_update in null this or statement prevents a crash by short-circuiting the statement
                if i["last_update"] == j.update or datetime.fromtimestamp(i["last_update"] / 1000) == j.update:
                    break
                else:
                    row_hist=Dynaadd(i,History(),1)
                    session.add(row_hist)
                    session.commit()
                    histcount+=1
        weekcount += 5
        halfhour += 1
    if weekcount >= 10080*7:
        try:
            r = requests.get(stations, params={"apiKey": apikey, "contract": name})
            rjson = r.json()
        except:
            e = open("errorlog.txt", "w")
            e.write("Error in static update " + (time.time() - starttime))
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
