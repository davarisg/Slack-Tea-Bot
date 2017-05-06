[![Codeship status for Slack-Tea-Bot](https://codeship.com/projects/730b8b40-6278-0134-e9e6-0ae4dffb78c7/status?branch=master)](https://codeship.com/projects/175112)

# Slack Tea Bot

A tea bot for Slack.

## Available Commands ##

1. _register_ - Registers the tea preference of a user (`@teabot register green tea`)
2. _brew_ - Initiates the brewing process (users have 120 seconds to respond) and takes an optional argument to limit the number of cups to brew (`@teabot brew` or `@teabot brew 5`)
3. _me_ - Reply with `@teabot me` when someone has offered to brew
4. _leaderboard_ - Displays the current leaderboard based on tea cups brewed (`@teabot leaderboard`)
5. _stats_ - Displays the stats for all users (`@teabot stats`) or (`@teabot stats @george`) for a single user
6. _nominate_ - Nominate someone to brew tea. You must brew tea more than %s times to use this (`@teabot nominate @george`)
7. _update_users_ -> Update teabot's user registry based on changes in your Slack team (`@teabot update_users`)

![Teabot Preview](https://github.com/davarisg/Slack-Tea-Bot/blob/master/screenshots/teabot-preview.gif)


## How to run the app ##

* Go to Slack's App & Integrations > Manage > Custom Integrations and add a new Bot called teabot.
* Create a virtualenv and load it.
* On the repository's root type `pip install -r requirements.txt`.
* Export your slack secret key `export SLACK_WEBHOOK_SECRET="mysecretslackkey"`.
* Initialize the database `python init_db.py`. You can configure the path to the sqlite DB in [conf.py](src/conf.py).
* Start the app `python src/app.py`.


## How to run tests locally ##

* Load your virtualenv.
* Install test required pip packages `pip install -r requirements_test.txt`.
* From the repository's root type `python -m unittest discover`.
