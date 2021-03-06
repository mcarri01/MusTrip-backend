""" mustrip.py """
import os
import json
from bson.json_util import dumps
from flask import Flask
from flask import request
from geopy.geocoders import Nominatim
from haversine import haversine
from pymongo import MongoClient




APP = Flask(__name__)
@APP.route('/')
def index():
    """ Temp index """
    return "Welcome"

############################################################
# Add to database functions
############################################################
@APP.route('/addUser', methods=['POST'])
def add_user():
    """Adds a new user (if does not exist) to the database"""
    _db = db_login()
    req_user = request.form["user"]
    user_exists = _db.users.count({"username": request.form['user']})
    if user_exists == 0:
        _db.users.insert({"username" : req_user})
        return json.dumps({"status": "success"})
    else:
        return json.dumps({"status": "User already exists"})


@APP.route("/addTrip", methods=["POST"])
def add_trip():
    """Adds a new trip (if does not exist) to the database"""
    _db = db_login()
    trip_id = request.form["trip_id"]
    req_user = request.form["user"]
    trip_exists = _db.users.count({"username": req_user, "trips.name" : trip_id})

    if trip_exists == 0:
        _db.users.update_one({"username": req_user}, {"$addToSet": {"trips" : {"name" : trip_id}}})
        return json.dumps({"status": "success"})
    else:
        return json.dumps({"status": "Trip already exists"})


@APP.route('/addTrack', methods=['POST'])
def add_track():
    """Adds a new track to a particular track playlist"""
    _db = db_login()
    trip_id = request.form["trip_id"]
    track_id = request.form["track"]
    req_user = request.form["user"]
    query = {"$addToSet": {"trips.$.tracks": track_id}}
    _db.users.update_one({"username" : req_user, "trips.name" : trip_id}, query)

    return json.dumps({"status": "success"})

############################################################
# Retrieve from database functions
############################################################
@APP.route("/getUser", methods=["POST"])
def get_user():
    """Retrieves a users information from the database"""
    _db = db_login()
    req_user = request.form["user"]
    user = _db.users.find_one({"username": req_user})
    return dumps(user)


@APP.route("/getTrip", methods=["POST"])
def get_trip():
    """Retrieves trip information for a particular user and trip ID"""
    _db = db_login()
    req_user = request.form["user"]
    trip_id = request.form["trip_id"]
    trip = _db.users.find_one({"username": req_user, "trips.name": trip_id})
    return dumps(trip)

@APP.route("/getPlaylists", methods=["POST"])
def get_tracks():
    """Retrieves list of tracks for a given trip ID"""
    _db = db_login()
    req_user = request.form["user"]
    trip_id = request.form["trip_id"]
    query = {"tracks": {"$elemMatch": {'type': 'tracks'}}}
    tracks = _db.users.find_one({"username": req_user, "trips.name": trip_id}, query)
    return dumps(tracks)


############################################################
# Retrieving city playlists by city name or coordinates
############################################################
@APP.route("/playlistbycity", methods=['POST'])
def get_by_city():
    """Returns playlist of popular music for given city name"""
    city = request.form["city"]
    print(city);
    geolocator = Nominatim()
    location = geolocator.geocode(city, timeout=5)
    if location:
        lat = location.latitude
        lng = location.longitude
        my_coord = (float(lat), float(lng))
        return retrieve_playlist(my_coord)
    else:
        data = {}
        data['city'] = "error"
        json_data = json.dumps(data)
        print(json_data);
        return json_data            
   
        


@APP.route("/getPlaylist", methods=['POST'])
def get_by_coord():
    """Returns playlist of popular music for given lat/lng """
    mylat = request.form["lat"]
    mylng = request.form["lng"]
    my_coord = (float(mylat), float(mylng))
    return retrieve_playlist(my_coord)


############################################################
# Helper functions for logic & generalizing
############################################################

# TODO: Switch to using MongoDB geospatial data to query location instead
def retrieve_playlist(my_coord):
    """Helper function to retrieve playlist regardless of input """
    _db = db_login()
    city_list = _db.cities.find()
    # max distance between 2 points on earth
    min_distance = 20036
    city_playlist = ""
    city_name = "NOT FOUND"
    for city in city_list:
        city_coord = (float(city.get('lat')), float(city.get('lng')))
        distance = haversine(my_coord, city_coord)
        if min_distance > distance:
            min_distance = distance
            city_playlist = city.get('distinctive_music')
            city_name = city.get('city')

    search_string = "/playlist/"
    # Get index of ID
    playlist_index = city_playlist.index(search_string)
    playlist_id = city_playlist[playlist_index + len(search_string):]
    # Return the playlist ID in URI form
    data = {}

    data['city'] = city_name
    data['playlist'] = playlist_id
    json_data = json.dumps(data)
    return json_data

def db_login():
    """Helper function to log into APP MongoDB """
    _mongouri = "mongodb://mcarri01:mustrip@ds017896.mlab.com:17896/mustrip"
    client = MongoClient(_mongouri)
    return client.mustrip

def search_users(_db, req_user):
    """Helper function to search through users in db """
    in_list = False
    user_list = _db.users.find()
    for user in user_list:
        if user['username'] == req_user:
            in_list = True
    return in_list

if __name__ == "__main__":

    PORT = int(os.environ.get('PORT', 5000))
    APP.run(host='0.0.0.0', port=PORT)
