"""  The database class and related stuff """

from m5.utilities import notify
from pickle import load, dump
from os.path import isdir
from os import mkdir

from m5.utilities import safe_io


class Database:
    """ Here is where the database logistics happen. """

    def __init__(self, username: str):
        """
        If the user is new, create a database file with empty tables:
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
                       'sessions'}

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