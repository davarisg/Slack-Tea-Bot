import os

SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

SQLALCHEMY_ENGINE = 'sqlite:////tmp/test.db'

BREW_COUNTDOWN = 120

VERSION = '0.2'

NOMINATION_POINTS_REQUIRED = 15

HELP_TEXT = '''
*TeaBot v%s Available Commands*

1. _register_ -> Registers the tea preference of a user (`@teabot register green tea`)
2. _brew_ - Initiates the brewing process (users have %s seconds to respond) and takes an optional argument to limit the number of cups to brew (`@teabot brew` or `@teabot brew 5`)
3. _me_ -> Reply with `@teabot me` when someone has offered to brew
4. _leaderboard_ -> Displays the current leaderboard based on tea cups brewed (`@teabot leaderboard`)
5. _stats_ -> Displays the stats for all users (`@teabot stats`) or (`@teabot stats @george`) for a single user
6. _nominate_ -> Nominate someone to brew tea. You must brew tea more than %s times to use this (`@teabot nominate @george`)
7. _update_users_ -> Update teabot's user registry based on changes in your Slack team (`@teabot update_users`)
''' % (VERSION, BREW_COUNTDOWN, NOMINATION_POINTS_REQUIRED)
