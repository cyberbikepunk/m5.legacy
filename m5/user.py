""" User classes and related stuff. """


from requests import Session, Request
from pprint import PrettyPrinter
from getpass import getpass

from m5.miner import Miner
from m5.database import Database
from m5.utilities import record


class Messenger:
    """
    The Messenger class manages user activity for couriers freelancing
    for Messenger (http://messenger.de). This is the default user class.
    It can theoretically be overridden for other courier companies.
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

        self.miner = Miner(self._session, self._server)
        self.interpreter = Database()

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
