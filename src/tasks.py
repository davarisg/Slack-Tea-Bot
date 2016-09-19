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

    for customer in customers:
        customer.user.teas_drunk += 1
        customer.user.teas_received += 1
        server.user.teas_brewed += 1

    server.user.teas_brewed += 1  # Account for server's tea
    server.user.teas_drunk += 1
    server.user.times_brewed += 1

    # There must be at least 1 customer to get a nomination point.
    if len(customers):
        server.user.nomination_points += 1

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


@celery.task
def update_user_stats():
    users = session.query(User).filter(User.tea_type.isnot(None)).all()

    for user in users:
        servers = session.query(Server).filter_by(user_id=user.id)
        customers = session.query(Customer).filter_by(user_id=user.id)

        user.teas_brewed = session.query(Customer).filter(
            Customer.server_id.in_([server.id for server in servers])
        ).count() + servers.count()
        user.teas_drunk = servers.count() + customers.count()
        user.teas_received = customers.count()
        user.times_brewed = servers.count()

    session.commit()
