# backend/services/geocoder.py
import googlemaps
from datetime import datetime

GMAPS_API_KEY = ""
gmaps = googlemaps.Client(key=GMAPS_API_KEY)

def get_address_from_coords(lat: float, lng: float):
    reverse_geocode_result = gmaps.reverse_geocode((lat, lng))
    return reverse_geocode_result[0]['formatted_address'] if reverse_geocode_result else "Address not found"

def get_coords_from_address(address: str):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        loc = geocode_result[0]['geometry']['location']
        return loc['lat'], loc['lng']
    return None, None