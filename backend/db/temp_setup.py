from backend.db.db import engine
from backend.models import Base


def setup_test_db():
    # create all tables
    Base.metadata.create_all(bind=engine)


def teardown_test_db():
    # drop all tables
    Base.metadata.drop_all(bind=engine)


setup_test_db()
