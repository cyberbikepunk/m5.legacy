#!/usr/bin/python

from requests import get
from time import strptime, strftime, localtime
from datetime import date
import re
import subprocess

class Miner:

    USERNAME = 'm-134'
    PASSWORD = 'PASSWORD'
    DEFAULT_DATE = '19.12.2014'
    DATE_FORMAT = '%d.%m.%Y'
    URL_BASE = 'http://bamboo-mec.de'
    URL_SUFFIX = '/ll.php5'
    USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0'

    def __init__(self):
        self.created = localtime()
        self.date = None
        self.user = None
        self.saved = None
        self.session = None

        print('Miner object created!')
        self.show()

    def pick_day(self):
        self.date = strptime(self.DEFAULT_DATE, self.DATE_FORMAT)
        self.formated_date = strftime(self.DATE_FORMAT, self.date)

        print('Picked a day!')
        self.show()

    def show(self):
        print('    MINER OBJECT')
        print('    Created on:     ' + strftime(self.DATE_FORMAT, self.created))

        if self.user:
            print('    User:           ' + self.user['username'])

        if self.date:
            print('    Target day:     ' + self.formated_date)

        if self.session:
            print('    Target URL:     ' + self.logged.url)
            print('    HTTP repsonse:  ' + str(self.logged.status_code))

        if self.saved:
            print('    Saved to file:  ' + self.saved)

    def login(self):
        self.session = Session()
        self.session.headers.update({'user-agent': self.USER_AGENT})
        self.logged = post(self.URL_BASE + self.URL_SUFFIX, self.user)

        print('Logged in!')
        self.show()

    def save_to_file(self):
        try:
            self.filename = self.formated_date + '.html'
            f = open(self.filename, 'w')
            try:
                f.write(self.logged.text)
                self.saved = 'Saved to ' + self.filename
                print('Saved html to file!')
            finally:
                f.close()
        except IOError:
            self.saved = 'ERROR'
            print('Html not saved to file!')
            pass

        self.show()

    def view_in_browser(self):
        subprocess.call(['firefox', self.filename])

    def scan_homepage(self):
        fertig = re.search('(?P<Done>\d+) Fertig', self.logged.text)
        fertig_dic = fertig.groupdict()
        print(fertig_dic)
        print(fertig_dic['Done'])