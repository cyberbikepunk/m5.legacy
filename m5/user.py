from requests import Session, Request
from pickle import load, dump
from os.path import isfile
from datetime import datetime
from pprint import PrettyPrinter
from getpass import getpass

from m5.miner import Miner


def date_string(date):
    """ :return: (str) A pretty date. """
    return date.strftime('%d-%m-%Y')


class Messenger:
    """ The Messenger class methods manage user information and activity. """

    def __init__(self, username='', password=''):
        """  Authenticate the user and fetch local data if any. """

        self._username = username
        self._password = password
        self._session = None
        self._miners = []
        self.data = []
        self._log = []

        # The remote server where the data is stored:
        self._server = 'http://bamboo-mec.de/'
        self._authenticate(self._username, self._password)

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
            self._rec('Welcome {}! You are logged in.', self._username)

    @property
    def _userlog(self):
        """ :return: (str) The relative path to the user log file. Here will do. """
        return self._username + '.log'

    @property
    def _userdata(self):
        """ :return: (str) The relative path to the user data file. """
        return self._username + '.pkl'

    @property
    def is_returning(self):
        """ :return: (bool) True if we find out the user's already got a data file. """

        if isfile(self._userdata):
            self._rec('Data file {} found! You are a returning user.', self._userdata)
            return True
        else:
            self._rec('Welcome {}! You are a newbie.', self._username)
            return False

    def load_data(self):
        """ Load pickled user data from file. """

        # We don't forgive file exceptions because we absolutely need access to past data.
        # If we can't access it, let the program crash. Don't muddle up new data with old data.
        with open(self._userdata, 'rb') as f:
            self.data = load(f)
            self._rec('Existing data loaded from {}.', self._userdata)

    def save_data(self):
        """ Pickle the user data to file. Yep, that our database! """

        with open(self._userdata, 'wb') as f:
            # Pickle with the highest protocol. Whatever that is...
            dump(self, f, -1)
            self._rec('Current data saved to {}.', self._userdata)

    def save_log(self):
        """ Append all current log messages to user log file. """

        with open(self._userlog, 'a') as f:
            f.write('\n'.join(self._log) + '\n\n')
            self._rec('Messenger log saved to {}', self._userlog)

    def _rec(self, message, *args):
        """ Write to user log and print to screen.

        :param message: (str) Log message strings with positional curly brackets
        :param *args: (str) Whatever arguments we want to insert
        """

        # Make sure the log message is unambiguous
        message = message.format (*args)
        timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
        entry = timestamp + ' | ' + message

        # Send it both ways: screen and file
        self._log.append(entry)
        print(entry)

    def logout(self):
        """ Logout from the server. """

        # TODO Maybe I should also close the session?
        url = self._server + 'index.php5'
        payload = {'logout': '1'}
        response = self._session.get(url, params=payload)

        # Last words before we exit
        if response.status == 302:
            self._rec('Successfully logged out. Goodbye!')

    def prompt_date(self):
        """ Prompt for 'quit' or a date in the format 'dd.mm.yyyy'.

        :return: (datetime obj)
        """

        # TODO Replace me later with a web frontend interface
        input_string = '19.12.2014'  # input('Enter a date or type "quit":')

        # This way towards the exit ->
        if input_string == 'quit':
            self.is_active = False

        else:
            try:
                day = datetime.strptime(input_string, '%d.%m.%Y')
            except ValueError:
                # If the date cannot be read, prompt again!
                print('Input format must be dd-mm-yy. Try again...')
                self.prompt_date()
            else:
                return day

    def mine(self, date):
        """ If that date hasn't received the treatment before, scrape it! """

        # Switch on the engine
        m = Miner(date=date, session=self._session, server=self._server)

        # Been there, done that
        if date in self.mined:
            self._rec('{} has already been mined', date_string(date))

        else:
            # Go browse the web summary page for that day
            # and scrape off the jobs uuid request parameters.
            jobs = m.fetch_jobs()

            # I don't work on weekends
            if not jobs:
                self._rec('No jobs found for {}', date_string(date))

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
                    pp.pprint(m.raw_data[0])                    # Job details
                    pp.pprint(m.raw_data[1])                    # Price table
                    [pp.pprint(d) for d in m.raw_data[2]]       # Addresses

                # Now do the book-keeping
                self.mined.add(date)

                # TODO We're never gonna scrape with a 100% success rate, but let's do better next time!
                self._rec('Mined: {} successfully!', date_string(date))
                for message in m.debug_messages:
                    self._rec(message)

