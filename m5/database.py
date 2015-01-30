"""  The database class and related stuff """

from m5.utilities import notify
from pickle import load, dump
from os.path import isdir


class Database():
    """
    Here is where the database logistics happen.
    """

    def __init__(self, username: str) -> Database:
        """
        If the user is new, create a database file
        with 3 empty tables:
            - jobs
            - checkins
            - checkpoints

        :param username: the owner
        :return: a Database object
        """

        self.username = username
        self.directory = '../users/'.format(self.username)

        self.tables = {'jobs',
                       'checkins',
                       'checkpoints'}

        for table in self.tables:
            setattr(table, list())

        if not self.exists:
            self.pickle()
            notify('Created a new database.')

    @property
    def exists(self) -> bool:
        """
        True if the user has a local database.
        """

        if isdir(self.directory):
            return True
        else:
            return False

    @log_me
    def process_addresses(self, addresses: list) -> list:
        """
        Scraped data fields are returned as raw strings by the miner.
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
        return checkpoints, checkins

    def merge_addresses(self):
        pass

    @log_me
    def pickle(self):
        """ Save the user database to file. """

        for name, table in self.tables.items():
            filename = self.directory.join(table).join('pkl')

            with open(filename, 'wb+') as f:
                # Pickle with the highest protocol
                dump(table, f, -1)
                notify('Saved {} table successfully', name)

    @log_me
    def _unpickle(self):
        """ Load the user database from file. """

        # TODO Handle file I/O errors properly

        for name, table in self.tables.items():
            filename = self.directory.join(table).join('pkl')

            with open(filename, 'rb') as f:
                table = load(f)
                notify('Loaded {} table successfully', name)

        # TODO call class attributes on the fly
