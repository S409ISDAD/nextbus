from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import DataSourceVersion

log = get_logger(__name__)


def reset_datasource():
    with SessionLocal() as db:
        datasources = db.query(DataSourceVersion).all()
        for ds in datasources:
            ds.last_modified = None
            ds.etag = None
            db.add(ds)
        db.commit()
        log.debug(f"Reset last_modified for {len(datasources)} datasources.")


if __name__ == "__main__":
    setup_logging()
    reset_datasource()
