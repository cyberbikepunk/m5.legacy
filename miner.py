import re
import subprocess
import requests
from datetime import datetime


class Miner:
    """
    The Miner class takes care of scraping the company server.
    """

    def __init__(self, date, session):
        self.date = date
        self.session = session
        self.date_string = date.strftime('%d.%m.%Y')
        self.url = 'http://bamboo-mec.de/ll.php5?' \
                   'status=delivered' \
                   '&datum={}' \
                   .format(self.date_string)
        self.raw_html = ''
        self.temp_file = self.date_string + '.html'

    def browse(self):
        subprocess.call(['firefox', self.temp_file])

    def download(self):
        response = self.session.get(self.url)
        f = open(self.temp_file, 'w')
        self.raw_html = response.text
        f.write(self.raw_html)
        self.browse()

    def scrape(self):
        pattern = 'uuid=(\d{7})'
        jobs = re.search(pattern, self.raw_html)
        if jobs:
            self.process()

    def process(self):
        pass

