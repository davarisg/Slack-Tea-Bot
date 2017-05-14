from mock import patch

from src.tasks import _brew_countdown
from tests.utils import BaseTestCase


class TasksTestCase(BaseTestCase):
    def setUp(self):
        super(TasksTestCase, self).setUp()
        self.user = self._create_user(tea_type='green tea')

        self.brew_countdown_patcher = patch('src.tasks.time.sleep')
        self.brew_countdown_patcher.start()
        self.post_message_patcher = patch('src.tasks.post_message')
        self.mock_post_message = self.post_message_patcher.start()

    def test_brew_countdown_without_customers(self):
        server = self._create_server(self.user.id)
        self.assertFalse(server.completed)

        _brew_countdown('tearoom')
        self.session.refresh(server)
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

        _brew_countdown('tearoom')
        self.session.refresh(server)
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
            'Time is up!\n%s wants %s' % (user1.display_name, user1.tea_type),
            'tearoom'
        )

    def tearDown(self):
        super(TasksTestCase, self).tearDown()
        self.brew_countdown_patcher.stop()
        self.post_message_patcher.stop()
