from __future__ import absolute_import
from src.models import session, User, Server


class UserManager(object):
    @classmethod
    def get_by_slack_id(cls, slack_id):
        return session.query(User).filter_by(slack_id=slack_id).first()

    @classmethod
    def get_by_username(cls, username):
        return session.query(User).filter_by(username=username).first()


class ServerManager(object):
    @classmethod
    def has_active_server(cls):
        return bool(session.query(Server).filter_by(completed=False).count())
