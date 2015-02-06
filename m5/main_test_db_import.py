""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""

# from calendar import Calendar
# from pprint import PrettyPrinter
from datetime import datetime

from m5.user import User
from m5.factory import Miner, Processor

u = User('m-134', 'PASSWORD')

# calendar = Calendar()
# dates = calendar.itermonthdates(2014, 12)
dates = [datetime(2014, 12, 19)]

m = Miner(u.username, u.remote_server, u.remote_session)
p = Processor()

for date in dates:
    raw_data = m.mine(date)
    tables = p.process(raw_data)

    # Order matters
    for table in tables:
        u.db.commit_all(table)
