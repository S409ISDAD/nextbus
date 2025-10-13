import factory
from datetime import date
from backend.models import Calendar, Service, Timetable, Journey
from backend.tests.db_session import TestingSessionLocal


class SQLAFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = TestingSessionLocal()
        sqlalchemy_session_persistence = "commit"


class CalendarFactory(SQLAFactory):
    class Meta:
        model = Calendar

    start_date = date(2025, 1, 1)
    monday = True
    tuesday = True
    wednesday = True
    thursday = True
    friday = True
    saturday = False
    sunday = False


class ServiceFactory(SQLAFactory):
    class Meta:
        model = Service

    line_name = factory.Sequence(lambda n: f"Line{n}")
    service_code = factory.Sequence(lambda n: f"SVC{n}")
    description = "Test Service"


class TimetableFactory(SQLAFactory):
    class Meta:
        model = Timetable

    service = factory.SubFactory(ServiceFactory)
    service_code = factory.LazyAttribute(lambda t: t.service.service_code)
    line_name = factory.LazyAttribute(lambda t: t.service.line_name)


class JourneyFactory(SQLAFactory):
    class Meta:
        model = Journey

    block_id = "DEF"
    sequence = factory.Sequence(lambda n: n + 1)
    start_time = "08:00"
    end_time = "09:00"
    calendar = factory.SubFactory(CalendarFactory)
    service = factory.SubFactory(ServiceFactory)
    timetable = factory.SubFactory(TimetableFactory)
