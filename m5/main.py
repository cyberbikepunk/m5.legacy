""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""

from calendar import Calendar
# from pprint import PrettyPrinter

from m5.user import User
from m5.factory import Miner

calendar = Calendar()
dates = calendar.itermonthdates(2014, 12)

u = User('m-134', 'PASSWORD')

for date in dates:
    m = Miner(date, u.remote_server, u.remote_session)
    m.mine()
    m.process()

    u.session.commit(m.clients)
    u.session.commit(m.orders)
    u.session.commit(m.checkins)
    u.session.commit(m.checkpoints)