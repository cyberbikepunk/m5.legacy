#!/usr/bin/python

from requests import Session
from pickle import load, dump
from os.path import isfile
from datetime import datetime
# from getpass import getpass

from miner import Miner


class User:
    """
    The User class manages user information and activity.
    """

    def __init__(self):
        """
        Initialize class attributes.
        """
        self._username = ''
        self._password = ''
        self.is_active = True
        self._session = None
        self.mined = set()
        self.data = []
        self._log = []

    @property
    def _server(self):
        """
        :return: (str) The company host server.
        """
        return 'http://bamboo-mec.de/'

    @property
    def _credentials(self):
        """
        :return: (dict) The payload for the post request on the login page.
        """
        return {'username': self._username,
                'password': self._password}

    @property
    def _userfile(self):
        """
        :return: (str) The relative path to the user data file.
        """
        return self._username + '.pkl'

    @property
    def is_returning(self):
        """
        :return: (bool) True if we find a user data file.
        """
        if isfile(self._userfile):
            self._rec('Data file {} found! You are a returning user.', self._userfile)
            return True
        else:
            self._rec('Welcome {}! You are a newbie.', self._username)
            return False

    def authenticate(self):
        """
        Log onto the company server.
        """
        login_url = self._server + 'll.php5'
        self._username = 'm-134'                # input('Enter username: ')
        self._password = 'PASSWORD'             # getpass('Enter password: ')
        self._session = Session()
        self._session.headers.update({'user-agent': 'Mozilla/5.0 '
                                                    '(X11; Ubuntu; Linux x86_64; rv:31.0) '
                                                    'Gecko/20100101 Firefox/31.0'})
        response = self._session.post(login_url,
                                      self._credentials,
                                      timeout=10.0)
        # We detect success by looking for the word success in german.
        if response.text.find('erfolgreich') > 0:
            self._rec('Hello {}, you are now logged in!', self._username)
        else:
            self._rec('Invalid username or password... try again!')
            self.authenticate()

    def load_data(self):
        """
        Load the pickled user data from file. We don't handle
        exceptions because we absolutely need past data.
        """
        f = open(self._userfile, 'rb')
        self.data = load(f)
        f.close()
        self._rec('Existing data loaded from {}.', self._userfile)

    def save_data(self):
        """
        Pickle the user data to file. No database for now.
        """
        f = open(self._userfile, 'wb')
        dump(self, f, -1)  # Highest protocol
        f.close()
        self._rec('Current data saved to {}.', self._userfile)

    def save_log(self):
        """
        Append all current log messages to user log file.
        """
        logfile = self._username + '.log'
        f = open(logfile, 'a')
        f.write('\n'.join(self._log) + '\n\n')
        f.close()
        self._rec('User log saved to {}', logfile)

    def _rec(self, message, *args):
        """
        Write to user log and print to screen.

        :argument message: (str) Log message format.
        :argument *args: (str) Positional arguments.
        """
        message = message.format(*args)
        timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
        entry = timestamp + ' | ' + message
        self._log.append(entry)
        print(entry)

    def logout(self):
        """
        Logout from the server.
        """
        path = 'index.php5'
        payload = {'logout': '1'}
        response = self._session.get(self._server + path, params=payload)
        if response.status == 302:
            self._rec('Successfully logged out. Goodbye!')

    def prompt_date(self):
        """
        Prompt for 'quit' or a date in the format 'dd.mm.yyyy'.
        If the date cannot be read, prompt again!

        :return: (datetime obj) The chosen date.
        """
        input_string = '19.12.2014'  # input('Enter a date or type "quit":')
        if input_string == 'quit':
            self.is_active = False
        else:
            try:
                day = datetime.strptime(input_string, '%d.%m.%Y')
            except ValueError:
                print('Input format must be dd-mm-yy. Try again...')
                self.prompt_date()
            else:
                return day

    def mine(self, date):
        """
        Check whether that day has been mined before. If not, mine and store the data.
        """
        m = Miner(date=date,
                  session=self._session,
                  server=self._server)

        if m.has_been_mined:
            self._rec('{} has already been mined', date.strftime('%d.%m.%Y'))
        else:
            jobs = m.fetch_jobs()
            if jobs:
                for j in jobs:
                    html = m.get_job(j)
                    if False:  # Todo : stop here for now
                        data = m.scrape_job(html)
                        m.package_job(data)
                        self.mined.add(date)
                self._rec('Mined successfully: {}', date.strftime('%d.%m.%Y'))

