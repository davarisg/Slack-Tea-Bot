from celery import Celery

from conf import CELERY_BROKER, CELERY_BACKEND
from models import Server, Customer, session
from utils import post_message

celery = Celery('app', broker=CELERY_BROKER, backend=CELERY_BACKEND)


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
