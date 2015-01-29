""" Miscellaneous utility functions """

from datetime import datetime
from geopy.geocoders import Nominatim


def record(message, *args):
    """
    Print a message to screen.
    """

    message = message.format(*args)
    timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
    tagged_message = timestamp + ' | ' + message
    print(tagged_message)


def serialize_address(address: dict):
    """
    Take a dictionnary and make a string for the geocoder.

    :param address: address field name/value pairs
    :return: geocodable address string
    """

    return address_string

def geocode(address: dict) -> tuple:
    """
    Geocode an address with Nominatim (http://nominatim.openstreetmap.org).

    :return position: longitude, latitude
    """

    geolocator = Nominatim()
    address_string = serialize_address(address)
    location = geolocator.geocode(address_string)

    position = (location.address,
                (location.latitude, location.longitude),
                location.raw)

    return position
