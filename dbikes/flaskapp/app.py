from flask import Flask, render_template, request,session,redirect,url_for
from sqlalchemy import create_engine
import json
import dbinfo
import pandas as pd
import datetime
from datetime import timedelta


app = Flask(__name__)

# cant pass a variable in flask without a super secret key because lord fobid flask makes it easy, anyway this is just a placeholder, though true
app.secret_key = "Kilkenny is the best county, come at me bro"

DB_NAME = dbinfo.DB_DBIKES_USER
DB_PASS = dbinfo.DB_DBIKES_PASS
DB_HOST = dbinfo.DB_DBIKES
GM_KEY = dbinfo.GMAPS_KEY

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

@app.route("/contacts")
def contacts():
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
    #dateDiff = (datetime.datetime.now() - datetime.timedelta(7)).timestamp()
    #dateDiff = datetime.timedelta(7).timestamp()
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE dynamic_stations.LastUpdate > DATE(NOW()) - INTERVAL 6 DAY AND Number = {number} GROUP BY DAY (dynamic_stations.LastUpdate) ORDER BY DAY(dynamic_stations.LastUpdate)", engine)
    return df.to_json(orient='records')


# Return JSON data with stand information from the past Day
@app.route("/btnFuncDay")
def buttonFunctionDay():
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    dateDiff = (datetime.datetime.now() - datetime.timedelta(1)).timestamp()
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE LastUpdate > {dateDiff} AND Number = {number} GROUP BY HOUR (dynamic_stations.LastUpdate) ORDER BY HOUR(dynamic_stations.LastUpdate)", engine)
    return df.to_json(orient='records')


if __name__ == "__main__":
    app.run(debug=True) 
