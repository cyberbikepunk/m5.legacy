""" Small scripts using the m5 module API. """

from m5.user import User
from m5.factory import Downloader
from datetime import date, timedelta


def bulk_download():

    u = User('m-134', 'PASSWORD')
    d = Downloader(u.remote_session, u.downloads)

    start = date(2014, 12, 1)
    end = date(2014, 12, 12)
    delta = end - start

    for n in range(delta.days):
        day = start + timedelta(days=n)
        d.download(day)


if __name__ == '__main__':
    bulk_download()
