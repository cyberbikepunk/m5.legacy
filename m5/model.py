""" This module defines our local database model. """

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, Float, String, Boolean, Enum, DateTime, Unicode
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

from datetime import datetime

Base = declarative_base()
print('\nBase: %s' % Base)


class Client(Base):
    """
    One client can place mulitple orders. By extention it has many checkins and checkpoints.
    """

    __tablename__ = 'client'

    client_id = Column(Integer, primary_key=True)

    order_ids = Column(Integer, ForeignKey('order.id'))
    checkin_ids = Column(Integer, ForeignKey('checkin.id'))
    checkpoint_ids = Column(Unicode, ForeignKey('checkpoint.id'))

    client_nb = Column(Integer, info={'regex': r'.*(\d{5})$',
                                      'required': True,
                                      'fragment': 'client',
                                      'line_nb': 0})
    client_name = Column(String, info={'regex': r'Kunde:\s(.*)\s\|',
                                       'required': True,
                                       'fragment': 'client',
                                       'line_nb': 0})

    orders = relationship('Order')
    checkpoints = relationship('Checkpoint')
    checkins = relationship('Checkin')


class Order(Base):
    """
    Orders hold information about a job, like .
    Each order is related to an arbitrary number of checkpoints and checkins.
    """

    __tablename__ = 'order'

    order_id = Column(Integer, primary_key=True)

    checkin_ids = Column(Integer, ForeignKey('checkin.id'))
    checkpoint_ids = Column(Unicode, ForeignKey('checkpoint.id'))
    client_ids = Column(Integer, ForeignKey('client.id'))

    order_nb = Column(Integer, info={'regex': r'.*(\d{10})',
                                     'required': True,
                                     'fragment': 'header',
                                     'line_nb': 0})
    cash_payment = Column(Boolean, info={'regex': r'(BAR)',
                                         'required': False,
                                         'fragment': 'header',
                                         'line_nb': 0})
    distance = Column(Float, info={'regex': r'(\d{1,2},\d{3})\skm',
                                   'required': False,
                                   'fragment': 'itinerary',
                                   'line_nb': 0})

    overnight = Column(Boolean, default=False)
    logistics = Column(Boolean, default=False)

    order = relationship('Order')
    checkpoint = relationship('Checkpoint')


class Checkin(Base):
    """
    A checkin is a timestamp. There is no geographical dimension.
    Each checkin is related to one order and one checkpoint.
    """

    __tablename__ = 'checkin'

    checkin_id = Column(Integer, primary_key=True)
    order_ids = Column(Integer, ForeignKey('order.id'))
    checkpoint_ids = Column(Unicode, ForeignKey('checkpoint.id'))

    timestamp = Column(DateTime, info={'regex': r'ST:\s(\d{2}:\d{2})',
                                       'required': True,
                                       'fragment': 'address',
                                       'line_nb': -2})
    after = Column(DateTime, info={'regex': r'(?:.*)ab\s(\d{2}:\d{2})',
                                   'required': False,
                                   'fragment': 'address',
                                   'line_nb': 2})
    until = Column(DateTime, info={'regex': r'(?:.*)bis\s+(\d{2}:\d{2})',
                                   'required': False,
                                   'fragment': 'address',
                                   'line_nb': -3})
    purpose = Column(Enum('pickup', 'dropoff'), info={'regex': r'(?:\d{5})\s(.*)',
                                                      'required': True,
                                                      'fragment': 'address',
                                                      'line_nb': 3})
    overnight = Column(Boolean, default=False)
    logistics = Column(Boolean, default=False)

    order = relationship('Order')
    checkpoint = relationship('Checkpoint')

    def __repr__(self):
        return "<Checkin(%s, Order %s, Checkpoint: %s)>" % (self.timestamp, self.order_id, self.checkpoint_id)


class Checkpoint(Base):
    """
    A checkpoint is a geographical point. There is no time dimension.
    One checkpoint may be associated with mulitple orders and checkins.
    """

    __tablename__ = 'checkpoints'

    checkpoint_id = Column(Unicode, primary_key=True)
    order_ids = Column(Integer, ForeignKey('order.id'))
    checkin_ids = Column(Integer, ForeignKey('checkpoint.id'))

    company = Column(String, info={'regex': r'(.*)',
                                   'required': False,
                                   'fragment': 'address',
                                   'line_nb': 1})
    street_and_nb = Column(String, info={'regex': r'(.*)',
                                         'required': True,
                                         'fragment': 'address',
                                         'line_nb': 2})
    postal_code = Column(Integer, info={'regex': r'(\d{5})(?:.*)',
                                        'required': True,
                                        'fragment': 'address',
                                        'line_nb': 3})
    city = Column(String, default='Berlin', info={'regex': r'(?:\d{5})\s(.*)',
                                                  'required': False,
                                                  'fragment': 'address',
                                                  'line_nb': 3})
    lat = Column(Float, info={'unit': '°N'})
    lon = Column(Float, info={'unit': '°E'})

    nb = Column(Integer)
    street = Column(String)
    full_address = Column(String)

    orders = relationship('Order')
    checkins = relationship('Checkins')

    def __repr__(self):
        return "<Checkpoints(%s, %s %s)>" % (self.address, self.city, self.postal_code)

if __name__ == '__main__':
    # test the module

    engine = create_engine('sqlite:///:memory:', echo=True)
    print(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    print(Session)

    ci = Checkin(checkin_id=1, timestamp=datetime.now())
    cp = Checkpoint(checkpoint_id='the_id', street_and_nb='Kreuzstrasse 14', postal_code='13187', city='Berlin')
    session.add(cp)
    session.add(ci)

    print(ci.timestamp)
    print(cp.street_and_nb)
