""" A main script for the m5 module

This script is intended for my private use while I'm developing.
The idea is to log myself onto the company server and let me play
with the module API. Once I'm happy, I'll write a web interface.
"""

from pprint import PrettyPrinter
from datetime import datetime

from m5.user import User
from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
from sandbox.database import Database


u = User('m-134', 'PASSWORD')

model = Model()
db = Database(u.username)

engine = create_engine('sqlite:///:memory:', echo=True)

if not db.exists:
    db.install()

engine = create_engine("sqlite:///mydatabase.db")

# produce our own MetaData object
metadata = MetaData()

# we can reflect it ourselves from a database, using options
# such as 'only' to limit what tables we look at...
metadata.reflect(engine, only=['user', 'address'])


            )

# we can then produce a set of mappings from this MetaData.
Base = automap_base(metadata=metadata)

# calling prepare() just sets up mapped classes and relationships.
Base.prepare()

# mapped classes are ready
User, Address, Order = Base.classes.user, Base.classes.address,        Base.classes.user_order