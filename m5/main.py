""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""
from calendar import Calendar
from pprint import PrettyPrinter

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from m5.user import User
from m5.miner import Miner


engine = create_engine('sqlite:///test9.db', echo=True)
Base = declarative_base()
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

calendar = Calendar()
dates = calendar.itermonthdates(2014, 12)

u = User('m-134', 'PASSWORD')
for date in dates:
    m = Miner(date, u.server, u.session)
    m.mine()

    client, order, checkins, checkouts = m.process()

