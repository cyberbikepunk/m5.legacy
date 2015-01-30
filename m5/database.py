"""  The database class and related stuff """

from m5.utilities import notify
from pickle import load, dump
from os.path import isdir
from os import mkdir

from m5.utilities import log_me, safe_io


class Database:
    """ Here is where the database logistics happen. """

    def __init__(self, username: str):
        """
        If the user is new, create a database file with empty tables:
            - jobs
            - checkins
            - checkpoints

        :param username: the owner
        :return: a Database object
        """

        self.username = username
        self.path = '../users/{}/'.format(self.username)

        self.tables = {'jobs',
                       'checkins',
                       'checkpoints'}

        # Create a class attribute
        # for each table on the fly
        for table in self.tables:
            setattr(self, table, list())

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

    @log_me
    def process(self, jobs: list) -> list:
        """
        Scraped data fields are returned as raw strings by the miner.
        This is where the data gets processed before it can be stored to
        the database.
        Unserialize the fields, geocode each address and return a table
        of checkpoints (with possible duplicates) and a table of checkins.

        Checkpoints table:
            - a list of tuples(checkpoint_id, job_ids, checkpoint)
            - checkpoint_id: a unique string (primary key)
            - job_ids: a set of correspon job ids (secondary key)
            - checkpoint: a dictionnay of name/value pairs

        Checkins table: tuple(checkin_id, job_id, checkin)
            - checkin_id: a unique string (primary key)
            - job_ids: a set of matching job ids (secondary key)
            - ckeckin: a dictionnay of name/value pairs
        """
        pass

    def merge_addresses(self):
        pass

    def save(self, table: str=None):
        """ Unpickle the database or tables from file """
        tables = {table} if table else self.tables
        for table in tables:
            self.save_table(table)

    def load(self, table: str=None):
        """ Pickle the database or tables to file """
        tables = {table} if table else self.tables
        for table in tables:
            self.load_table(table)

    @log_me
    @safe_io
    def save_table(self, table: str):
        """ Pickle one table to file """

        filename = self.path + table + '.pkl'
        with open(filename, 'wb+') as f:
            # Use the highest protocol
            dump(getattr(self, table), f, -1)
        notify('Saved {} table to file.', table)

    @log_me
    @safe_io
    def load_table(self, table: str):
        """ Unpickle one table from file. """

        filename = self.path + table + '.pkl'
        with open(filename, 'wb+') as f:
            setattr(self, table, load(f))
        notify('Loaded {} table from file.', table)