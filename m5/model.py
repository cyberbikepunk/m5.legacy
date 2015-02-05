""" This module defines our local database model. """

from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.types import Integer, Float, String, Boolean, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, synonym_for


Base = declarative_base()


class Client(Base):
    __tablename__ = 'client'

    client_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)

    @synonym_for('client_id')
    @property
    def id(self):
        return self.client_id


class Order(Base):
    __tablename__ = 'order'

    order_id = Column(Integer, primary_key=True, autoincrement=False)

    client_id = Column(Integer, ForeignKey('client.client_id'))
    client = relationship('Client', backref=backref('order'))

    type = Column(Enum('city_tour', 'overnight', 'help'))
    payed_cash = Column(Boolean)
    city_tour = Column(Float)
    overnight = Column(Float)
    waiting_time = Column(Float)
    extra_stops = Column(Float)
    fax_confirm = Column(Float)
    distance = Column(Float)

    @synonym_for('client_id')
    @property
    def id(self):
        return self.order_id


class Checkin(Base):
    __tablename__ = 'checkin'

    checkin_id = Column(Integer, primary_key=True, autoincrement=False)

    checkpoint_id = Column(Integer, ForeignKey('checkpoint.checkpoint_id'))
    checkpoint = relationship('Checkpoint', backref=backref('checkin'))

    order_id = Column(Integer, ForeignKey('order.order_id'))
    order = relationship('Order', backref=backref('checkin'))

    purpose = Column(Enum('pickup', 'dropoff'))
    after = Column(DateTime)
    until = Column(DateTime)

    @synonym_for('checkin_id')
    @property
    def id(self):
        return self.checkin_id


class Checkpoint(Base):
    __tablename__ = 'checkpoint'

    checkpoint_id = Column(String, primary_key=True, autoincrement=False)

    company = Column(String)
    street_name = Column(String)
    street_nb = Column(String)


    @synonym_for('checkpoint_id')
    @property
    def id(self):
        return self.checkpoint_id

