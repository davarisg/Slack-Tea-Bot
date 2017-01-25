from src.models import Base, engine
from src.tasks import update_slack_users

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
update_slack_users()
