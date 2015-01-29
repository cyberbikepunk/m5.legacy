"""  The database class and related stuff """

from m5.utilities import record
from pickle import load, dump
from os.path import isdir


class Database():
    """
    Here is where the database logistics happen.
    """

    def __init__(self, username: str) -> Database:
        """
        Instantiate a database object. Create the database file
        if needed. The database has the following tables:

            - jobs
            - addresses
            - checkpoints

        :param username: the owner
        :return: a Database object
        """

        self.username = username
        self.directory = '../users/'.format(self.username)

        self.tables = {'jobs',
                       'addresses',
                       'checkpoints'}

        for table in self.tables:
            setattr(table, list())

        if not self.exists:
            self.pickle()
            record('Created a new database.')

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
        of unduplicated checkpoints and checkins, structured like this...

        Checkpoints table:
            - a list of tuples(checkpoint_id, job_ids, checkpoint)
            - checkpoint_id: a unique string (primary key)
            - job_ids: a SET of correspon job ids (secondary key)
            - checkpoint: a dictionnay of name/value pairs

        Checkins table: tuple(checkin_id, job_id, checkin)
            - checkin_id: a unique string (primary key)
            - job_ids: a set of matching job ids (secondary key)
            - ckeckin: a dictionnay of name/value pairs
        """
        return checkpoints, checkins

    @log_me
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
                record('Saved {} table successfully', name)

    @log_me
    def _unpickle(self):
        """ Load the user database from file. """

        # TODO Handle file I/O errors properly

        for name, table in self.tables.items():
            filename = self.directory.join(table).join('pkl')

            with open(filename, 'rb') as f:
                table = load(f)
                record('Loaded {} table successfully', name)

        # TODO call class attributes on the fly
