from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

from backend.db.db import SessionLocal
from backend.models import Calendar, Service, StopTime, Journey, DirectionType


def generate_timetable(line_id: str, db: Session):
    today = datetime.now().date()

    # Fetch the services for the given route
    services = (
        db.query(Service)
        .join(Journey, Service.service_code == Journey.service_code)
        .filter(Journey.line_id == line_id)
        .all()
    )

    # Collect all unique stops in order of appearance
    stop_order = {}
    journey_stop_times = {}
    journey_ids = set()
    start_times = {}

    for service in services:
        for journey in service.journeys:
            if journey.direction == DirectionType.outbound:
                journey_ids.add(journey.id)
                start_times[journey.id] = journey.start_time
                stop_times = (
                    db.query(StopTime)
                    .filter(StopTime.journey_id == journey.id)
                    .order_by(StopTime.stop_sequence)
                    .all()
                )
                journey_stop_times[journey.id] = {}
                for stop_time in stop_times:
                    stop = stop_time.stop
                    if stop:
                        if stop.common_name not in stop_order.keys():
                            stop_order[stop.common_name] = stop_time.stop_sequence
                        dep_time = stop_time.departure_time
                        if dep_time is not None:
                            total_seconds = int(dep_time.total_seconds())
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            formatted_time = f"{hours:02d}:{minutes:02d}"
                            if stop.common_name == "Health Centre":
                                print(
                                    f"Stop: {stop.common_name}, Time: {stop.atco_code}"
                                )
                            journey_stop_times[journey.id][stop.common_name] = (
                                formatted_time
                            )
                        else:
                            journey_stop_times[journey.id][stop.common_name] = "-"

    # Sort stops by their sequence
    stop_ordered = [stop[0] for stop in sorted(stop_order.items(), key=lambda x: x[1])]

    # Sort journey_ids by their start_time (timedelta)
    sorted_journey_ids = sorted(journey_ids, key=lambda jid: start_times[jid])

    # Build DataFrame: rows=stops, columns=journeys
    data = {}
    for id in sorted_journey_ids:
        data[id] = [journey_stop_times[id].get(stop, "-") for stop in stop_ordered]

    df = pd.DataFrame(data, index=stop_ordered)
    df.columns = [""] * len(
        df.columns
    )  # Hide journey ids by setting empty column names
    df.to_html("timetable.html", justify="center", border=1)
    print("✔ Timetable generated at timetable.html")


if __name__ == "__main__":
    line_id = "SCSO:PH0005857:165:64"
    with SessionLocal() as db:
        generate_timetable(line_id, db)
