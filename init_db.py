from src.models import Base, engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
