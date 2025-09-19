from sqlalchemy.orm import Session

from backend.db.db import SessionLocal
from backend.models import (
    StopTime, Journey,
)


def print_journey(journey_id: str, db: Session):
    journey: Journey = db.query(Journey).filter(Journey.id == journey_id).first()
    stop_times = db.query(StopTime).filter(StopTime.journey_id == journey_id).order_by(StopTime.stop_sequence).all()

    stops = []
    for st in stop_times:
        stop = st.stop.common_name
        dest = st.headsign
        dep_str = st.departure_time_str
        stops.append((stop, dest, dep_str))

    print(
        f"{journey.start_time} to {journey.headsign} ({journey.vehicle_journey_code}):"
    )

    for stop in stops:
        print(f"  {stop[0] + " - " + stop[2]:<40} ({stop[1]})")


if __name__ == "__main__":
    journey_id = "PH0005857:120:13:VJ2564"
    with SessionLocal() as db:
        print_journey(journey_id, db)
