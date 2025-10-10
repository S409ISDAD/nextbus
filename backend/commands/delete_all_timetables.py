from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import (
    Timetable,
    TimetableToTTDataSource,
    Calendar,
    Service,
    Operator,
)
from sqlalchemy import text
from backend.commands.reset_datasource import reset_datasource

log = get_logger(__name__)


def reset_all():
    with SessionLocal() as db:
        timetable_count = db.query(Timetable).count()
        calendar_count = db.query(Calendar).count()
        service_count = db.query(Service).count()
        tttds_count = db.query(TimetableToTTDataSource).count()
        operator_count = db.query(Operator).count()

        log.info(f"Deleting {timetable_count} Timetable rows")
        log.info(f"Deleting {calendar_count} Calendar rows")
        log.info(f"Deleting {service_count} Service rows")
        log.info(f"Deleting {tttds_count} TimetableToTTDataSource rows")
        log.info(f"Deleting {operator_count} Operator rows")

        db.query(Timetable).delete()
        db.query(Calendar).delete()
        db.query(Service).delete()
        db.query(TimetableToTTDataSource).delete()
        db.query(Operator).delete()

        db.commit()

        tables = [
            "timetable",
            "calendar",
            "service",
            "calendar_exception",
            "stop_time",
            "journey",
            "timetable_data_source",
            "route_link",
            "service_stop_usage",
            "operator",
        ]

        for table in tables:
            seq_name = f"{table}_id_seq"
            try:
                db.execute(text(f'ALTER SEQUENCE "{seq_name}" RESTART WITH 1'))
            except Exception as e:
                log.error(f"Could not reset sequence {seq_name}: {e}")

        db.commit()


if __name__ == "__main__":
    setup_logging()
    reset_all()
    reset_datasource()
