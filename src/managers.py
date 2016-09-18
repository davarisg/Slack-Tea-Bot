from models import User, Server
from models import session


class UserManager(object):
    @classmethod
    def get_by_slack_id(cls, slack_id):
        return session.query(User).filter_by(slack_id=slack_id).first()

    @classmethod
    def get_by_username(cls, username):
        return session.query(User).filter_by(slack_id=username).first()


class ServerManager(object):
    @classmethod
    def has_active_server(cls):
        return bool(session.query(Server).filter_by(completed=False).count())
