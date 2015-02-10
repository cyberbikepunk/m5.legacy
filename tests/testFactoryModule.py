""" Various unittest scripts for the factory module. """

from unittest import TestCase

from os import listdir, remove
from os.path import dirname, join
from datetime import date
from requests import Session
from bs4 import BeautifulSoup
from random import randint
from re import search

from m5.factory import Downloader


class TestFactoryModule(TestCase):

    def setUp(self):
        """  Log into the remote server. """

        self.url = 'http://bamboo-mec.de/ll.php5'

        test_dir = dirname(__file__)
        self.directory = join(test_dir, 'temp')

        credentials = {'username': 'm-134',
                       'password': 'PASSWORD'}

        self.session = Session()
        headers = {'user-agent': 'Mozilla/5.0'}
        self.session.headers.update(headers)

        response = self.session.post(self.url, credentials)
        if response.ok:
            print('Now logged in to %s.' % self.url)
        else:
            print('Failed to log in')
            exit(1)

    def tearDown(self):
        """  Logout. """

        # Say goodbye to the server
        url = 'http://bamboo-mec.de/index.php5'
        payload = {'logout': '1'}

        response = self.session.get(url, params=payload)

        if response.history[0].status_code == 302:
            # We have been redirected to the home page
            print('Logged out successfully. Goodbye!')

        self.session.close()

        # clean up the temp directory
        for file in listdir(self.directory):
            if search(self.day.strftime('%Y-%m-%d'), file):
                remove(join(self.directory, file))

    def testDownloader(self):
        """ Check if the Downloader class can download files correctly from the company server. """

        d = Downloader(self.session,
                       self.directory,
                       overwrite=True)

        random_day = randint(1, 28)
        random_month = randint(1, 12)
        self.day = date(2014, random_month, random_day)

        print('Testing file download for %s.' % str(self.day))
        soups = d.download(self.day)

        if not soups:
            # No jobs on that day... try again
            self.testDownloader()
        else:
            for soup in soups:
                self.assertIsInstance(soup.data, BeautifulSoup)
                self.assertIsInstance(soup.stamp.date, date)
                self.assertIsInstance(soup.stamp.uuid, str)

                order_detail = soup.data.find(id='order_detail')
                self.assertIsNotNone(order_detail)
