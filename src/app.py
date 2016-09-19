import random
import re
import time

from conf import BREW_COUNTDOWN, NOMINATION_POINTS_REQUIRED, HELP_TEXT
from managers import UserManager, ServerManager
from models import Server, Customer, session, User
from slack_client import sc
from tasks import brew_countdown
from utils import post_message

COMMAND_RE = re.compile(r'^<@([\w\d]+)> (register|brew|me|stats|leaderboard|nominate|yo|ping|help)?\s?(.*)$', flags=re.IGNORECASE)
TEABOT_MENTION_RE = re.compile(r'<@([\w\d]+)>')
MENTION_RE = re.compile(r'^<@([\w\d]+)>$')


# Decorator
def require_registration(func):
    def func_wrapper(self, *args, **kwargs):
        if not self.request_user.tea_type:
            return post_message('You need to register first.')
        else:
            return func(self, *args, **kwargs)
    return func_wrapper


class Listener(object):
    def __init__(self, teabot):
        self.teabot = teabot

    def listen(self):
        if sc.rtm_connect():
            while True:
                event = sc.rtm_read()
                if event and event[0].get('type', '') == 'message':
                    Dispatcher(self.teabot).dispatch(event)
                time.sleep(1)


class Dispatcher(object):
    def __init__(self, teabot):
        self.teabot = teabot
        self.command_body = ''
        self.request_user = None

    def dispatch(self, event):
        text = event[0].get('text', '')
        request_slack_user_id = event[0].get('user', '')
        try:
            slack_user_id, command, command_body = COMMAND_RE.search(text).groups()
            if slack_user_id != self.teabot.slack_id:
                return

            command = command.strip()
            self.command_body = command_body.strip()
            self.request_user = UserManager.get_by_slack_id(request_slack_user_id)

            # Call the appropriate function
            getattr(self, command)()
        except AttributeError:
            regex = TEABOT_MENTION_RE.search(text)
            if regex and regex.groups()[0] == self.teabot.slack_id:
                post_message('No idea what that means mate.')

    @require_registration
    def brew(self):
        # Make sure the user is not brewing already
        if ServerManager.has_active_server():
            return post_message('Someone else is already making tea. Want in?')

        session.add(Server(user_id=self.request_user.id))
        session.commit()
        brew_countdown.apply_async(countdown=BREW_COUNTDOWN)
        return post_message(random.choice(['%s is making tea, who is in?' % self.request_user.first_name, 'Who wants a cuppa?']))

    @staticmethod
    def help():
        return post_message(HELP_TEXT)

    @staticmethod
    def leaderboard():
        leaderboard = session.query(User).filter(User.tea_type.isnot(None)).order_by(User.teas_brewed.desc()).all()
        _message = '*Teabot Leaderboard*\n\n'
        for index, user in enumerate(leaderboard):
            _message += '%s. _%s_ has brewed *%s* cups of tea\n' % (index + 1, user.real_name, user.teas_brewed)

        return post_message(_message)

    @require_registration
    def me(self):
        server = session.query(Server).filter_by(completed=False)
        if not server.count():
            return post_message('No one has volunteered to make tea, why dont you make it %s?' % self.request_user.first_name)

        server = server.first()

        if session.query(Customer).filter_by(user_id=self.request_user.id, server_id=server.id).count():
            return post_message('You said it once already %s.' % self.request_user.first_name)

        session.add(Customer(user_id=self.request_user.id, server_id=server.id))
        session.commit()
        return post_message('Hang tight %s, tea is being served soon' % self.request_user.first_name)

    @require_registration
    def nominate(self):
        if ServerManager.has_active_server():
            return post_message('Someone else is already making tea, I\'ll save your nomination for later :smile:')

        try:
            slack_id = MENTION_RE.search(self.command_body).groups()[0]
        except AttributeError:
            return post_message('You must nominate another user to brew!')

        nominated_user = UserManager.get_by_slack_id(slack_id)
        if nominated_user.nomination_points < NOMINATION_POINTS_REQUIRED:
            return post_message('You can\'t nominate someone unless you brew tea %s times!' % NOMINATION_POINTS_REQUIRED)

        # Subtract nomination points from request user.
        nominated_user.nomination_points -= NOMINATION_POINTS_REQUIRED

        session.add(Server(user_id=nominated_user.id))
        session.commit()
        brew_countdown.apply_async(countdown=BREW_COUNTDOWN)

        return post_message('%s has nominated %s to make tea! Who wants in?' % (
            self.request_user.first_name,
            nominated_user.first_name
        ))

    @staticmethod
    def ping():
        return post_message('pong')

    def stats(self):
        """
        Get stats for user(s) - (# of teas drunk, # of teas brewed, # of times brewed, # of teas received)
        :param command_body: can either be empty (get stats for all users) or can reference a specific user
        """
        try:
            slack_id = MENTION_RE.search(self.command_body).groups()[0]
        except AttributeError:
            slack_id = None

        if slack_id:
            users = UserManager.get_by_slack_id(slack_id)
        else:
            users = session.query(User).filter(User.tea_type.isnot(None)).all()

        results = []

        for user in users:
            results.append({
                'author_name': user.real_name,
                'teas_drunk': user.teas_drunk,
                'teas_brewed': user.teas_brewed,
                'times_brewed': user.times_brewed,
                'teas_received': user.teas_received
            })

        return post_message('', attachments=[
            {
                "fallback": "Teabot Stats",
                "pretext": "",
                "author_name": "%s" % result['author_name'],
                "fields": [
                    {
                        "value": "Number of tea cups consumed -> %(teas_drunk)s\nNumber of tea cups brewed -> %(teas_brewed)s\nNumber of times you've brewed tea -> %(times_brewed)s\nNumber of tea cups you were served -> %(teas_received)s" % result,
                        "short": False
                    },
                ]
            }
            for result in results
        ])

    def register(self):
        if not self.command_body:
            return post_message('You didn\'t tell me what type of tea you like. Try typing `@teabot register green tea`')

        message = 'Welcome to the tea party %s' % self.request_user.first_name
        if self.request_user.tea_type:
            message = 'I have updated your tea preference.'

        self.request_user.tea_type = self.command_body
        session.commit()
        return post_message(message)

    @staticmethod
    def yo():
        return post_message('Sup?')


if __name__ == '__main__':
    Listener(UserManager.get_by_username('teabot')).listen()
