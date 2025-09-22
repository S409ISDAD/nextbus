from sqlalchemy.orm import Session

from backend.config import setup_logging
from backend.db.db import SessionLocal
from backend.models import (
    StopTime,
    Journey,
)


def print_journey(journey_id: str, db: Session):
    journey: Journey = db.query(Journey).filter(Journey.id == journey_id).first()
    stop_times = (
        db.query(StopTime)
        .filter(StopTime.journey_id == journey_id)
        .order_by(StopTime.stop_sequence)
        .all()
    )

    stops = []
    for st in stop_times:
        stop = st.stop.long_name
        dest = st.headsign
        dep_str = st.departure_time_str
        stops.append((stop, dest, dep_str))

    print(
        f"{journey.start_time} to {journey.headsign} ({journey.vehicle_journey_code}):"
    )

    longest_stop_name = max(len(f"  {stop[0] + ' - ' + stop[2]}") for stop in stops)

    for stop in stops:
        print(f"  {stop[0] + ' - ' + stop[2]:<{longest_stop_name}} ({stop[1]})")


if __name__ == "__main__":
    setup_logging()
    journey_id = "PH0005857:167:67:VJ98"
    with SessionLocal() as db:
        print_journey(journey_id, db)
