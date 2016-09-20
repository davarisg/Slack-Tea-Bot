from __future__ import absolute_import

import uuid
from unittest import TestCase

from src.models import Base, User, session, engine


class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        Base.metadata.create_all(engine)

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        Base.metadata.drop_all(engine)

    @classmethod
    def _create_user(cls, slack_id=None, username=None, *args, **kwargs):
        user = User()
        if not slack_id:
            slack_id = 'U%s' % str(uuid.uuid4())[:6]
        user.slack_id = slack_id

        if not username:
            username = str(uuid.uuid4())[:10]
        user.username = username

        for key, value in kwargs.iteritems():
            setattr(user, key, value)

        session.add(user)
        session.flush()
        session.commit()
        return user
