# Import all dependencies
#################################################
import numpy as np
import sqlalchemy
import datetime as dt

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


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
        f"<h1>Welcome to my Hawaii Climate App API!</h1>"
        f"<h3> This is a Flask API for Climate Analysis. </h3><br/>"
        f"The following are available routes:<br/>"
        f"<strong>Daily Precipitation Totals for the Last Year: </strong> api/v1.0/precipitation<br/>" 
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"Click here for direct link</a></li><br/>"
        f"<strong>All Hawaii Weather Stations:</strong> api/v1.0/stations<br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"Click here for direct link</a></li><br/>"
        f"<strong>Temperature Observations for the Last Year:</strong> api/v1.0/tobs<br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"Click here for direct link</a></li><br/>"
        f"<strong>List of minimum, average & maximum temperatures for the range beginning with the provided start date through to 08-23-2017:</strong>\
            api/v1.0/&lt;start&gt;<br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/01-01-2010>"
        f"Click here for direct link</a></li><br/>"
        f"<strong>List of minimum, average & maximum temperatures for the range beginning with the provided start and end date range:</strong>\
            api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/01-01-2010/08-23-2017>"
        f"Click here for direct link</a></li><br/><br/>"

        f"Be advsed that dates can only be provided between 01-01-2010 and 08-23-2017 inclusive.<br/>"
        f"For &lt;start&gt;: Please enter a start date in the format mm-dd-YYYY where &lt;start&gt; is. For example: /api/v1.0/01-01-2010. <br/>"
        f"For &lt;start&gt;/&lt;end&gt;: Please enter a start date in the format mm-dd-YYYY followed by an end date in the format mm-dd-YYYY\
            where &lt;start&gt;/&lt;end&gt; is. For example: /api/v1.0/01-01-2010/08-23-2017.<br/><br/><br/>"
        
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


    # Convert list into normal list
    all_stations = list(np.ravel(yearly_temperature_data))
    

    return jsonify(all_stations)



@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def date_temps(start=None, end=None):
    """JSON list of the minimum, average and maximum temperatures for a given start or start-end date range."""
    """When only the start date is provided, calculate TMIN, TAVG, and TMAX for all dates equal to or greater than the provided start date."""
    """When the start and end date is provided, calculate the TMIN, TAVG, and TMAX for dates between the provided start and end date inclusive."""
    session = Session(engine)

    # Select Statement
    sel = [func.min(measurement.tobs), 
           func.avg(measurement.tobs), 
           func.max(measurement.tobs)]

    if not end:
        start = dt.datetime.strptime(start, "%m-%d-%Y")
        results_start = session.query(*sel).\
            filter(measurement.date >= start).all()

        session.close()

        temps = list(np.ravel(results_start))
        return jsonify(temps)

    # Calculate TMIN, TAVG, TMAX with start and stop
    start = dt.datetime.strptime(start, "%m-%d-%Y")
    end = dt.datetime.strptime(end, "%m-%d-%Y")

    results_range = session.query(*sel).\
        filter(measurement.date >= start).\
            filter(measurement.date <= end).all()

    session.close()

    # Unravel results into array and convert to a list
    temps = list(np.ravel(results_range))

    return jsonify(temps=temps)


if __name__ == '__main__':
    app.run(debug=True)

