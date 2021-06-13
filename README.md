# Dublin Bikes web app
Web application that displays occupancy and weather information for Dublin Bike based on data from JCDecaux API.

## Contributors:

- Samuel Hamilton
- Edvinas Patarakas
- Stefan Bordei

### Goal

The goal of this project was to develop a web application to display occupancy and weather information for Dublin Bikes.

The project consisted of:

- Data collection through JCDecaux API and Open Weather API
- Data management and storage on AWS using RDS
- Developing a Flask web application that will be hosted on an AWS EC2 instance and serving it on a named host
- Bike stations displayed using Google Maps API
- Occupancy and weather information display for each station
- Interactivity 
- ML model for predicting occupancy based on weather patterns, trained on collected data

## How to use it:

If you want to run this website locally you can use the following steps. Before running the app you will need a few things:

	- JCDecauz API key
	- Google Maps API Key
	- Database (you can use a local data base or an RDS instance on AWS)
	- Open Weather API Key 

1. Clone the repository using:
`git clone https://github.com/stefan-bordei/dbikes-web-app.git`

2. Create a python file called `dbinfo.py` containing:
- `JCD_API_KEY='Your_JCD_API_Key'` 
- `DB_DBIKES='Your_Database_Link'`
- `DB_DBIKES_USER='DB_User_Name'`
- `DB_DBIKES_PASS='DB_Password'`
- `OW_API_KEY='Your_OpenWeather_API_Key'`

3. Run `python /server/flaskapp/app.py`
4. Open a web browser and go to `http://localhost:5000`


## Functionality:

  

On the EC2 instance 2 separate python scripts are collecting data from the JCDecaux API and Open Weather API and retrieving it as a JSON file. The APIs are queried every 5 minutes. The JSON data is then mapped and pushed to tables in a database running on Amazon RDS.

The database contains 3 tables, One table for static data that gets updated every 7 days using a cron job.This table contains information that is not likely to change often like the Station Name, Address and the location. All the data that is changing constantly is stored in 2 other tables. One table that constantly updates it’s fields and another that keeps adding to the entries in order for us to be able to access “historical” data for predictions.

  

The Flask application sends requests to the RDS instance and retrieves data that it uses to populate the web pages.

  

Every time the Map page is loaded the Flask app queries the table containing dynamic data and uses that to generate the markers on the map. If the user selects a specific marker on the map the Flask app queries the database again for historical data regarding that station in order to generate 2 graphs representing the bikes availability for 24h and for the previous 7 days.

The user also has the ability to choose a date and time (7 days in advance) in order to get a prediction for the bike availability for a specific station.

  

After deploying the web app to EC2 we discovered that when more than one person was on the Map page sometimes it would be slow loading the data so we decided to use gunicorn with the default 3 workers for load balancing. We also used nginx and certbot in order to run The web app on port 443 and forward all http requests to https.
