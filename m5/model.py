""" This module holds the database model """

from sqlalchemy import Table, Column, ForeignKey, ColumnDefault
from sqlalchemy.types import Integer, Float, String, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.dialects.sqlite import

Base = declarative_base()


def initilialize(metadata):

    Table('checkpoints', metadata,
          Column('company', String, default=None),
          Column('address', String, default=None),
          Column('city', String, default=None),
          Column('postal_code', Integer, default=None),
          Column('lat', Float, default=None),
          Column('lon', Float), default=None)

    Table('orders', metadata,
          Column('id', Integer, primary_key=True),
          Column('checkpoint_id', ForeignKey('checkpoints.id')),
          Column('distance', Float, default=0),
          Column('cash_payment', Boolean, default=False))

    Table('checkins', metadata,
          Column('id', Integer, primary_key=True),
          Column('checkpoint_id', ForeignKey('checkpoints.id')),
          Column('order_id', Float, default=0),
          Column('drop_off', Boolean, default=None),
          Column('pickup', Boolean, default=None),
          Column('timestamp', DateTime, default=None),
          Column('after', DateTime, default=None),
          Column('until', Boolean, default=None),
          Column('purpose', String, default=None))

    Table('blueprints', metadata,
          Column('line_number', Integer),
          Column('regex'),
          Column('tag', String),
          Column('optional'))

    Table('tag', metadata,
          Column('name', String),
          Column('attrs', String))

    Table('sometable', metadata, Column('id', Integer, primary_key=True), sqlite_autoincrement=True)


class Checkpoints(Base):
    """ Checkpoints are a geographical point. They have no time dimension.
    """

    __tablename__ = 'checkpoints'

    Column('checkpoint_id', Integer, primary_key=True),
    Column('order_id', ForeignKey('orders.id')),


    children = relationship('Child')


class Orders(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent.id'))

from sqlalchemy.engine import Engine
from sqlalchemy import event



@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

