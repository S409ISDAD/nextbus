import pytest
from pytest_factoryboy import register
from sqlalchemy import create_engine
from backend.models import Base
from backend.tests.factories import (
    CalendarFactory,
    ServiceFactory,
    TimetableFactory,
    JourneyFactory,
)
from backend.tests.db_session import TEST_DATABASE_URL
from sqlalchemy.orm import sessionmaker


register(CalendarFactory)
register(ServiceFactory)
register(TimetableFactory)
register(JourneyFactory)


@pytest.fixture(scope="function")
def db_session():
    """
    Creates a temporary database session for testing purposes.
    """
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
