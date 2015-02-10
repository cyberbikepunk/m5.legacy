""" Various unittest scripts for the factory module. """

from unittest import TestCase

from datetime import date
from pprint import PrettyPrinter
from requests import Session

from m5.factory import Downloader


class TestFactory(TestCase):

    def setUp(self):
        """  Log into the remote server. """

        self.server = 'http://bamboo-mec.de/'
        self.username = 'm-134'

        path = 'll.php5'
        url = '%s%s' % (self.server, path)
        credentials = {'username': self.username,
                       'password': 'PASSWORD'}

        self.session = Session()
        headers = {'user-agent': 'Mozilla/5.0'}
        self.session.headers.update(headers)

        response = self.session.post(url, credentials)
        if response.ok:
            print('Now logged in to %s.' % self.server)
        else:
            print('Failed to log in')
            exit(1)

    def tearDown(self):
        """  Logout. """
        pass

    def testCalculation(self):
        """ Check if the Downloader class works OK. """

        pp = PrettyPrinter()

        d = Downloader(self.username,
                       self.server,
                       self.session,
                       overwrite=True)

        day = date(2014, 12, 19)
        soups = d.download(day)
        pp.pprint(soups)
