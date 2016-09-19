from sqlalchemy.sql import ClauseElement

from conf import CHANNEL
from slack_client import sc


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


def post_message(text, channel, attachments=None, mrkdwn=False):
    sc.api_call(
        'chat.postMessage',
        channel=channel,
        text=text,
        icon_emoji=':tea:',
        username='Tea Bot',
        mrkdwn=mrkdwn,
        attachments=attachments
    )
