from models import session, User, Server, Customer


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


class CustomerManager(object):
    @classmethod
    def get_for_user_server(cls, user_id, server_id):
        return session.query(Customer).filter_by(user_id=user_id, server_id=server_id).first()
