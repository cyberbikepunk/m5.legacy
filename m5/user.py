""" User classes and related stuff. """


from requests import Session, Request
from pickle import load, dump
from os.path import isfile
from datetime import datetime
from pprint import PrettyPrinter
from getpass import getpass

from m5.miner import MessengerMiner


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

    def __init__(self, username='', password=''):
        """  Authenticate the user and fetch local data if any. """
        
        self._username = username
        self._password = password
        self._session = None
        self._miners = set()
        self._data = list()

        # The remote server where the company data is stored:
        self._server = 'http://bamboo-mec.de/'
        self._authenticate(self._username, self._password)

        # Data that has already been mined is stored locally
        self._datafile = 'users/{}.pkl'.format(self._username)
        if self._is_returning:
            self._load()

    def _authenticate(self, username='', password=''):
        """ Make login attempts until successful. """

        if not username:
            self._username = input('Enter username:')
        if not password:
            self._password = getpass('Enter password:')

        login_url = self._server + 'll.php5'
        credentials = {'username': self._username, 'password': self._password}
        request = Request('post', login_url, params=credentials).prepare()

        self._session = Session()
        # Pretend we're browsing
        headers = {'user-agent': 'Mozilla/5.0'}
        self._session.headers.update(headers)

        # Make a login attempt
        # TODO request error handling
        response = self._session.send(request, timeout=10.0)
        if not response.ok:
            self._authenticate()
        else:
            self._print('You are logged in.')

    @property
    def _is_returning(self) -> bool:
        """ True if the user has local data. """

        if isfile(self._datafile):
            self._print('You are a returning user.')
            return True
        else:
            self._print('You are a new user.')
            return False

    def _load(self):
        """ Load pickled user data from file. """

        # TODO Handle file I/O errors properly
        with open(self._datafile, 'rb') as f:
            objects = load(f)
            self._print('Loaded user data successfully')

        # Unpack the pickled object
        self._miners = objects['miners']
        self._data = objects['data']

    def save(self):
        """ Pickle the user data to file. Yep, that our database! """

        # Package up for pickling
        objects = {'miners': self._miners, 'data': self._data}

        with open(self._datafile, 'wb+') as f:
            # Pickle with the highest protocol
            dump(objects, f, -1)
            self._print('Saved user data successfully')

    def _print(self, message, *args):
        """ Print a status message to screen. """

        message = message.format(*args)
        timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
        tagged_message = self._username + ' | ' + timestamp + ' | ' + message
        print(tagged_message)

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
            self._print('Logged out successfully. Goodbye!')

        # self._session.close()

    def prompt(self, input_string=None):
        """ Prompt the user for quit or a public method. """

        if not input_string:
            try:
                input_string = input('Enter "method()" or "quit()":  ')
            except (KeyboardInterrupt, SystemExit):
                # Avoid corrupting data:
                # exit cleanly every time
                print('\n')
                self.quit()
            else:
                try:
                    exec('self.' + input_string)
                except (
                        SyntaxError,
                        ValueError,
                        TypeError,
                        AttributeError,
                        NameError
                ) as error:
                    print(error.__class__.__name__ + ' | ' + error.msg)
                    self.prompt()

    def mine(self, date_string):
        """
        If that date hasn't been mined before, mine it!

        :param date_string: one day in the format dd-mm-yyyy
        """

        # Convert the input to a datetime object
        date = datetime.strptime(date_string, '%d-%m-%Y')

        # Turn the engine on
        m = MessengerMiner(date=date, session=self._session, server=self._server)

        # Been there, done that
        # TODO Check the existence of a miner instance
        if False:
            self._print('{} has already been mined', date_string)
            del m

        else:
            # Go browse the web summary page for that day
            # and scrape off the jobs uuid request parameters.
            jobs = m.fetch_jobs()

            # I don't work on weekends
            if not jobs:
                self._print('No jobs found for {}', date_string)

            else:
                for j in jobs:
                    # Grab the job's web page, regex it and store
                    # the collected fields in a sensible manner.
                    # We don't pickle the data yet! Only upon exit.
                    soup = m.get_job(j)
                    raw_data = m.scrape_job(soup)
                    m.package_job(raw_data)

                    # We wanna see results!
                    pp = PrettyPrinter()
                    pp.pprint(m.raw_data)

                # Now do the book-keeping
                self._miners.add(m)

                self._print('Mined: {} successfully!', date_string)
                # If some fields failed to be scraped,
                # return some feedback about the context
                for message in m.debug_messages:
                    self._print(message)