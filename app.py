import os
import random
import re
import time
from sqlite3 import IntegrityError

from celery import Celery
from slackclient import SlackClient
from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Integer, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')
slack_client = SlackClient('EjV7K0o6LcTTGRSdNB2kw9tm')

COMMAND_RE = re.compile(r'^<@U2ATJ8BMJ> (register|brew|me|stats|yo|ping|help)?\s?(.*)$', flags=re.IGNORECASE)
MENTION_RE = re.compile(r'<@U2ATJ8BMJ>')

BREW_COUNTDOWN = 10

VERSION = '0.1'

engine = create_engine('sqlite:////tmp/test.db', echo=True)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

celery = Celery('app', broker='redis://localhost:6379', backend='redis://localhost:6379')


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    slack_id = Column(String(255), unique=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), nullable=True)
    real_name = Column(String(255), nullable=True)

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


def save_slack_users():
    for member in sc.api_call('users.list')['members']:
        session.add(User(
            slack_id=member.get('id'),
            username=member.get('name'),
            email=member.get('profile').get('email', ''),
            real_name=member.get('profile').get('real_name', ''),
        ))
        try:
            session.commit()
        except IntegrityError:
            pass


def register(slack_user_id, tea_type):
    if not tea_type:
        return post_message('You didn\'t tell me what type of tea you like. Try typing `@teabot register green tea`')

    user = session.query(User).filter_by(slack_id=slack_user_id).first()
    user.tea_type = tea_type
    session.commit()
    return post_message('Welcome to the tea party %s' % user.real_name)


def brew(slack_user_id):
    user = session.query(User).filter_by(slack_id=slack_user_id).first()
    # Make sure the user is not brewing already
    if session.query(Server).filter_by(completed=False).count():
        return post_message('Someone else is already making tea. Want in?')

    session.add(Server(user_id=user.id))
    session.commit()
    brew_countdown.apply_async(countdown=BREW_COUNTDOWN)
    return post_message(random.choice(['%s is making tea, who is in?' % user.real_name, 'Who wants a cuppa?']))


def me(slack_user_id):
    user = session.query(User).filter_by(slack_id=slack_user_id).first()
    server = session.query(Server).filter_by(completed=False)
    if not server.count():
        return post_message('No one has volunteered to make tea, why dont you make it %s?' % user.real_name)

    server = server.first()

    if session.query(Customer).filter_by(user_id=user.id, server_id=server.id).count():
        return post_message('You said it once already %s.' % user.real_name)

    session.add(Customer(user_id=user.id, server_id=server.id))
    session.commit()
    return post_message('Hang tight %s, tea is being served soon' % user.real_name)


@celery.task
def brew_countdown():
    server = session.query(Server).filter_by(completed=False).first()
    server.completed = True
    customers = session.query(Customer).filter_by(server_id=server.id)
    session.commit()

    if not customers.count():
        return post_message('Time is up! Looks like no one else wants a cuppa.')

    return post_message("\n".join(
        ['Time is up!'] +
        ['%s wants %s' % (customer.user.real_name, customer.user.tea_type) for customer in customers]
    ))


def post_message(text):
    sc.api_call('chat.postMessage', channel='ocado', text=text)


sc = SlackClient('xoxb-78936283732-6Oq4LiF3exiv91PkfVmX8Gln')


if __name__ == "__main__":
    if sc.rtm_connect():
        while True:
            read = sc.rtm_read()
            if read and read[0].get('type', '') == 'message':
                text = read[0].get('text', '')
                slack_user_id = read[0].get('user', '')
                try:
                    command, command_body = COMMAND_RE.search(text).groups()
                    if command == 'register':
                        register(slack_user_id, command_body)
                    elif command == 'brew':
                        brew(slack_user_id)
                    elif command == 'me':
                        me(slack_user_id)
                    elif command == 'stats':
                        post_message('Sorry, I don\'t know how to do that')
                    elif command == 'help':
                        post_message('''
*TeaBot v%s Available Commands*

1. _register_ -> Registers the tea preference of a user `@teabot register green tea`
2. _brew_ -> Initiates the brewing process (users have %s seconds to respond) `@teabot brew`
3. _me_ -> Reply with `@teabot me` when someone has offered to brew tea
4. _stats_ [FUTURE]
                        ''' % (VERSION, BREW_COUNTDOWN))
                    elif command == 'yo':
                        post_message('Sup?')
                    elif command == 'ping':
                        post_message('pong')
                except AttributeError:
                    if MENTION_RE.search(text):
                        post_message('No idea what this means mate.')
            time.sleep(1)
