from mock import patch

from src.models import session
from src.tasks import brew_countdown
from tests.utils import BaseTestCase


class TasksTestCase(BaseTestCase):
    def setUp(self):
        super(TasksTestCase, self).setUp()
        self.user = self._create_user(tea_type='green tea')

        self.patcher = patch('src.tasks.post_message')
        self.mock_post_message = self.patcher.start()

    def test_brew_countdown_without_customers(self):
        server = self._create_server(self.user.id)
        self.assertFalse(server.completed)

        brew_countdown('tearoom')
        session.refresh(server)
        self.assertTrue(server.completed)
        self.assertEqual(self.user.teas_drunk, 1)
        self.assertEqual(self.user.teas_received, 0)
        self.assertEqual(self.user.teas_brewed, 1)
        self.assertEqual(self.user.times_brewed, 1)
        self.assertEqual(self.user.nomination_points, 0)
        self.mock_post_message.assert_called_with('Time is up! Looks like no one else wants a cuppa.', 'tearoom')

    def test_brew_countdown_with_customer(self):
        server = self._create_server(self.user.id)
        user1 = self._create_user(tea_type='green tea')
        self._create_customer(user1.id, server.id)
        self.assertFalse(server.completed)

        brew_countdown('tearoom')
        session.refresh(server)
        self.assertTrue(server.completed)
        self.assertEqual(self.user.teas_drunk, 1)
        self.assertEqual(self.user.teas_received, 0)
        self.assertEqual(self.user.teas_brewed, 2)
        self.assertEqual(self.user.times_brewed, 1)
        self.assertEqual(self.user.nomination_points, 1)
        self.assertEqual(user1.teas_drunk, 1)
        self.assertEqual(user1.teas_received, 1)
        self.assertEqual(user1.teas_brewed, 0)
        self.assertEqual(user1.times_brewed, 0)
        self.assertEqual(user1.nomination_points, 0)
        self.mock_post_message.assert_called_with(
            'Time is up!\n%s wants %s' % (user1.first_name, user1.tea_type),
            'tearoom'
        )

    def tearDown(self):
        super(TasksTestCase, self).tearDown()
        self.patcher.stop()
