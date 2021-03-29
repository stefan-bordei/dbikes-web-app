from flask import Flask, render_template, request,session,redirect,url_for
from sqlalchemy import create_engine
import json
import dbinfo
import pandas as pd
import datetime


app = Flask(__name__)

# cant pass a variable in flask without a super secret key because lord fobid flask makes it easy, anyway this is just a placeholder, though true
app.secret_key = "Kilkenny is the best county, come at me bro"

DB_NAME = dbinfo.DB_DBIKES_USER
DB_PASS = dbinfo.DB_DBIKES_PASS
DB_HOST = dbinfo.DB_DBIKES


@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/plan")
def plan():
    return render_template("plan.html")

@app.route("/about_us",methods=["GET","POST"])
def about_us():
    if request.method == 'POST':
        data = request.get_json()
        email = str(data["email"])
        user_password = str(data["password"])
        print(user_password, email)

    return render_template("about_us.html")

@app.route("/map")
def mapbike():
    return render_template("map.html")

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route("/stations")
def stations():
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    df = pd.read_sql_table("static_stations", engine)
    return df.to_json(orient='records')

@app.route("/prediction")
def prediction():
    return render_template("prediction.html")



#function that gets the station number from the html webpage and saves it to the session
@app.route("/varSender",methods=["GET","POST"])
def varGet():
    print("IT FUCKIN GOT THIS FAR")
    if request.method == "POST":
        data=request.get_json()
        session["station_number"] = str(data["number"])
        return redirect(url_for("buttonFunction"))


# Return JSON data with stand information from the past week
@app.route("/btnFunc")
def buttonFunction():
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    dateDiff = (datetime.datetime.now() - datetime.timedelta(7)).timestamp()
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE LastUpdate > {dateDiff} AND Number = {number}", engine)
    return df.to_json(orient='records')


# Return JSON data with stand information from the past Day
@app.route("/btnFuncDay")
def buttonFunctionDay():
    number = session.get("station_number",None)
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    dateDiff = (datetime.datetime.now() - datetime.timedelta(1)).timestamp()
    df = pd.read_sql_query(f"SELECT DISTINCT Number, AvailableBikeStands, AvailableBikes, LastUpdate from dynamic_stations WHERE LastUpdate > {dateDiff} AND Number = {number}", engine)
    return df.to_json(orient='records')


if __name__ == "__main__":
    app.run(debug=True)
