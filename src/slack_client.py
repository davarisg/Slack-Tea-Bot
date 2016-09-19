from __future__ import absolute_import
from slackclient import SlackClient

from src.conf import SLACK_WEBHOOK_SECRET

sc = SlackClient(SLACK_WEBHOOK_SECRET)
