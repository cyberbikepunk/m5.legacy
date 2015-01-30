""" Address class and related stuff. """

from geopy.geocoders import Nominatim


class Address():

    def serialize_address(address: dict):
        """
        Take a dictionnary and make a string for the geocoder.

        :param address: address field name/value pairs
        :return: geocodable address string
        """

        return address_string

    @log_me
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