from slackclient import SlackClient

from conf import SLACK_WEBHOOK_SECRET

sc = SlackClient(SLACK_WEBHOOK_SECRET)
