import os

SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

SQLALCHEMY_ENGINE = 'sqlite:////tmp/test.db'

CELERY_BROKER = 'redis://localhost:6379'
CELERY_BACKEND = 'redis://localhost:6379'

BREW_COUNTDOWN = 10

VERSION = '0.2'

CHANNEL = 'general'

NOMINATION_POINTS_REQUIRED = 15
