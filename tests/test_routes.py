from __future__ import absolute_import

from mock import patch

from src.app import Dispatcher
from src.models import session
from tests.utils import BaseTestCase


class DispatcherTestCase(BaseTestCase):
    def setUp(self):
        super(DispatcherTestCase, self).setUp()
        self.tea_bot = self._create_user(slack_id='U123456', username='teabot')
        self.dispatcher = Dispatcher(self.tea_bot)

        self.patcher = patch('src.app.post_message')
        self.mock_post_message = self.patcher.start()

    def tearDown(self):
        super(DispatcherTestCase, self).tearDown()
        self.patcher.stop()

    def test_register(self):
        unregistered_user = self._create_user(first_name='George')
        self.assertIsNone(unregistered_user.tea_type)
        self.dispatcher.dispatch([{'text': '<@U123456> register peppermint tea', 'user': unregistered_user.slack_id}])

        session.refresh(unregistered_user)
        self.assertEqual(unregistered_user.tea_type, 'peppermint tea')
        self.mock_post_message.assert_called_with('Welcome to the tea party George')

    def test_register_without_tea_type(self):
        unregistered_user = self._create_user(first_name='George')
        self.assertIsNone(unregistered_user.tea_type)
        self.dispatcher.dispatch([{'text': '<@U123456> register', 'user': unregistered_user.slack_id}])

        session.refresh(unregistered_user)
        self.assertIsNone(unregistered_user.tea_type)
        self.mock_post_message.assert_called_with('You didn\'t tell me what type of tea you like. Try typing `@teabot register green tea`')

    def test_register_update_tea_type(self):
        unregistered_user = self._create_user(first_name='George', tea_type='green tea')
        self.assertEqual(unregistered_user.tea_type, 'green tea')
        self.dispatcher.dispatch([{'text': '<@U123456> register peppermint tea', 'user': unregistered_user.slack_id}])

        session.refresh(unregistered_user)
        self.assertEqual(unregistered_user.tea_type, 'peppermint tea')
        self.mock_post_message.assert_called_with('I have updated your tea preference.')
