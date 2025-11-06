from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import Timetable, Calendar, Service, Operator, FileImport
from sqlalchemy import text
from backend.commands.reset_datasource import reset_datasource

log = get_logger(__name__)


def reset_all():
    with SessionLocal() as db:
        timetable_count = db.query(Timetable).count()
        calendar_count = db.query(Calendar).count()
        service_count = db.query(Service).count()
        operator_count = db.query(Operator).count()
        file_import_count = db.query(FileImport).count()

        log.info(f"Deleting {timetable_count} Timetable rows")
        db.query(Timetable).delete()

        log.info(f"Deleting {calendar_count} Calendar rows")
        db.query(Calendar).delete()

        log.info(f"Deleting {service_count} Service rows")
        db.query(Service).delete()

        log.info(f"Deleting {operator_count} Operator rows")
        db.query(Operator).delete()

        log.info(f"Deleting {file_import_count} FileImport rows")
        db.query(FileImport).delete()

        db.commit()

        tables = [
            "timetable",
            "calendar",
            "service",
            "calendar_exception",
            "stop_time",
            "journey",
            "route_link",
            "service_stop_usage",
            "file_import",
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
