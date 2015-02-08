""" This module defines our local database model. """

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.types import Integer, Float, String, Boolean, Enum, DateTime
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy import create_engine

from random import randint, choice, uniform
from uuid import uuid4


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

    type = Column(Enum('city_tour', 'overnight', 'help'))
    payed_cash = Column(Boolean)
    distance = Column(Float)

    client = relationship('Client', backref=backref('order'))

    @synonym_for('client_id')
    @property
    def id(self):
        return self.order_id

    def __repr__(self):
        return u'<Order(id: {0:s}, type: {1:s}, payed_cash: {2:s}, distance: {3:s})>'.format(
            str(self.id), self.type, str(self.payed_cash), str(self.distance))


class Checkin(Base):
    __tablename__ = 'checkin'

    checkin_id = Column(Integer, primary_key=True, autoincrement=False)
    order_id = Column(Integer, ForeignKey('order.order_id'))
    checkpoint_id = Column(Integer, ForeignKey('checkpoint.checkpoint_id'))

    purpose = Column(Enum('pickup', 'dropoff', 'begin', 'end'))

    order = relationship('Order', backref=backref('checkin'))
    checkpoint = relationship('Checkpoint', backref=backref('checkin'))

    @synonym_for('checkin_id')
    @property
    def id(self):
        return self.checkin_id


class Checkpoint(Base):
    __tablename__ = 'checkpoint'

    checkpoint_id = Column(String, primary_key=True, autoincrement=False)
    company = Column(String)

    @synonym_for('checkpoint_id')
    @property
    def id(self):
        return self.checkpoint_id


if __name__ == '__main__':
    engine = create_engine('sqlite:///test9.db', echo=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    clients = list()
    orders = list()
    checkpoints = list()
    checkins = list()

    checkpoint_ids = list()
    client_ids = list()
    order_ids = list()

    for i in range(10):
        client_ids.append(randint(1, 99999))
        clients.append(Client(client_id=client_ids[i],
                              name=str(uuid4())))

    for i in range(50):
        order_ids.append(randint(1, 9999999999))
        orders.append(Order(order_id=order_ids[i],
                            distance=uniform(0, 20),
                            payed_cash=choice([True, False]),
                            type=choice(['city_tour', 'overnight', 'help']),
                            client_id=choice(client_ids)))

    for i in range(10):
        checkpoint_ids.append(str(uuid4()))
        checkpoints.append(Checkpoint(checkpoint_id=checkpoint_ids[i],
                                      company=str(uuid4())))

    for i in range(100):
        checkins.append(Checkin(checkin_id=randint(1, 1000000),
                                purpose=choice(['pickup', 'dropoff', 'begin', 'end']),
                                order_id=choice(order_ids),
                                checkpoint_id=choice(checkpoint_ids)))

    session.add_all(clients)
    session.add_all(orders)
    session.add_all(checkpoints)
    session.add_all(checkins)

    session.commit()

