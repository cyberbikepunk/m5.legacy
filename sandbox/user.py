""" User related classes. """


from pickle import load, dump
from os.path import isfile
from datetime import datetime
from pprint import PrettyPrinter
from requests import Request, Session
from getpass import getpass


from m5.factory import Scraper


def _safe_request(session, request):
    """ Handle http request exceptions properly

    :param session: Session object
    :param request: Request object
    :return: Reponse object
    """

    # TODO error handling
    return session.send(request.prepare(), timeout=10.0)


class Messenger:
    """
    The User class manages user activity for couriers freelancing
    for User (http://messenger.de). This is the default user class.
    It could be extended to other courier companies.

    Public methods (API):
        - mine('dd.mm.yyyy'): mine one day of data
        - save(): save user data
        - quit(): save, disconnect and exit
        - more to come...
    """

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

        # Data that has already been mined is stored locally
        self._userdata = '../users/{}.pkl'.format(self._username)
        self._userlog = '../users/{}.log'.format(self._username)

        # Go and fetch it
        if self._is_returning:
            self._load_data()

    @property
    def _is_returning(self) -> bool:
        """ True if the user has local data. """

        if isfile(self._userdata):
            self._rec('You are a returning user.')
            return True
        else:
            self._rec('You are a new user.')
            return False

    def _authenticate(self, username='', password=''):
        """ Make login attempts until successful. """

        if not username:
            self._username = input('Enter username:')
        if not password:
            self._password = getpass('Enter password:')

        login_url = self._server + 'll.php5'
        credentials = {'username': self._username, 'password': self._password}
        request = Request('post', login_url, params=credentials)

        self._session = Session()
        # Pretend we're browsing
        headers = {'user-agent': 'Mozilla/5.0'}
        self._session.headers.update(headers)

        # Make a login attempt
        response = _safe_request(self._session, request)
        if not response.ok:
            self._authenticate()
        else:
            self._rec('Welcome {}! You are logged in.', self._username)

    def _load_data(self):
        """ Load pickled user data from local file. """

        # We don't forgive file exceptions because we absolutely need access
        # to past data. The idea is: if we can't open the file, die!
        with open(self._userdata, 'rb') as f:
            self.data = load(f)
            self._rec('Existing data loaded from {}.', self._userdata)

    def save_data(self):
        """ Pickle the user data to file. Yep, that our database! """

        with open(self._userdata, 'wb') as f:
            # Pickle with the highest protocol.
            dump(self, f, -1)
            self._rec('Current data saved to {}.', self._userdata)

    def save_log(self):
        """ Append all current log messages to user log file. """

        with open(self._userlog, 'a') as f:
            f.write('\n'.join(self._log) + '\n\n')
            self._rec('User log saved to {}', self._userlog)

        # Now do the book-keeping
        self.mined.add(date)

    def _rec(self, message: str, *args):
        """ Write to user log and print to screen.

        :param message: The log message may contain curly formatters
        :param *args: The formatter arguments
        """

        # First timestamp the message
        message = message.format(*args)
        timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
        entry = timestamp + ' | ' + message

        # The send it both ways: to screen and file
        self._log.append(entry)
        print(entry)

    def logout(self):
        """ Logout from the server. """

        # TODO Maybe I should also close the session?
        url = self._server + 'index.php5'
        payload = {'logout': '1'}
        response = self._session.get(url, params=payload)

        # Last words before we exit the program
        if response.status == 302:
            self._rec('Successfully logged out. Goodbye!')

    def prompt(self, input_string: str=None):
        """ Prompt the user for a method call.

        Usage:
            - mine('dd.mm.yyy')
        """

        if not input_string:
            input_string = input('Enter "public_method(...)" or "quit()":')
        try:
            exec('self.' + input_string)
        except (SyntaxError, ValueError, TypeError):
            self.prompt()

        # Better be safe than sorry
        # TODO make a clean exit on interrupt

    def quit(self):
        """ Make a clean exit from the program """
        self.save_data()
        self.save_log()
        self.logout()


    def prompt_date(self) -> datetime:
        """ Prompt on the console for 'quit' or a date in the format 'dd.mm.yyyy'. """

        # TODO Replace me later with a web frontend interface
        input_string = '18.12.2014'  # input('Enter a date or type "quit":')

        # This way to the exit ->
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

    def mine(self, date: datetime):
        """ If that date hasn't been scraped before, scrape it! """
        date_string = date.strftime('%d-%m-%Y')
        # Switch on the engine
        m = Scraper(date=date, session=self._session, server=self._server)

        # Been there, done that
        if date in self._miners:
            self._rec('{} has already been mined', date_string)
            m.close()

        else:
            # Go browse the web summary page for that day
            # and scrape off the job uuid request parameters.
            jobs = m.scrape_uuids()

            # I don't work on weekends
            if not jobs:
                self._rec('No jobs found for {}', date_string)

            else:
                for j in jobs:
                    # Grab the job's web page, regex it and store
                    # the collected fields in a sensible manner.
                    # We don't pickle the data yet: instead, we
                    # pickle multiple days at once before exit.
                    soup = m._get_job(j)
                    raw_data = m._scrape_job(soup)
                    m.process_job(raw_data)

                    # So wanna see results?
                    pp = PrettyPrinter()
                    pp.pprint(m.raw_data[0])                    # Job details
                    pp.pprint(m.raw_data[1])                    # Price table
                    [pp.pprint(d) for d in m.raw_data[2]]       # Addresses



                # We're never gonna scrape with a 100% success
                # rate, but let's do better next time!
                # TODO Hopefully remove this debug message later
                self._rec('Mined: {} successfully!', date_string)
                for message in m._warnings:
                    self._rec(message)