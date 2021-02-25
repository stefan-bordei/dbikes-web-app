import requests
from datetime import datetime


weather= "https://prodapi.metweb.ie/observations/phoenix-park/today"

w= requests.get(weather)

wjson=w.json()




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



