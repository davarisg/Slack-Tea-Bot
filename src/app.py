import random
import re
import time

from conf import BREW_COUNTDOWN, VERSION, NOMINATION_POINTS_REQUIRED
from decorators import require_registration
from managers import UserManager, ServerManager
from models import Server, Customer, session, User
from slack_client import sc
from tasks import brew_countdown
from utils import post_message

COMMAND_RE = re.compile(r'^<@([\w\d]+)> (register|brew|me|stats|leaderboard|nominate|yo|ping|help)?\s?(.*)$', flags=re.IGNORECASE)
TEABOT_MENTION_RE = re.compile(r'<@([\w\d]+)>')
MENTION_RE = re.compile(r'^<@([\w\d]+)>$')


def register(user, tea_type):
    if not tea_type:
        return post_message('You didn\'t tell me what type of tea you like. Try typing `@teabot register green tea`')

    message = 'Welcome to the tea party %s' % user.first_name
    if user.tea_type:
        message = 'I have updated your tea preference.'

    user.tea_type = tea_type
    session.commit()
    return post_message(message)


@require_registration
def brew(user):
    # Make sure the user is not brewing already
    if ServerManager.has_active_server():
        return post_message('Someone else is already making tea. Want in?')

    session.add(Server(user_id=user.id))
    session.commit()
    brew_countdown.apply_async(countdown=BREW_COUNTDOWN)
    return post_message(random.choice(['%s is making tea, who is in?' % user.first_name, 'Who wants a cuppa?']))


@require_registration
def me(user):
    server = session.query(Server).filter_by(completed=False)
    if not server.count():
        return post_message('No one has volunteered to make tea, why dont you make it %s?' % user.first_name)

    server = server.first()

    if session.query(Customer).filter_by(user_id=user.id, server_id=server.id).count():
        return post_message('You said it once already %s.' % user.first_name)

    session.add(Customer(user_id=user.id, server_id=server.id))
    session.commit()
    return post_message('Hang tight %s, tea is being served soon' % user.first_name)


def stats(command_body=None):
    """
    Get stats for user(s) - (# of teas drunk, # of teas brewed, # of times brewed, # of teas received)
    :param command_body: can either be empty (get stats for all users) or can reference a specific user
    """
    try:
        slack_id = MENTION_RE.search(command_body).groups()[0]
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


@require_registration
def nominate(user, command_body=None):
    if ServerManager.has_active_server():
        return post_message('Someone else is already making tea, I\'ll save your nomination for later :smile:')

    try:
        slack_id = MENTION_RE.search(command_body).groups()[0]
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

    return post_message('%s has nominated %s to make tea! Who wants in?' % (user.first_name, nominated_user.first_name))


def leaderboard():
    leaderboard = session.query(User).filter(User.tea_type.isnot(None)).order_by(User.teas_brewed.desc()).all()
    _message = '*Teabot Leaderboard*\n\n'
    for index, user in enumerate(leaderboard):
        _message += '%s. _%s_ has brewed *%s* cups of tea\n' % (index + 1, user.real_name, user.teas_brewed)

    return post_message(_message)


if __name__ == "__main__":
    if sc.rtm_connect():
        teabot = UserManager.get_by_username('teabot')
        while True:
            read = sc.rtm_read()
            if read and read[0].get('type', '') == 'message':
                text = read[0].get('text', '')
                request_slack_user_id = read[0].get('user', '')
                try:
                    slack_user_id, command, command_body = COMMAND_RE.search(text).groups()
                    if slack_user_id != teabot.slack_id:
                        continue

                    command_body = command_body.strip()
                    request_user = UserManager.get_by_slack_id(request_slack_user_id)

                    if command == 'register':
                        register(request_user, command_body)
                    elif command == 'brew':
                        brew(request_user)
                    elif command == 'me':
                        me(request_user)
                    elif command == 'stats':
                        stats(command_body)
                    elif command == 'nominate':
                        nominate(request_user, command_body)
                    elif command == 'leaderboard':
                        leaderboard()
                    elif command == 'help':
                        post_message('''
*TeaBot v%s Available Commands*

1. _register_ -> Registers the tea preference of a user (`@teabot register green tea`)
2. _brew_ -> Initiates the brewing process (users have %s seconds to respond) (`@teabot brew`)
3. _me_ -> Reply with `@teabot me` when someone has offered to brew
4. _leaderboard_ -> Displays the current leaderboard based on tea cups brewed (`@teabot leaderboard`)
5. _stats_ -> Displays the stats for all users (`@teabot stats`) or (`@teabot stats @george`) for a single user
6. _nominate_ -> Nominate someone to brew tea. You must brew tea more than %s times to use this (`@teabot nominate @george`)
                        ''' % (VERSION, BREW_COUNTDOWN, NOMINATION_POINTS_REQUIRED))
                    elif command == 'yo':
                        post_message('Sup?')
                    elif command == 'ping':
                        post_message('pong')
                except AttributeError:
                    regex = TEABOT_MENTION_RE.search(text)
                    if regex and regex.groups()[0] == teabot.slack_id:
                        post_message('No idea what that means mate.')
            time.sleep(1)
