""" Miscellaneous utility classes and fs """

from datetime import datetime
from geopy import Nominatim


def log_me(f):
    return f


def time_me(f):
    return f


def safe_io(f):
    return f


def safe_request(f):
    return f


def notify(message, *args):
    """ Print a message to the screen. """

    message = message.format(*args)
    timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
    print('%s | %s' % timestamp, message)


@log_me
def geocode(self, address: dict) -> dict:
    """
    Geocode an address with Nominatim (http://nominatim.openstreetmap.org).

    :return position: longitude, latitude
    """

    geolocator = Nominatim()
    address = self.pretty_address(address)
    location = geolocator.geocode(address)

    position = (location.address,
                (location.latitude, location.longitude),
                location.raw)

    return None


def area():
    """ Postal code polygon area
    :return:
    """
    pass
