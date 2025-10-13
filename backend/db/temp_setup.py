from backend.db.db import engine, SessionLocal
from backend.models import Base, DataSource


def setup_test_db():
    # create all tables for tests
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        ds = DataSource(name="Test DataSource", description="For testing purposes")
        db.add(ds)

        db.commit()


def teardown_test_db():
    # drop all tables after tests
    Base.metadata.drop_all(bind=engine)


setup_test_db()
