from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from backend.db.db import SessionLocal
from backend.models import Service, ServiceStopUsage, Stop, StopTime, Journey
from backend.deps import LONDON


def generate_timetable(service_id: int, db: Session, inbound: bool = True):
    today = datetime.now(tz=LONDON) + timedelta(days=2)

    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        print(f"Service {service_id} not found")
        return

    # Get ordered stops for inbound trips
    stops = (
        db.query(ServiceStopUsage)
        .filter(
            ServiceStopUsage.service_id == service_id,
            ServiceStopUsage.line_name == service.line_name,
            ServiceStopUsage.inbound.is_(inbound),
        )
        .order_by(ServiceStopUsage.order)
        .all()
    )
    stop_ordered = [su.stop_id for su in stops]

    # Get valid inbound trips
    journeys = (
        db.query(Journey)
        .filter(
            Journey.service_id == service_id,
            Journey.inbound.is_(inbound),
        )
        .order_by(Journey.start_time)
        .all()
    )
    journeys = [j for j in journeys if j.is_valid(today)]

    print(
        f"Generating timetable for service {service.line_name} ({'inbound' if inbound else 'outbound'}) with {len(journeys)} journeys and {len(stops)} stops."
    )

    data = {j.id: [] for j in journeys}
    for su in stops:
        for i in journeys:
            st = (
                db.query(StopTime)
                .filter(
                    StopTime.journey_id == i.id,
                    StopTime.stop_id == su.stop_id,
                )
                .first()
            )
            if st:
                data[i.id].append(st.dep_or_arr_str)
            else:
                data[i.id].append("-")

    stop_mask = []
    for i, atco in enumerate(stop_ordered):
        if any(data[j.id][i] != "-" for j in journeys):
            stop_mask.append(True)
        else:
            stop_mask.append(False)

    stop_ordered_filtered = [
        atco for atco, keep in zip(stop_ordered, stop_mask) if keep
    ]

    for j_id in data:
        data[j_id] = [time for time, keep in zip(data[j_id], stop_mask) if keep]

    stops_objs = db.query(Stop).filter(Stop.atco_code.in_(stop_ordered_filtered)).all()

    stop_names = []
    for atco in stop_ordered_filtered:
        stop = next((s for s in stops_objs if s.atco_code == atco), None)
        stop_names.append(stop.common_name if stop else "Unknown")

    # Create DataFrame
    df = pd.DataFrame(data, index=stop_names)
    df.columns = [journey.vehicle_journey_code for journey in journeys]

    # Export to HTML
    df.to_html("timetable.html", justify="center", border=1)
    print("✔ Timetable generated at timetable.html")


if __name__ == "__main__":
    service_id = 7
    with SessionLocal() as db:
        generate_timetable(service_id, db, inbound=False)
