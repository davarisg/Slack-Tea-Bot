import os

SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

SQLALCHEMY_ENGINE = 'sqlite:////tmp/test.db'

CELERY_BROKER = 'redis://localhost:6379'
CELERY_BACKEND = 'redis://localhost:6379'

BREW_COUNTDOWN = 120

VERSION = '0.2'

CHANNEL = 'general'

NOMINATION_POINTS_REQUIRED = 15

HELP_TEXT = '''
*TeaBot v%s Available Commands*

1. _register_ -> Registers the tea preference of a user (`@teabot register green tea`)
2. _brew_ -> Initiates the brewing process (users have %s seconds to respond) (`@teabot brew`)
3. _me_ -> Reply with `@teabot me` when someone has offered to brew
4. _leaderboard_ -> Displays the current leaderboard based on tea cups brewed (`@teabot leaderboard`)
5. _stats_ -> Displays the stats for all users (`@teabot stats`) or (`@teabot stats @george`) for a single user
6. _nominate_ -> Nominate someone to brew tea. You must brew tea more than %s times to use this (`@teabot nominate @george`)
''' % (VERSION, BREW_COUNTDOWN, NOMINATION_POINTS_REQUIRED)
