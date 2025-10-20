from backend.db.db import engine, SessionLocal
from backend.models import Base, DataSource


def setup_test_db():
    # create all tables
    Base.metadata.create_all(bind=engine)


def teardown_test_db():
    # drop all tables
    Base.metadata.drop_all(bind=engine)


setup_test_db()
