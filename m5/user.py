""" User classes and related stuff. """


from requests import Session, Request
from pickle import load, dump
from os.path import isfile
from pprint import PrettyPrinter
from getpass import getpass

from m5.miner import MessengerMiner
from m5.interpreter import Interpreter
from m5.utilities import record


class Messenger:
    """
    The Messenger class manages user activity for couriers freelancing
    for Messenger (http://messenger.de). This is the default user class.
    It can be extended to other courier companies.

    Public methods (API):
        - mine('dd.mm.yyyy'): mine one day of data
        - save(): pickle the user object
        - quit(): make a clean exit
        - more to come...
    """

    _DEBUG = True

    def __init__(self, username='', password=''):
        """  Authenticate the user and fetch local data if any. """

        self.username = username
        self._password = password
        self._session = None
        self.mined = dict()
        self.interpreted = set()
        self.raw_data = list()
        self.data = list()

        # The remote server where the company data is stored:
        self._server = 'http://bamboo-mec.de/'
        self._authenticate(self.username, self._password)

        # Data that has already been mined is stored locally
        self._datafile = '../users/{}.pkl'.format(self.username)
        if self._is_returning:
            self._load()

        self.miner = MessengerMiner(self._session, self._server)
        self.interpreter = Interpreter()

    def _authenticate(self, username='', password=''):
        """ Make login attempts until successful. """

        if not username:
            self.username = input('Enter username:')
        if not password:
            self._password = getpass('Enter password:')

        login_url = self._server + 'll.php5'
        credentials = {'username': self.username, 'password': self._password}

        self._session = Session()
        # Pretend we're browsing
        headers = {'user-agent': 'Mozilla/5.0 Firefox/31.0'}
        self._session.headers.update(headers)

        # Make a login attempt
        # TODO request error handling
        response = self._session.post(login_url, credentials)
        if not response.ok:
            self._authenticate()
        else:
            record('You are logged in.')

    @property
    def _is_returning(self) -> bool:
        """ True if the user has local data. """

        if isfile(self._datafile):
            record('You are a returning user.')
            return True
        else:
            record('You are a new user.')
            return False

    def _load(self):
        """ Load pickled user data from file. """

        # TODO Handle file I/O errors properly
        with open(self._datafile, 'rb') as f:
            objects = load(f)
            record('Loaded user data successfully')

        # Unpack the pickled object
        self.mined = objects['miners']
        self.data = objects['data']

    def save(self):
        """ Pickle the user data to file. Yep, that our database! """

        # Package up for pickling
        objects = {'miners': self.mined, 'data': self.data}

        with open(self._datafile, 'wb+') as f:
            # Pickle with the highest protocol
            dump(objects, f, -1)
            record('Saved user data successfully')

    def quit(self):
        """ Make a clean exit from the program. """

        self.save()
        self._logout()
        exit(0)

    def _logout(self):
        """ Logout from the server and close the session. """

        url = self._server + 'index.php5'
        payload = {'logout': '1'}
        response = self._session.get(url, params=payload)
        # We have been redirected once
        response = response.history[0]

        # Last words before we exit
        if response.status_code == 302:
            record('Logged out successfully. Goodbye!')

        self._session.close()

    def interpret(self, date):
        pass

    def mine(self, date):
        """
        If that date hasn't been mined before, mine it!

        :param date_string: one day in the format dd-mm-yyyy
        """

        jobs, addresses = self.miner.process(date)