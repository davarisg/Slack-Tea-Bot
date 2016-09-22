from mock import patch

from src.app import Dispatcher
from src.conf import BREW_COUNTDOWN, NOMINATION_POINTS_REQUIRED
from src.managers import ServerManager, CustomerManager
from src.models import session, Customer, Server
from tests.utils import BaseTestCase


class DispatcherTestCase(BaseTestCase):
    def setUp(self):
        super(DispatcherTestCase, self).setUp()
        self.tea_bot = self._create_user(slack_id='U123456', username='teabot')
        self.dispatcher = Dispatcher(self.tea_bot)
        self.registered_user = self._create_user(tea_type='green tea')
        self.unregistered_user = self._create_user(first_name='George')

        self.patcher = patch('src.app.post_message')
        self.mock_post_message = self.patcher.start()

    def tearDown(self):
        super(DispatcherTestCase, self).tearDown()
        self.patcher.stop()

    def test_command_with_column(self):
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> ping',
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with('pong', 'tearoom')

        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456>: ping',
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with('pong', 'tearoom')

    def test_brew_unregistered(self):
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> brew',
            'user': self.unregistered_user.slack_id
        }])
        self.mock_post_message.assert_called_with('You need to register first.', 'tearoom')

    def test_brew(self):
        self.assertFalse(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> brew',
                'user': self.registered_user.slack_id
            }])
            mock_brew_countdown.apply_async.assert_called_with(countdown=BREW_COUNTDOWN, args=('tearoom',))
            self.assertTrue(ServerManager.has_active_server())

    def test_brew_with_active_server(self):
        self._create_server(self.registered_user.id)
        self.assertTrue(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> brew',
                'user': self.registered_user.slack_id
            }])
            mock_brew_countdown.apply_async.assert_not_called()
            self.mock_post_message.assert_called_with('Someone else is already making tea. Want in?', 'tearoom')
            self.assertTrue(ServerManager.has_active_server())

    def test_me(self):
        user = self._create_user(tea_type='mint tea')
        server = self._create_server(user.id)
        self.assertIsNone(CustomerManager.get_for_user_server(self.registered_user.id, server.id))
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> me',
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with(
            'Hang tight %s, tea is being served soon' % self.registered_user.first_name,
            'tearoom'
        )
        self.assertIsNotNone(CustomerManager.get_for_user_server(self.registered_user.id, server.id))

    def test_me_unregistered(self):
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> me',
            'user': self.unregistered_user.slack_id
        }])
        self.mock_post_message.assert_called_with('You need to register first.', 'tearoom')

    def test_me_without_server(self):
        self.assertEqual(session.query(Customer).filter_by(user_id=self.registered_user.id).count(), 0)
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> me',
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with(
            'No one has volunteered to make tea, why dont you make it %s?' % self.registered_user.first_name,
            'tearoom'
        )
        self.assertEqual(session.query(Customer).filter_by(user_id=self.registered_user.id).count(), 0)

    def test_me_as_server(self):
        server = self._create_server(self.registered_user.id)
        self.assertIsNone(CustomerManager.get_for_user_server(self.registered_user.id, server.id))
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> me',
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with(
            '%s you are making tea! :face_with_rolling_eyes:' % self.registered_user.first_name,
            'tearoom'
        )
        self.assertIsNone(CustomerManager.get_for_user_server(self.registered_user.id, server.id))

    def test_nominate(self):
        self.registered_user.nomination_points = NOMINATION_POINTS_REQUIRED
        self.registered_user1 = self._create_user(tea_type='abc')
        session.flush()
        session.commit()

        self.assertFalse(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> nominate <@%s>' % self.registered_user1.slack_id,
                'user': self.registered_user.slack_id
            }])
            self.mock_post_message.assert_any_call(
                '%s has nominated %s to make tea! Who wants in?' % (
                    self.registered_user.first_name,
                    self.registered_user1.first_name
                ),
                'tearoom'
            )
            self.assertEqual(
                session.query(Server).filter_by(
                    user_id=self.registered_user1.id,
                    completed=False
                ).count(),
                1
            )
            self.assertEqual(
                session.query(Customer).filter_by(
                    user_id=self.registered_user.id
                ).count(),
                1
            )
            mock_brew_countdown.apply_async.assert_called_with(countdown=BREW_COUNTDOWN, args=('tearoom',))

    def test_nominate_not_enough_points(self):
        self.registered_user1 = self._create_user(tea_type='abc')
        session.flush()
        session.commit()

        self.assertFalse(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> nominate <@%s>' % self.registered_user1.slack_id,
                'user': self.registered_user.slack_id
            }])
            self.mock_post_message.assert_any_call(
                'You can\'t nominate someone unless you brew tea %s times!' % NOMINATION_POINTS_REQUIRED,
                'tearoom'
            )
            self.assertEqual(
                session.query(Server).filter_by(
                    user_id=self.registered_user1.id,
                    completed=False
                ).count(),
                0
            )
            self.assertEqual(
                session.query(Customer).filter_by(
                    user_id=self.registered_user.id
                ).count(),
                0
            )
            mock_brew_countdown.apply_async.assert_not_called()

    def test_nominate_unregistered(self):
        self.assertFalse(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> nominate <@%s>' % self.registered_user.slack_id,
                'user': self.unregistered_user.slack_id
            }])
            self.mock_post_message.assert_called_with('You need to register first.', 'tearoom')
            self.assertEqual(
                session.query(Server).filter_by(
                    user_id=self.unregistered_user.id,
                    completed=False
                ).count(),
                0
            )
            self.assertEqual(
                session.query(Customer).filter_by(
                    user_id=self.registered_user.id
                ).count(),
                0
            )
            mock_brew_countdown.apply_async.assert_not_called()

    def test_nominate_with_server(self):
        self.registered_user1 = self._create_user(tea_type='abc')
        self._create_server(self.registered_user.id)

        self.assertTrue(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> nominate <@%s>' % self.registered_user1.slack_id,
                'user': self.registered_user.slack_id
            }])
            self.mock_post_message.assert_any_call(
                'Someone else is already making tea, I\'ll save your nomination for later :smile:',
                'tearoom'
            )
            self.assertEqual(
                session.query(Server).filter_by(
                    user_id=self.registered_user.id,
                    completed=False
                ).count(),
                1
            )
            self.assertEqual(
                session.query(Customer).filter_by(
                    user_id=self.registered_user1.id
                ).count(),
                0
            )
            mock_brew_countdown.apply_async.assert_not_called()

    def test_nominate_no_mention(self):
        self.registered_user1 = self._create_user(tea_type='abc')

        self.assertFalse(ServerManager.has_active_server())
        with patch('src.app.brew_countdown') as mock_brew_countdown:
            self.dispatcher.dispatch([{
                'channel': 'tearoom',
                'text': '<@U123456> nominate',
                'user': self.registered_user.slack_id
            }])
            self.mock_post_message.assert_any_call('You must nominate another user to brew!', 'tearoom')
            self.assertEqual(
                session.query(Server).filter_by(
                    user_id=self.registered_user1.id,
                    completed=False
                ).count(),
                0
            )
            self.assertEqual(
                session.query(Customer).filter_by(
                    user_id=self.registered_user.id
                ).count(),
                0
            )
            mock_brew_countdown.apply_async.assert_not_called()

    def test_stats(self):
        self.registered_user1 = self._create_user(
            tea_type='abc',
            teas_brewed=5,
            teas_drunk=2,
            teas_received=3,
            times_brewed=2
        )

        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> stats',
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with(
            '',
            'tearoom',
            attachments=[
                {
                    "fallback": "Teabot Stats",
                    "pretext": "",
                    "author_name": "%s" % self.registered_user.real_name,
                    "fields": [
                        {
                            "value": "Number of tea cups consumed -> 0\nNumber of tea cups brewed -> 0\nNumber of times you've brewed tea -> 0\nNumber of tea cups you were served -> 0",
                            "short": False
                        },
                    ]
                },
                {
                    "fallback": "Teabot Stats",
                    "pretext": "",
                    "author_name": "%s" % self.registered_user1.real_name,
                    "fields": [
                        {
                            "value": "Number of tea cups consumed -> 2\nNumber of tea cups brewed -> 5\nNumber of times you've brewed tea -> 2\nNumber of tea cups you were served -> 3",
                            "short": False
                        },
                    ]
                }
            ]
        )

    def test_stats_for_user(self):
        self.registered_user1 = self._create_user(
            tea_type='abc',
            teas_brewed=5,
            teas_drunk=2,
            teas_received=3,
            times_brewed=2
        )

        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> stats <@%s>' % self.registered_user1.slack_id,
            'user': self.registered_user.slack_id
        }])
        self.mock_post_message.assert_called_with(
            '',
            'tearoom',
            attachments=[
                {
                    "fallback": "Teabot Stats",
                    "pretext": "",
                    "author_name": "%s" % self.registered_user1.real_name,
                    "fields": [
                        {
                            "value": "Number of tea cups consumed -> 2\nNumber of tea cups brewed -> 5\nNumber of times you've brewed tea -> 2\nNumber of tea cups you were served -> 3",
                            "short": False
                        },
                    ]
                }
            ]
        )

    def test_register(self):
        self.assertIsNone(self.unregistered_user.tea_type)
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> register peppermint tea',
            'user': self.unregistered_user.slack_id
        }])

        session.refresh(self.unregistered_user)
        self.assertEqual(self.unregistered_user.tea_type, 'peppermint tea')
        self.mock_post_message.assert_called_with('Welcome to the tea party George', 'tearoom')

    def test_register_without_tea_type(self):
        self.assertIsNone(self.unregistered_user.tea_type)
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> register',
            'user': self.unregistered_user.slack_id
        }])

        session.refresh(self.unregistered_user)
        self.assertIsNone(self.unregistered_user.tea_type)
        self.mock_post_message.assert_called_with(
            'You didn\'t tell me what type of tea you like. Try typing `@teabot register green tea`',
            'tearoom'
        )

    def test_register_update_tea_type(self):
        self.assertEqual(self.registered_user.tea_type, 'green tea')
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> register peppermint tea',
            'user': self.registered_user.slack_id
        }])

        session.refresh(self.registered_user)
        self.assertEqual(self.registered_user.tea_type, 'peppermint tea')
        self.mock_post_message.assert_called_with('I have updated your tea preference.', 'tearoom')

    def test_did_not_understand(self):
        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': '<@U123456> unknown command',
            'user': self.registered_user.slack_id
        }])

        self.mock_post_message.assert_called_with('I did not understand that. Try `@teabot help`', 'tearoom')

        self.dispatcher.dispatch([{
            'channel': 'tearoom',
            'text': 'hey <@U123456>',
            'user': self.registered_user.slack_id
        }])

        self.mock_post_message.assert_called_with('I did not understand that. Try `@teabot help`', 'tearoom')
