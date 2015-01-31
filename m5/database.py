"""  The database class and extention classes. """

from pickle import load, dump
from os.path import isdir
from os import mkdir
from geopy import Nominatim
from ordered_set import OrderedSet

from m5.utilities import safe_io, log_me, safe_request, notify


class Database:
    """ Here is where the database logistics happen. """

    def __init__(self, username: str):
        """
        If the user is new, create database files with empty tables:
            - jobs
            - checkins
            - checkpoints
            - sessions

        :param username: the owner
        :return: a Database object
        """

        self.username = username
        self.path = '../users/{}/'.format(self.username)

        self.tables = {'jobs',
                       'checkins',
                       'checkpoints',
                       'sessiotns'}

        # Create a class attribute
        # for each table on the fly
        for table in self.tables:
            carpenter = getattr(__name__, table)
            tb = carpenter()
            setattr(self, table, tb)

        if not self.exists:
            # Create a database
            mkdir(self.path)
            self.save()
            notify('Created a new database.')

    @property
    def exists(self) -> bool:
        """ True if the user has a database. """
        exists = True if isdir(self.path) else False
        return exists

    def merge(self):
        pass

    def save(self, table: str=None):
        """ Pickle the database or a table from file. """
        tables = {table} if table else self.tables
        for table in tables:
            self.save_table(table)

    def load(self, table: str=None):
        """ Unpickle the database or a table to file. """
        tables = {table} if table else self.tables
        for table in tables:
            self.load_table(table)

    @safe_io
    def save_table(self, table: str):
        """ Pickle one table to file. """
        filename = self.path + table + '.pkl'
        with open(filename, 'wb+') as f:
            # Use the highest protocol
            dump(getattr(self, table), f, -1)
        notify('Saved {} table to file.', table)

    @safe_io
    def load_table(self, table: str):
        """ Unpickle one table from file. """
        filename = self.path + table + '.pkl'
        with open(filename, 'wb+') as f:
            setattr(self, table, load(f))
        notify('Loaded {} table from file.', table)


class Checkpoint(Database):
    """ A checkpoint is a geographic position. There's no time dimension.
            Checkpoints table:
            - a list of tuples(checkpoint_id, job_ids, checkpoint)
            - checkpoint_id: a unique string (primary key)
            - job_ids: a set of correspon job ids (secondary key)
            - checkpoint: a dictionnay of name/value pairs

    """

    def serialize(self) -> str:
        """ Return a string to feed the Nominatim geocoder.
        :return: e.g. "Meteorstrasse 14, 13127 Berlin, Germany"
        """
        pass

    @log_me
    @safe_request
    def geocode(self, checkpoint: dict) -> tuple:
        """ Geocode an address with Nominatim: http://nominatim.openstreetmap.org
        :return position: longitude, latitude
        """

        geolocator = Nominatim()
        serial_checkpoint = self.serialize(checkpoint)
        loc = geolocator.geocode(serial_checkpoint)

        return loc.latitude, loc.longitude

    @staticmethod
    def primary_key(self, jobs: dict) -> set:
        """
        :return:
        """
        pass

    def secondary_keys(self, jobs: dict) -> set:
        """
        :return:
        """
        pass

    def __eq__(self, other):
        """  Loosely compare two checkpoints """
        # Tolerance in meters?
        pass

    def package(self):
        """
        :return: """
        pass


class Checkin(Database):
    """ A Checkin is moment when the messenger stops at a checkpoint.

    Checkins table:
        - tuple(checkin_id, job_id, checkin)
        - checkin_id: a unique string (primary key)
        - job_ids: a set of matching job ids (secondary key)
        - ckeckin: a dictionnay of name/value pairs
    """

    def unserialize(self, raw_data: dict) -> dict:
        pass

    def primary_key(self, jobs: dict) -> OrderedSet:
        """ The timestamp is the primary key in the table.
        :return:
        """
        pass

    def secondary_keys(self, jobs: dict) -> set:
        """ The geoposition is the secondary key.
        :return: lat, long tuples
        """
        pass

    def package(self):
        """ Package a dictionnary into a table. See the Miner
        :return: """
        pass