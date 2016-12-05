import random

from sqlalchemy.sql import ClauseElement

from slack_client import sc
from giphy_client import giphy_client


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance, True


def post_message(text, channel, attachments=None, mrkdwn=False, gif_search_term=None):
    gif_url = None
    if gif_search_term:
        gif_url = random.choice(list(giphy_client.search(gif_search_term))).media_url

    if gif_url is not None:
        text += '\n\n%s' % gif_url

    sc.api_call(
        'chat.postMessage',
        channel=channel,
        text=text,
        icon_emoji=':tea:',
        username='Tea Bot',
        mrkdwn=mrkdwn,
        attachments=attachments
    )
