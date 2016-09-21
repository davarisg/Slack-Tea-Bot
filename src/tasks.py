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
            'schedule': crontab(hour='*', minute=0)
        }
    },
)


@celery.task
def brew_countdown(channel):
    server = session.query(Server).filter_by(completed=False).first()
    if not server:
        return

    server.completed = True
    customers = session.query(Customer).filter_by(server_id=server.id)

    for customer in customers.all():
        customer.user.teas_drunk += 1
        customer.user.teas_received += 1
        server.user.teas_brewed += 1

    server.user.teas_brewed += 1  # Account for server's tea
    server.user.teas_drunk += 1
    server.user.times_brewed += 1

    if not customers.count():
        session.commit()
        return post_message('Time is up! Looks like no one else wants a cuppa.', channel)

    # There must be at least 1 customer to get a nomination point.
    server.user.nomination_points += 1
    session.commit()

    return post_message("\n".join(
        ['Time is up!'] +
        ['%s wants %s' % (customer.user.first_name, customer.user.tea_type) for customer in customers]
    ), channel)


@celery.task
def update_slack_users():
    """
    Periodic task to update slack user info
    """
    slack_users = sc.api_call('users.list')
    if not slack_users['ok']:
        return

    for member in slack_users['members']:
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
