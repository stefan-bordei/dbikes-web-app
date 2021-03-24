from flask import Flask, render_template
from sqlalchemy import create_engine
import json
import dbinfo
import pandas as pd


app = Flask(__name__)

DB_NAME = dbinfo.DB_DBIKES_USER
DB_PASS = dbinfo.DB_DBIKES_PASS
DB_HOST = dbinfo.DB_DBIKES

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/plan")
def plan():
    return render_template("plan.html")

@app.route("/about_us")
def about_us():
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

@app.route("/btnFunc")
def buttonPrediction():
    engine = create_engine(f"mysql+mysqlconnector://{DB_NAME}:{DB_PASS}@{DB_HOST}/dbikes_main", echo=True)
    df = pd.read_sql_table("dynamic_stations", engine)
    return df.to_json(orient='records')

if __name__ == "__main__":
    app.run(debug=True)
