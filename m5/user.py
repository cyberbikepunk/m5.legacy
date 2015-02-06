""" User classes and related stuff. """

from getpass import getpass
from requests import Session as RemoteSession
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from m5.utilities import notify, log_me, safe_request


class User:
    """
    The User class manages user activity for couriers freelancing
    for User (http://messenger.de). This is the default user class.
    It can theoretically be overridden for other courier companies.
    """

    Base = declarative_base()
    Session = sessionmaker()

    _DEBUG = True

    def __init__(self, username: str, password: str):
        """  Authenticate the user on the remote server and initialise the local database. """

        self.username = username
        self._password = password

        # The company server
        self.remote_server = 'http://bamboo-mec.de/'
        self.remote_session = RemoteSession()
        self._authenticate(self.username, self._password)

        # One database per user
        self.db_path = '../users/db_%s.sqlite' % self.username
        self.db_engine = create_engine('sqlite:///%s' % self.db_path, echo=self._DEBUG)
        self.Base.metadata.create_all(self.db_engine)
        self.Session.configure(bind=self.db_engine)

        # We query on this:
        self.db = self.Session()

    @log_me
    @safe_request
    def _authenticate(self, username=None, password=None):
        """ Make login attempts until successful. """

        if not username:
            self.username = input('Enter username: ')
        if not password:
            self._password = getpass('Enter password: ')

        login_url = self.remote_server + 'll.php5'
        credentials = {'username': self.username,
                       'password': self._password}

        # Pretend
        headers = {'user-agent': 'Mozilla/5.0'}
        self.remote_session.headers.update(headers)

        response = self.remote_session.post(login_url, credentials)

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

        url = self.remote_server + 'index.php5'
        payload = {'logout': '1'}

        response = self.remote_session.get(url, params=payload)

        if response.history[0].status_code == 302:
            # We have been redirected to the home page
            notify('Logged out successfully. Goodbye!')

        self.remote_session.close()
