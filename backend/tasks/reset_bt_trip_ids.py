from backend.config import setup_logging
from backend.db.db import SessionLocal
from backend.models import Journey


def reset_trip_ids():
    with SessionLocal() as db:
        count = (
            db.query(Journey)
            .filter(Journey.bt_trip_id.isnot(None))
            .update({Journey.bt_trip_id: None}, synchronize_session=False)
        )
        db.commit()
        print(f"Reset bt_trip_id for {count} journeys.")


if __name__ == "__main__":
    setup_logging()
    reset_trip_ids()
