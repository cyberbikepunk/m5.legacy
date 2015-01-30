""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""

from pprint import PrettyPrinter

from m5.user import User
from datetime import datetime

pp = PrettyPrinter()

u = User('m-134', 'PASSWORD')


# Pick a date
date = datetime(2014, 12, 19)


# Play with the API
u.db.checkins = list(range(1000))
u.db.save('checkins')
u.db.checkins = list(range(100))
pp.pprint(u.db.checkins)
u.db.save('checkins')
u.db.load('checkins')
pp.pprint(u)
