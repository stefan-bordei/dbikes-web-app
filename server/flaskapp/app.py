from flask import Flask, render_template, request,session,redirect,url_for
from sqlalchemy import create_engine
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base, ConcreteBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import *
from sqlalchemy import exc
from random import randint
import logging
import requests
import time
import os
import json,requests
import pickle
import json,requests
#imports the pickle file used for the predictions
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
             'RecievedAt' : datetime.now()}

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
        engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)
        CustomerQueries.__table__.create(bind=engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        session = Session()

        req = request.form
        session.add(CustomerQueries(**map_customer_query_data(request.form)))
        session.commit()

        return redirect(request.url)

    return render_template("contacts.html")


@app.route("/stations")
def stations():
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)
    df_static = pd.read_sql_table("static_stations", engine)
    df_live = pd.read_sql_table("dynamic_stations_live", engine)
    return df_static.merge(df_live, on=["Number"]).to_json(orient='records')

@app.route("/prediction")
def prediction():
    return render_template("prediction.html")

#function that gets the station number from the html webpage and saves it to the session
@app.route("/varSender",methods=["GET","POST"])
def varGet():
    """
    Function which retrieves a variable from the JS ajax and saves it to a flask variable for later use
    """
    if request.method == "POST":
        data=request.get_json()
        session["station_number"] = str(data["number"])
        # redirects to the buttonFunction app route
        return redirect(url_for("buttonFunction"))


# Return JSON data with stand information from the past week
@app.route("/btnFunc")
def buttonFunction():
    """
    function which performs an SQL query to return the weekly historical data for a station where a station number matches the provided number
    """
    # sets the number variable to the session variable station_number (which is set from the JS)
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE dynamic_stations.LastUpdate > DATE(NOW()) - INTERVAL 6 DAY AND Number = {number} GROUP BY DAY (dynamic_stations.LastUpdate) ORDER BY DAY(dynamic_stations.LastUpdate)", engine)
    return df.to_json(orient='records')


# Return JSON data with stand information from the past Day
@app.route("/btnFuncDay")
def buttonFunctionDay():
    """
        function which performs an SQL query to return the  historical data (past 24 hours) for a station where a station number matches the provided number
        """
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)
    dateDiff = (datetime.now() - timedelta(1)).timestamp() # gets the epoch time this time 24 hours ago
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE LastUpdate > {dateDiff} AND Number = {number} GROUP BY HOUR (dynamic_stations.LastUpdate) ORDER BY HOUR(dynamic_stations.LastUpdate)", engine)
    return df.to_json(orient='records')


@app.route("/predGetter",methods=["GET","POST"])
def predGet():
    """
    Retrieves the variables from ajax within the javascript and sets them to the Flask variables (to be used in a seperate function)
    """
    if request.method == "POST":
        data = request.get_json()
        session["station_number"] = str(data["number"])
        session["date"]=str(data["date"])
        session["time"]=str(data["time"])
        # after setting the variables thi is then routed to the predSend function
        return redirect(url_for("predSend"))


@app.route("/predSender",methods=["GET","POST"])
def predSend():
    """
    Function which retrieves the date and number for a prediction, uses the appropriate model and then sends the result back to the webpage
    """

    # retrieves the session variables (station number and the date for the prediction
    number= session.get("station_number",None)
    date=session.get("date",None)
    time=session.get("time",None)

    date=datetime.strptime(date,'%Y-%m-%d')

    # set weekday to True
    weekday = True

    # retrieve the hour (hour is one of the variables used in the prediction
    hour=int(time.split(":")[0])
    # set the weeday to false if the prediction date day is saturday or sunday
    if date.day > 5:
        weekday=False

    date=date.timestamp()
    # create temp, humidity and rain to 0 0 and False (these are used in the prediction and will be updated)
    temp=0
    humid=0
    rain=False

    # URl for the weather forecast data
    BASE_URL = "http://api.openweathermap.org/data/2.5/forecast?id=2964574&appid=8ae40bdb25ab978b8f3e77a14b91b68d"

    response = requests.get(BASE_URL)

    data = response.json()

    # iterate through the JSON file (the forecast weather data)
    for i in data["list"]:
        # if it is the correct date and time
        if i["dt"] == date:
            # set the temp and the humidity to the temp and humidity at that time
            temp= (i["main"])["temp"]
            humid =(i["main"])["humidity"]
            # iterate through the nested weather list
            for j in i["weather"]:
                # if the weather is rainy (e.g light rain, heavy rain)
                if "rain" in j["main"]:
                    # set rain to true
                    rain=True

    # if the temperature is given in Kelvin convert to celcius (most of the time it is in kelvin but just incase)
    if temp >100:
        # technically could mess up the temperature if it was over 100 and in celcius but if it ever gets that hot the prediction model being thrown off is the least of our worries
        temp-=273.15
    # creates a dictionary with the variables needed for the prediction
    d={"Hour":hour,"Temperature":temp,"Rain":rain,"isWeekDay":weekday}
    # creates a dataframe from that data (prediction model requires a dataframe)
    data=pd.DataFrame(d,index=[0])
    # Uses the prediction model for the station number with the dataframe
    prediction=regression_models[int(number)]

    # returns the predicted free Bike amount
    return str(prediction.predict(data)[0])

@app.route("/wthrGetter")
def weatherGetter():
    """
        function which performs an SQL query to return the most recent weather data
        """
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=False)
    df = pd.read_sql_query(f"SELECT * from weather_data ORDER BY id DESC LIMIT 1", engine)
    return df.to_json(orient='records')




if __name__ == "__main__":
    app.run(debug=True) 
