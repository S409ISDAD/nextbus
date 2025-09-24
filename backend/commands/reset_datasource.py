from backend.config import setup_logging
from backend.db.db import SessionLocal
from backend.models import DataSource


def reset_datasource():
    with SessionLocal() as db:
        datasources = db.query(DataSource).all()
        for ds in datasources:
            ds.last_modified = None
            db.add(ds)
        db.commit()
        print(f"Reset last_modified for {len(datasources)} datasources.")


if __name__ == "__main__":
    setup_logging()
    reset_datasource()
