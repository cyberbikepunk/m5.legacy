""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""

from calendar import Calendar
from pprint import PrettyPrinter
from datetime import datetime
# from sqlite3 import IntegrityError
from sqlalchemy.exc import IntegrityError

from m5.user import User
from m5.factory import Miner, Processor
from m5.utilities import notify
from sqlalchemy.orm.exc import FlushError


u = User('m-134', 'PASSWORD')

calendar = Calendar()
dates = calendar.itermonthdates(2014, 11)
# dates = [datetime(2014, 12, 2)]

m = Miner(u.username, u.remote_server, u.remote_session)
p = Processor()
pp = PrettyPrinter()

for date in dates:
    raw_data = m.mine(date)
    bundle = p.process(raw_data)

    pp.pprint(bundle)

    # Order matters
    for tables in bundle:
        for table in tables:
            try:
                u.session.add(table)
                u.session.commit()
            except (IntegrityError, FlushError):
                notify('Database Intergrity ERROR: {}', str(table))
                u.session.rollback()