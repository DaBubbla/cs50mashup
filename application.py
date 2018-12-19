import os
import re
from flask import Flask, jsonify, redirect, render_template, request
from werkzeug.exceptions import default_exceptions
from tokenize import tokenize

from cs50 import SQL
from helpers import lookup

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")


@app.route("/articles")
def articles():
    """Look up articles for geo"""

    # Locate geo info and call lookup()

    geo = request.values.get("geo")
    if not geo:
        raise RuntimeError("Geo not set.")
    articles = lookup(geo)

    # Return articles as JSON object
    # TODO
    return jsonify([ articles[0], articles[1], articles[2], articles[3] ])


@app.route("/search")
def search():
    """Search for places that match query"""
     # TODO
    # Waiting for search values / args
    q = request.args.get("q") + "%"

    if not q:
        raise RuntimeError("There is no 'q'.")


    # # Verify that user's query matches place in places either by postal code, name, or state
    """Can only retreive one piece at a time ie city is ok, state is ok - city + state = no go"""
    place = db.execute("SELECT \
                        * \
                        FROM places \
                        WHERE places.place_name LIKE :q OR places.postal_code LIKE :q OR places.admin_name1 LIKE :q OR places.admin_code1 \
                        GROUP BY place_name", q=q)


    if not place:
        raise RuntimeError("Something went wrong with 'place'!")


    if len(place) > 10:
        return jsonify([ place[0], place[1], place[2], place[3], place[4], place[5], place[6], place[7], place[8], place[9] ])
    else:
        return jsonify(place)


@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Find 10 cities within view, pseudorandomly chosen if more within view
    if sw_lng <= ne_lng:

        # Doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # Crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    return jsonify(rows)
