# Import all dependencies
#################################################
import numpy as np

import sqlalchemy
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify, request


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
# Create Database connection
Base.metadata.create_all(engine)
# Reflect the database tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement = Base.classes.measurement 
station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"<h1>Welcome to my Climate App API!</h1>"
        f"<h3> This is a Flask API for Climate Analysis. </h3><br/>"
        f"<strong>The following are available routes:</strong><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/><br/><br/>"
        f"Be advsed that dates can only be chosen between 2010-01-01 and 2017-08-23.<br/>"
        f"For &lt;start&gt;: Please enter a start date in the format YYYY-MM-DD where &lt;start&gt; is. For example: /api/v1.0/2015-01-01. <br/>"
        f"For &lt;start&gt;/&lt;end&gt;: Please enter a start date in the format YYYY-MM-DD followed by an end date in the format YYYY-MM-DD\
            where &lt;start&gt;/&lt;end&gt; is. For example: /api/v1.0/2015-01-01/2017-01-01.<br/><br/><br/>"
        
        f"<h3>Below are hyperlinked routes. Please click the link below to see corresponding page:</h2>"
        f"<ol><li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"JSON representation of the dictionary of the yearly precipitation analysis from the most recent date</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"JSON list of all the weather stations and their characteristics from the dataset</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"JSON list of temperature observations for the previous year</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2015-01-01>"
        f"JSON list of minimum, average & maximum temperatures for the range beginning with the provided start date through to 2017-08-23</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2015-01-01/2017-01-01>"
        f"JSON list of minimum, average & maximum temperatures for the range beginning with the provided start and end date range</a></li></ol><br/>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """JSON representation of the dictionary of the yearly precipitation analysis from the most recent date"""
    
    # Find the latest date in the dataset (Order by descending date)
    latest_date_str = session.query(measurement.date).\
        order_by(measurement.date.desc()).\
            first()[0]

    latest_date = dt.date.fromisoformat(latest_date_str)

    # Calculate one year prior to the above date of 2017-08-23:
    prior_year_date = latest_date - dt.timedelta(days=365)


    # Create query of 'Measurement' table for prcp and date columns 
    yearly_precipitation_query = session.query(measurement.date, 
                                               measurement.prcp).\
                                                filter(measurement.date.between(prior_year_date, latest_date)).\
                                                    all()


    session.close()


    # Create a dictionary and append to a list for yearly precipitation data
    yearly_precipitation_data = []
    for date, prcp in yearly_precipitation_query:
        precipitation_dict = {}
        precipitation_dict["Precipitation"] = prcp
        precipitation_dict["Date"] = date
        yearly_precipitation_data.append(precipitation_dict)

    return jsonify(yearly_precipitation_data)
    


@app.route("/api/v1.0/stations")
def stations():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """JSON list of all the weather stations and their characteristics from the dataset"""
    # Query all stations
    stations_query = session.query(station.station, 
                                  station.name,
                                  station.latitude,
                                  station.longitude,
                                  station.elevation).\
                                    all()

    session.close()

    # Convert list into normal list
    all_stations = list(np.ravel(stations_query))
    
    # Create a dictionary from the station variable and append to a list for all stations
    # all_stations = []
    # for station, name, latitude, longitude, elevation in stations_query:
    #     station_dict = {}
    #     station_dict["station"] = station
    #     station_dict["name"] = name
    #     station_dict["latitude"] = latitude
    #     station_dict["longitude"] = longitude
    #     station_dict["elevation"] = elevation
    #     all_stations.append(station_dict)

    return jsonify(all_stations)



@app.route("/api/v1.0/tobs")
def tobs():
    # Create session (link) from Python to the DB
    session = Session(engine)

    """JSON list of temperature observations for the previous year"""
    
    # Find latest date for most active station = Station "USC00519281".
    top_active_station = session.query(measurement.station).\
        group_by(measurement.station).\
            order_by(func.count(measurement.station).desc()).\
                first()
    t_station = top_active_station.station
    
    latest_date_str = session.query(measurement.date).\
        filter(measurement.station==t_station).\
            order_by(measurement.date.desc()).\
                first()[0]

    latest_date = dt.date.fromisoformat(latest_date_str)    
    
    # Calculate one year prior to the above date of 2017-08-18 for Station "USC00519281".
    one_year_prior = latest_date - dt.timedelta(days=365)

    # Design a query to retrieve the last 12 months of temperature data
    yearly_temperature_data = session.query(measurement.date, 
                                            measurement.tobs).\
                                                filter(measurement.date.between(one_year_prior, latest_date)).\
                                                    all()


    session.close()


    # Create a dictionary from the row data and append to a list of all_passengers
    temperature = []
    for date, tobs in yearly_temperature_data:
        temperature_dict = {}
        temperature_dict["Temperature Observations"] = tobs
        temperature_dict["Date"] = date
        temperature.append(temperature_dict)

    return jsonify(temperature)



@app.route("/api/v1.0/<start>", defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def temps_for_date_range(start, end):
    """JSON list of the minimum, average and maximum temperatures for a given start or start-end date range."""
    """When only the start date is provided, calculate TMIN, TAVG, and TMAX for all dates equal to or greater than the provided start date."""
    """When the start and end date is provided, calculate the TMIN, TAVG, and TMAX for dates between the provided start and end date inclusive."""
    
    # Create our session (link) from Python to the DB.
    session = Session(engine)

    # If both a start date and an end date is provided
    if end != None:
        temperature_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).filter(
            measurement.date <= end).all()
    
    # If only a start date is provided
    else:
        temperature_data = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).all()

    session.close()

    # Convert the query results to a list.
    temperature_list = []
    no_temperature_data = False
    for min_temp, avg_temp, max_temp in temperature_data:
        if min_temp == None or avg_temp == None or max_temp == None:
            no_temperature_data = True
        temperature_list.append(min_temp)
        temperature_list.append(avg_temp)
        temperature_list.append(max_temp)
    # Return the JSON representation of dictionary.
    if no_temperature_data == True:
        return f"No temperature data found for the given date or date range between 2010-01-01 and 2017-08-23. Please provide another date range with the correct format (YYYY-MM-DD) if only providing\
            start date and (YYYY-MM-DD/YYYY-MM-DD) if providing start and end date."
    else:
        return jsonify(temperature_list)




# def stats(start=None, end=None):
#     """Return TMIN, TAVG, TMAX."""
#     session = Session(engine)

#     # Select statement
#     sel = [func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)]

#     if not end:
#         start = dt.datetime.strptime(start, "%Y%m%d")
#         results = session.query(*sel).\
#             filter(measurement.date >= start).all()

#         session.close()

#         temps = list(np.ravel(results))
#         return jsonify(temps)

#     # calculate TMIN, TAVG, TMAX with start and stop
#     start = dt.datetime.strptime(start, "%Y%m%d")
#     end = dt.datetime.strptime(end, "%Y%m%d")

#     results = session.query(*sel).\
#         filter(measurement.date >= start).\
#         filter(measurement.date <= end).all()

#     session.close()

#     # Unravel results into a 1D array and convert to a list
#     temps = list(np.ravel(results))
#     return jsonify(temps=temps)


if __name__ == '__main__':
    app.run(debug=True)
