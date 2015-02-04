""" This module defines our local database model. """

from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.types import Integer, Float, String, Boolean, Enum, DateTime, Time
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy import create_engine

# We use the declarative way
# to construct our metadata
Base = declarative_base()

# There is a bidirectional many-to-many relationship
# between the order and checkpoint tables. We need
# an intermediate association table for this to work.
orders_to_checkpoints = Table('association',
                              Base.metadata,
                              Column('order_id', Integer, ForeignKey('checkpoint.checkpoint_id')),
                              Column('checkpoint_id', String, ForeignKey('order.order_id')))


class Client(Base):
    """ The client table. One client can place many orders. """

    __tablename__ = 'client'

    # We use the unique 5-digit client number as the primary key
    client_id = Column(Integer, primary_key=True, autoincrement=False)

    name = Column(String)

    # The client table has a one-to-many
    # relationship with the order table
    order_ids = Column(Integer, ForeignKey('order.order_id'))
    orders = relationship('Order', backref='order')

    @synonym_for('client_id')
    @property
    def id(self):
        """ Return a standard name for the primary key. """
        return self.client_id


class Order(Base):
    """ The order table. An order is related to a single client. """

    __tablename__ = 'order'

    # We use the unique 12-digit order number as the primary key
    order_id = Column(Integer, primary_key=True, autoincrement=False)

    type = Column(Enum('city_tour', 'overnight', 'timed'))
    payed_cash = Column(Boolean)
    distance = Column(Float)

    # The order table has a many-to-one
    # relationship with the client table
    client_id = Column(Integer, ForeignKey('client.client_id'))

    @synonym_for('order_id')
    @property
    def id(self):
        """ Return a standard name for the primary key. """
        return self.order_id


class Checkin(Base):
    """ The check-in table. A checkin is a timestamp linked to an address. """

    __tablename__ = 'checkin'

    # We use the check-in timestamp as the primary key
    checkin_id = Column(DateTime, primary_key=True, autoincrement=False)

    purpose = Column(Enum('pickup', 'dropoff', 'begin', 'end'))
    after = Column(Time)
    until = Column(Time)

    # The check-in table has a bidirectional many-to-one relationship with address table
    checkpoint_id = ForeignKey('checkpoint.checkpoint_id')

    @synonym_for('timestamp')
    @property
    def id(self):
        """ Return a standard name for the primary key. """
        return self.timestamp


class Checkpoint(Base):
    """ The checkpoint table. A checkpoint can be checked-in multiple times. """

    __tablename__ = 'checkpoint'

    # We use the unique string returned by the geo-coder as the primary key
    checkpoint_id = Column(String, primary_key=True, autoincrement=False)
    order_ids = Column(Integer, ForeignKey('order.order_id'))
    checkin_ids = Column(DateTime, ForeignKey('checkin.checkin_id'))

    company = Column(String)
    street_nb = Column(Integer)
    street_name = Column(String)
    postal_code = Column(Integer)
    city = Column(String)
    lat = Column(Float)
    lon = Column(Float)

    # The check-in has a bidirectional one-to-many relationship with address table...
    checkins = relationship('Checkin', backref='checkpoint')
    # ... and a bidirectional many-to-many relationship with the order table
    orders = relationship('Order', backref='checkpoints', secondary=orders_to_checkpoints)

    @synonym_for('checkpoint_id')
    @property
    def id(self):
        """ Return a standard name for the primary key. """
        return self.checkpoint_id


if __name__ == '__main__':
    # test the module

    engine = create_engine('sqlite:///:memory:', echo=True)

    Session = sessionmaker(bind=engine)
    session = Session()

    ci = Checkin(checkin_id=1, timestamp=datetime.now())
    cp = Checkpoint(id='the_id', street_and_nb='Kreuzstrasse 14', postal_code='13187', city='Berlin')
    od = Order(id=201412191780, distance=12.345, payesd_cash=False)
    cl = Client(id=23462, name='Mickey Mouse')

    session.add_all()

    print(ci)
    print(cp)
    print(od)
    print(cl)
