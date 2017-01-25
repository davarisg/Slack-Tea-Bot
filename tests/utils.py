from __future__ import absolute_import

import uuid
from unittest import TestCase

from src.models import Base, User, get_session, engine, Server, Customer


class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        Base.metadata.create_all(engine)
        self.session = get_session()

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        self.session.rollback()
        Base.metadata.drop_all(engine)

    @classmethod
    def _create_customer(cls, user_id, server_id):
        session = get_session()
        customer = Customer(user_id=user_id, server_id=server_id)
        session.add(customer)
        session.flush()
        session.commit()
        return customer

    @classmethod
    def _create_server(cls, user_id, completed=False):
        session = get_session()
        server = Server(user_id=user_id, completed=completed)
        session.add(server)
        session.flush()
        session.commit()
        return server

    @classmethod
    def _create_user(cls, slack_id=None, username=None, first_name=None, real_name=None, *args, **kwargs):
        session = get_session()
        user = User()
        if not slack_id:
            slack_id = 'U%s' % str(uuid.uuid4())[:6]
        user.slack_id = slack_id

        if not username:
            username = str(uuid.uuid4())[:10]
        user.username = username

        if not first_name:
            first_name = str(uuid.uuid4())[:8]
        user.first_name = first_name

        if not real_name:
            real_name = str(uuid.uuid4())[:8]
        user.real_name = real_name

        for key, value in kwargs.iteritems():
            setattr(user, key, value)

        session.add(user)
        session.flush()
        session.commit()
        return user
