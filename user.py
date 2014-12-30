#!/usr/bin/python

from requests import Session
from pickle import load, dump
from getpass import getpass
from os.path import isfile
from datetime import datetime

from miner import *


class User:
    """ The User class manages user information and activity. In short,
    it's the backbone of the program.
    """

    def __init__(self):
        """ Initialize all User class attributes. That's it. """
        self.username = ''
        self.password = ''
        self.is_authenticated = False
        self.is_active = True
        self.session = None
        self.miner = Miner()
        self.data = []
        self.log = []

    def credentials(self):
        """ Return the payload for the post request on the login page
        in the form of a dictionary, where keys are form input names
        and values are form input values.
        """
        return {'username': self.username,
                'password': self.password}

    def file(self):
        """ Return the relative path to the user data file. """
        return self.username + '.pkl'

    def authenticate(self):
        """ Prompt for user credentials and try logging onto the company
        server. Raise a flag when successfully logged in. We detect success
        by looking for the word 'erfolgreich' (success in german) in the
        html source code returned by the server. Is there a better way?
        """
        login_url = 'http://bamboo-mec.de/ll.php5'
        self.username = input('Enter username: ')
        self.password = getpass('Enter password: ')

        self.session = Session()
        response = self.session.post(login_url, self.credentials())

        if response.text.find('erfolgreich') > 0:
            self.is_authenticated = True
            self.rec('Hello {}, you are now logged in!', self.username)
        else:
            self.rec('Invalid username or password... try again!')

    def is_returning(self):
        """ Return True if the user is a returning one. This is the
        case if a matching user data file is found.
        """

        if isfile(self.file()):
            self.rec('Data file {} found! You are a returning user.', self.file())
            return True
        else:
            self.rec('Welcome {}! You are a newbie.', self.file())
            return False

    def save_data(self):
        """ Pickle the user data object to file. This is not
        best way to store large quantities of data but it will
        do for now.
        """
        f = open(self.file(), 'wb')
        dump(self, f, -1)  # Highest protocol
        f.close()
        self.rec('Current data saved to {}.', self.file())

    def load_data(self):
        """ Load the pickled user data object from the file.
        If there's a problem accessing or reading the file, let
        the program crash. A returning user MUST have access to
        its past data.
        """
        f = open(self.file(), 'rb')
        self.data = load(f)
        f.close()
        self.rec('Existing data loaded from {}.', self.file())

    def save_log(self):
        """ Append the all current log messages to file. """
        logfile = self.username + '.log'
        f = open(logfile, 'a')
        f.write('\n'.join(self.log) + '\n\n')
        f.close()
        self.rec('User log saved to {}', logfile)

    def rec(self, message, *args):
        """ Format a log message and append the user log.
        The same message is also sent to the screen.
        """
        message = message.format(*args)
        timestamp = '{:%Y-%m-%d %H:%M:%S %fms}'.format(datetime.now())
        with timestamp + ' | ' + message as entry:
            self.log.append(entry)
            print(entry)

    def disconnect(self):
        pass

    def prompt(self):
        command = input('Enter your command or type "help" or "quit":')
        self.rec('User command: ' + command)

