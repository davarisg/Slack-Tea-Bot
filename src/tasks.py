from celery import Celery
from celery.schedules import crontab

from conf import CELERY_BROKER, CELERY_BACKEND
from models import Server, Customer, session, User
from slack_client import sc
from utils import post_message

celery = Celery('app', broker=CELERY_BROKER, backend=CELERY_BACKEND)
celery.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='UTC',
    CELERYBEAT_SCHEDULE={
        'update-slack-users': {
            'task': 'tasks.update_slack_users',
            'schedule': crontab(hour='*')
        }
    },
)


@celery.task
def brew_countdown():
    server = session.query(Server).filter_by(completed=False).first()
    server.completed = True
    customers = session.query(Customer).filter_by(server_id=server.id)
    session.commit()

    if not customers.count():
        return post_message('Time is up! Looks like no one else wants a cuppa.')

    return post_message("\n".join(
        ['Time is up!'] +
        ['%s wants %s' % (customer.user.real_name, customer.user.tea_type) for customer in customers]
    ))


@celery.task
def update_slack_users():
    """
    Periodic task to update slack user info
    """
    for member in sc.api_call('users.list')['members']:
        slack_id = member.get('id')
        username = member.get('name')
        email = member.get('profile').get('email', '')
        real_name = member.get('profile').get('real_name', '')
        first_name = member.get('profile').get('first_name', '')
        last_name = member.get('profile').get('last_name', '')
        deleted = member.get('profile').get('deleted')

        user = session.query(User).filter_by(slack_id=slack_id).first()
        if user:
            user.username = username
            user.email = email
            user.real_name = real_name
            user.first_name = first_name
            user.last_name = last_name
            user.deleted = deleted
        else:
            session.add(User(
                slack_id=slack_id,
                username=username,
                email=email,
                real_name=real_name,
                first_name=first_name,
                last_name=last_name,
                deleted=deleted
            ))

        session.commit()
