from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, func, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from conf import SQLALCHEMY_ENGINE

engine = create_engine(SQLALCHEMY_ENGINE, echo=False)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    slack_id = Column(String(255), unique=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), nullable=True)
    real_name = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    deleted = Column(Boolean, default=False)

    tea_type = Column(String(1024))


class Server(Base):
    __tablename__ = 'server'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', foreign_keys=[user_id])
    completed = Column(Boolean, default=False)
    created = Column(DateTime, default=func.current_timestamp())


class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    server_id = Column(Integer, ForeignKey('server.id'))
    user = relationship('User', foreign_keys=[user_id])
    server = relationship('Server', foreign_keys=[server_id])
    created = Column(DateTime, default=func.current_timestamp())
