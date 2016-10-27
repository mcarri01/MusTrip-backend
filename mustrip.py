import os
import ast
from flask import Flask
from geopy.geocoders import Nominatim
import json
from flask import request
from pymongo import MongoClient
from haversine import haversine

app = Flask(__name__)

@app.route('/')
def index():
	return "Welcome"

@app.route('/addPlaylist', methods=['POST'])
def add_playlist():

	db = db_login()
	req_user = request.form["user"]
	playlist_id = request.form["playlist"]
	user_exists = search_users(db, req_user)
	if user_exists:
		db.users.update_one({'username': req_user}, {"$addToSet": {'trips': {'playlists' : playlist_id}}})
		return json.dumps({"status": "success"})
	else:
		return json.dumps({"status": "User not Found"})
	

@app.route("/addTrip", methods=["POST"])
def add_trip():
	db = db_login()
	req_user = request.form["user"]
	trip_id = request.form["trip_id"]
	user_exists = search_users(db, req_user)
	if user_exists:
		db.users.update_one({'username': req_user}, {"$addToSet": {'trips': trip_id}})
		return json.dumps({"status": "success"})
	else:
		return json.dumps({"status": "User not Found"})



@app.route("/getPlaylists", methods=["POST"])
def get_playlists():
	db = db_login()
	req_user = request.form["user"]
	user_exists = search_users(db, req_user)
	if user_exists:
		user = db.users.find_one({"username" : req_user})
		return json.dumps(user['trips'])
	else:
		return json.dumps({"status": "NOT FOUND"})

@app.route('/addUser', methods=['POST'])
def add_user():
	db = db_login()
	req_user = request.form["user"]
	user_list = db.users.find()
	user_exists = search_users(db, req_user)
	if user_exists:
		db.users.insert_one({"username": req_user})
		return json.dumps({"status": "exists"})
	else:
		return json.dumps({"status": "success"})

@app.route("/playlistbycity", methods=['POST'])
def get_by_city():
	city = request.form["city"]
	geolocator = Nominatim()
	location = geolocator.geocode(city)
	lat = location.latitude
	lng = location.longitude
	my_coord = (float(lat), float(lng))
	return retrieve_playlist(my_coord)


@app.route("/getPlaylist", methods=['POST'])
def get_by_coord():
	mylat = request.form["lat"]
	mylng = request.form["lng"]
	my_coord = (float(mylat), float(mylng))
	return retrieve_playlist(my_coord)

def retrieve_playlist(my_coord):
	db = db_login()
	city_list = db.cities.find()
	# max distance between 2 points on earth
	min_distance = 20036
	city_playlist = 0
	city_name = "NOT FOUND"
	for city in city_list:
		city_coord = (float(city.get('lat')), float(city.get('lng')))
		distance = haversine(my_coord, city_coord)
		if min_distance > distance:
			min_distance = distance
			city_playlist = city.get('distinctive_music')
			city_name = city.get('city')

	base_uri = "https://api.spotify.com/v1/users/thesoundsofspotify/playlists/"
	search_string = "/playlist/"
	# Get index of ID
	playlist_index = city_playlist.index(search_string)
	playlist_id = city_playlist[playlist_index + len(search_string):]
	# Return the playlist ID in URI form
	data = {}	
	data['city'] = city_name
	data['playlist'] = base_uri + playlist_id
	json_data = json.dumps(data)
	return json_data

def db_login():
	MONGODB_URI = "mongodb://mcarri01:mustrip@ds017896.mlab.com:17896/mustrip"
	client = MongoClient(MONGODB_URI)
	return client.mustrip

def search_users(db, req_user):
	in_list = False
	user_list = db.users.find()
	for user in user_list:
		if user['username'] == req_user:
			in_list = True
			
	return in_list

if __name__ == "__main__":

	port = int(os.environ.get('PORT', 5000))
    	app.run(host='0.0.0.0', port=port)

