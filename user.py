#!/usr/bin/python

from requests import Session
from pickle import load, dump
from os.path import isfile
from datetime import datetime
# from getpass import getpass

from miner import Miner


class User:
    """
    The User class manages user information, activity and stores user
    data. In short, it's the backbone of the program.
    """

    def __init__(self):
        """
        Initialize all User class attributes.
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
        :return: (str) the company server
        """
        return 'http://bamboo-mec.de/'

    def _credentials(self):
        """
        Return the payload for the post request on the login page,
        as required by the request module.

        :return: (dict) user credentials
        """
        return {'username': self._username,
                'password': self._password}

    def _userfile(self):
        """
        The user data file contains pickled data. For now
        we store everything in the working directory.

        :return: (str) Relative path to the user data file
        """
        return self._username + '.pkl'

    def authenticate(self):
        """
        Prompt for user credentials and try logging onto the company
        server. Raise a flag when successfully logged in. We detect success
        by looking for the word 'erfolgreich' (success in german) in the
        html returned by the server. Is there a better way?
        """
        path = 'll.php5'
        self._username = 'm-134'                # input('Enter username: ')
        self._password = 'PASSWORD'             # getpass('Enter password: ')
        self._session = Session()
        self._session.headers.update({'user-agent': 'Mozilla/5.0 '
                                                    '(X11; Ubuntu; Linux x86_64; rv:31.0) '
                                                    'Gecko/20100101 Firefox/31.0'})
        response = self._session.post(self._server+path,
                                      self._credentials(),
                                      timeout=10.0)

        if response.text.find('erfolgreich') > 0:
            self._rec('Hello {}, you are now logged in!', self._username)
        else:
            self._rec('Invalid username or password... try again!')
            self.authenticate()

    def is_returning(self):
        """
        Test whether the user has used the program before by looking for
        a matching data file. Avoid mining data twice.

        :return: (bool) True if we find the file.
        """

        if isfile(self._userfile()):
            self._rec('Data file {} found! You are a returning user.', self._userfile())
            return True
        else:
            self._rec('Welcome {}! You are a newbie.', self._username)
            return False

    def save_data(self):
        """
        Pickle the user data object to file. This is not
        best way to store large quantities of data but it will
        do for now.
        """
        f = open(self._userfile(), 'wb')
        dump(self, f, -1)  # Highest protocol
        f.close()
        self._rec('Current data saved to {}.', self._userfile())

    def load_data(self):
        """
        Load the pickled user data object from the file.
        We don't handle any exexptions because we need
        access to past data.
        """
        f = open(self._userfile(), 'rb')
        self.data = load(f)
        f.close()
        self._rec('Existing data loaded from {}.', self._userfile())

    def save_log(self):
        """
        Append the all current log messages to the user log file.
        """
        logfile = self._username + '.log'
        f = open(logfile, 'a')
        f.write('\n'.join(self._log) + '\n\n')
        f.close()
        self._rec('User log saved to {}', logfile)

    def _rec(self, message, *args):
        """
        Write to the user log (list of strings). The message
        is also sent to the screen.

        :argument message: (str) the unformatted log message
        :argument *args: (str) positional formatting arguments
        """
        message = message.format(*args)
        timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
        entry = timestamp + ' | ' + message
        self._log.append(entry)
        print(entry)

    def logout(self):
        """
        Logout from the company server by 'clicking' on logout:
        """
        path = 'index.php5'
        payload = {'logout': '1'}
        response = self._session.get(self._server + path, params=payload)
        if response.status == 302:
            self._rec('Successfully logged out. Goodbye!')

    def prompt_date(self):
        """
        Prompt for a date in the format 'dd.mm.yyyy' or the word 'quit'.
        If the date format cannot be read, prompt again!

        :return: (datetime obj) the chosen date
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
        Launch the mining process: check wether that particular day has
        already been mined. If so, well, don't do anything. If not,
        instantiate a miner object and start mining. If the mining
        process is succesfull, make sure the resulting data is stored!
        """
        m = Miner(date=date,
                  session=self._session,
                  server=self._server)

        if m.has_been_mined():
            self._rec('{} has already been mined', date.strftime('%d.%m.%Y'))
        else:
            jobs = m.fetch_jobs()
            if jobs:
                for j in jobs:
                    data = m.scrape_job(j)
                    print(data)
                    exit()
                    # m.package_job(data)
                    # self.mined.add(date)
                self._rec('Mined successfully: ', date.strftime('%d.%m.%Y'))

