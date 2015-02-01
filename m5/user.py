""" User classes and related stuff. """

from getpass import getpass

from requests import Session
from sandbox.database import Database
from m5.utilities import notify, log_me, safe_request


class User:
    """
    The User class manages user activity for couriers freelancing
    for User (http://messenger.de). This is the default user class.
    It can theoretically be overridden for other courier companies.
    """

    _DEBUG = True

    def __init__(self, username: str, password: str):
        """  Authenticate the user and instantiate a database. """

        self.username = username
        self._password = password

        # The company server
        self._server = 'http://bamboo-mec.de/'
        self._session = Session()

        self._authenticate(self.username, self._password)
        self.db = Database(username)

    @log_me
    @safe_request
    def _authenticate(self, username=None, password=None):
        """ Make login attempts until successful. """

        if not username:
            self.username = input('Enter username: ')
        if not password:
            self._password = getpass('Enter password: ')

        login_url = self._server + 'll.php5'
        credentials = {'username': self.username,
                       'password': self._password}

        # Pretend
        headers = {'user-agent': 'Mozilla/5.0'}
        self._session.headers.update(headers)

        response = self._session.post(login_url, credentials)

        if not response.ok:
            self._authenticate()
        else:
            notify('You are now logged in.')

    def quit(self):
        """ Make a clean exit from the program. """

        self.db.save()
        self._logout()
        exit(0)

    def _logout(self):
        """ Logout from the server and close the session. """

        url = self._server + 'index.php5'
        payload = {'logout': '1'}

        response = self._session.get(url, params=payload)

        if response.history[0].status_code == 302:
            # We have been redirected to the home page
            notify('Logged out successfully. Goodbye!')

        self._session.close()
