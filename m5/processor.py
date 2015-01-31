""" The Processor class and descendants """

__author__ = 'opabinia'

from geopy.geocoders import Nominatim

from m5.model import Model


class Processor(Model):
    """
    The processor takes freshly scraped data by the miner
    and returns tables that can be merged into the database.
    """

    pass


class Checkpoint(Model):

    def _unserialize(self) -> dict:
        pass

    def _extract_keys(self)-> tuple():
        """ Takes unserialized data and extract the table keys.
        :return: checkpoint_id, [checkin_id, order_id, etc...)
        """
        pass

    def _package(self):
        """ Takes unserialized data and table keys.
        :return: checkpoint_id, [checkin_id, order_id, etc...)
        """
        pass

    def pretty_address(self, checkpoint_id: dict) -> str:
        """ Take a dictionnary and make a string for the geocoder.

        :param address: address field name/value pairs
        :return: geocodable address string
        """
        pass

    @log_me
    def geocode(self, checkpoint_id: dict) -> tuple:
        """
        Geocode an address with Nominatim (http://nominatim.openstreetmap.org).

        :return position: longitude, latitude
        """

        geolocator = Nominatim()
        address = self.pretty_address(checkpoint_id)
        location = geolocator.geocode(address)

        position = (location.address,
                    (location.latitude, location.longitude),
                    location.raw)

        return lat, lon