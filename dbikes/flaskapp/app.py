from flask import Flask, render_template, request,session,redirect,url_for
from sqlalchemy import create_engine
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
import json,requests
import pickle

import json,requests
pickle_in = open("dict.pickle","rb")
regression_models = pickle.load(pickle_in)
import dbinfo
import pandas as pd
import datetime
from datetime import timedelta,datetime


app = Flask(__name__)

# cant pass a variable in flask without a super secret key because lord fobid flask makes it easy, anyway this is just a placeholder, though true
app.secret_key = "Kilkenny is the best county, come at me bro"

DB_NAME = dbinfo.DB_DBIKES_USER
DB_PASS = dbinfo.DB_DBIKES_PASS
DB_HOST = dbinfo.DB_DBIKES
GM_KEY = dbinfo.GMAPS_KEY

Base = declarative_base()

def map_customer_query_data(obj):        
    """
        Function to return a dictionary mapped from obj.
        Used for the weather table.
    """
    return {
             'FirstName' : obj['firstname'],
             'LastName' : obj['lastname'],
             'EmailAddress' : obj['emailAddress'],
             'Country' : obj['country'],
             'Subject' : obj['subject'],
             'RecievedAt' : datetime.datetime.now()}

class CustomerQueries(Base):
    """
        class constructor for the customer_query table.
    """

    __tablename__ = "customer_query"
    id = Column(Integer, primary_key=True)
    FirstName = Column(String(128))
    LastName = Column(String(128))
    EmailAddress = Column(String(128))
    Country = Column(String(128))
    Subject = Column(String(128))
    RecievedAt = Column(DateTime)

    def __repr__(self):
        """
            Prints the values instead of the memory pointer.
        """
        
        return "<Node(Id='%s', Number='%s', Status='%s', AvailableBikeStands='%s', BikeStands='%s', LastUpdate='%s')>" \
                % (self.Id, self.Number, self.Status, self.AvailableBikeStands, self.BikeStands, self.LastUpdate)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/plan")
def plan():
    return render_template("prediction.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/map")
def mapbikes():
    return render_template("map.html", apiKey = GM_KEY)

@app.route("/contacts",methods=["GET","POST"])
def contacts():
    if request.method == "POST":
        engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
        CustomerQueries.__table__.create(bind=engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        session = Session()

        req = request.form
        session.add(CustomerQueries(**map_customer_query_data(request.form)))
        session.commit()
        print(f"mail: {req['emailAddress']}\nsubject: {req['subject']}")

        return redirect(request.url)

    return render_template("contacts.html")


@app.route("/stations")
def stations():
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    df_static = pd.read_sql_table("static_stations", engine)
    df_live = pd.read_sql_table("dynamic_stations_live", engine)
    return df_static.merge(df_live, on=["Number"]).to_json(orient='records')

@app.route("/prediction")
def prediction():
    return render_template("prediction.html")

#function that gets the station number from the html webpage and saves it to the session
@app.route("/varSender",methods=["GET","POST"])
def varGet():
    if request.method == "POST":
        data=request.get_json()
        session["station_number"] = str(data["number"])
        return redirect(url_for("buttonFunction"))


# Return JSON data with stand information from the past week
@app.route("/btnFunc")
def buttonFunction():
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE dynamic_stations.LastUpdate > DATE(NOW()) - INTERVAL 6 DAY AND Number = {number} GROUP BY DAY (dynamic_stations.LastUpdate) ORDER BY DAY(dynamic_stations.LastUpdate)", engine)
    return df.to_json(orient='records')


# Return JSON data with stand information from the past Day
@app.route("/btnFuncDay")
def buttonFunctionDay():
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    dateDiff = (datetime.now() - timedelta(1)).timestamp()
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE LastUpdate > {dateDiff} AND Number = {number} GROUP BY HOUR (dynamic_stations.LastUpdate) ORDER BY HOUR(dynamic_stations.LastUpdate)", engine)
    return df.to_json(orient='records')


@app.route("/predGetter",methods=["GET","POST"])
def predGet():
    if request.method == "POST":
        print("AAAAAAAAAAAAAAAAAAAAAAAh")
        data = request.get_json()
        print(data)
        session["station_number"] = str(data["number"])
        session["date"]=str(data["date"])
        return redirect(url_for("predSend"))


@app.route("/predSender",methods=["GET","POST"])
def predSend():
    number= session.get("station_number",None)
    date=session.get("date",None)
    p = '%Y-%m-%dT%H:%M'
    weekday = True
    date =datetime.strptime(date,p)
    date=date.replace(minute=0)
    hour=date.hour
    if date.day > 5:
        weekday=False

    date=date.timestamp()
    temp=0
    humid=0
    rain=False
    print("DOWN TO URL")
    BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?id=2964574&appid=8ae40bdb25ab978b8f3e77a14b91b68d"

    response = requests.get(BASE_URL)

    data = response.json()

    for i in data["list"]:
        if i["dt"] == date:
            temp= (i["main"])["temp"]
            humid =(i["main"])["humidity"]
            for j in i["weather"]:
                if "rain" in j["main"]:
                    rain=True

    print("DID JSON")
    if temp >100:
        temp-=273.15
    d={"Hour":hour,"Temperature":temp,"Rain":rain,"isWeekDay":weekday}
    data=pd.DataFrame(d,index=[0])
    print("DATAFRAME MADE")
    print(data)
    print(data.shape)
    print(data.dtypes)
    prediction=regression_models[int(number)]

    return str(prediction.predict(data)[0])





if __name__ == "__main__":
    app.run(debug=True) 
