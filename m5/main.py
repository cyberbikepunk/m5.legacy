""" Small scripts using the m5 module API. """

from m5.user import User
from m5.factory import Miner, Scraper
from datetime import date, timedelta
from pprint import PrettyPrinter


def bulk_download():

    u = User('m-134', 'PASSWORD')
    d = Miner(u.remote_session, u.username)

    start = date(2013, 3, 1)
    end = date(2014, 12, 24)
    delta = end - start

    soups = list()
    for n in range(delta.days):
        day = start + timedelta(days=n)
        soup = d.download(day)
        soups.append(soup)

    return soups


def bulk_scrape():

    s = Scraper()
    pp = PrettyPrinter()

    soups = bulk_download()
    serial = s.scrape(soups)
    pp.pprint(serial)


if __name__ == '__main__':
    bulk_download()
