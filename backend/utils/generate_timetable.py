from datetime import datetime

from sqlalchemy.orm import Session

from backend.db.db import SessionLocal
from backend.models import (
    Calendar,
    Service,
    ServiceStopUsage,
    Stop,
    StopTime,
    Journey,
    journey_is_valid_filter,
)
from backend.deps import LONDON
import sys


def generate_timetable(
    service: Service, today: datetime, db: Session, inbound: bool = True
):
    # Get ordered stops for inbound trips
    stops = (
        db.query(ServiceStopUsage)
        .filter(
            ServiceStopUsage.service_id == service.id,
            ServiceStopUsage.line_name == service.line_name,
            ServiceStopUsage.inbound.is_(inbound),
        )
        .order_by(ServiceStopUsage.order)
        .all()
    )
    stop_ordered = [su.stop_id for su in stops]

    current_timetable = service.get_correct_timetable()

    # Get valid inbound trips
    journey_filters = [
        Journey.service_id == service.id,
        Journey.inbound.is_(inbound),
        journey_is_valid_filter(today.date()),
    ]
    if current_timetable:
        journey_filters.append(Journey.timetable_id == current_timetable.id)

    journeys = (
        db.query(Journey)
        .filter(*journey_filters)
        .join(Calendar, Journey.calendar)
        .order_by(Journey.start_time)
        .distinct(Journey.start_time, Journey.end_time)
        .all()
    )

    print(
        f"Generating timetable for service {service.line_name} ({'inbound' if inbound else 'outbound'}) with {len(journeys)} journeys and {len(stops)} stops."
    )

    timing_points = {}

    stoptimes = (
        db.query(StopTime)
        .filter(
            StopTime.journey_id.in_([j.id for j in journeys]),
            StopTime.stop_id.in_([s.stop_id for s in stops]),
        )
        .all()
    )
    journey_stop_to_stoptime = {(st.journey_id, st.stop_id): st for st in stoptimes}

    data = {j.id: [] for j in journeys}
    for su in stops:
        for i in journeys:
            st = journey_stop_to_stoptime.get((i.id, su.stop_id))
            if st:
                data[i.id].append(st.dep_or_arr_str)
                timing_points[su.stop_id] = st.timing_status
            else:
                data[i.id].append(None)

    stop_mask = []
    for i, atco in enumerate(stop_ordered):
        if any(data[j.id][i] is not None for j in journeys):
            stop_mask.append(True)
        else:
            stop_mask.append(False)

    stop_ordered_filtered = [
        atco for atco, keep in zip(stop_ordered, stop_mask) if keep
    ]

    for j_id in data:
        data[j_id] = [time for time, keep in zip(data[j_id], stop_mask) if keep]

    stops_objs = db.query(Stop).filter(Stop.atco_code.in_(stop_ordered_filtered)).all()

    stop_names = [
        next((s.name for s in stops_objs if s.atco_code == atco), "Unknown")
        for atco in stop_ordered_filtered
    ]

    response = {
        "service": {
            "id": service.id,
            "line_name": service.line_name,
            "inbound": inbound,
        },
        "stops": [
            {"id": atco, "name": name, "timing_status": timing_points.get(atco, "OTH")}
            for atco, name in zip(stop_ordered_filtered, stop_names)
        ],
        "journeys": [
            {
                "id": j.id,
                "start_time": str(j.start_time),
                "times": data[j.id],
            }
            for j in journeys
        ],
    }

    return response


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_timetable.py <service_id> <inbound (1/0)>")
        sys.exit(1)
    service_id = int(sys.argv[1])
    inbound = bool(int(sys.argv[2])) if len(sys.argv) > 2 else True
    with SessionLocal() as db:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            print(f"Service with ID {service_id} not found.")
            sys.exit(1)
        today = datetime.now(tz=LONDON)
        data = generate_timetable(service, today, db, inbound=inbound)

        stops = data["stops"]
        journeys = data["journeys"]

        # Header row
        header = ["Stop"]
        print("{:<30}".format(header[0]), end="")
        for h in header[1:]:
            print("{:<6}".format(h), end="")
        print()

        # Rows
        for i, stop in enumerate(stops):
            print("{:<30}".format(stop["name"]), end="")
            for j in journeys:
                time = j["times"][i] if i < len(j["times"]) else None
                print("{:<6}".format(time or "  -  "), end="")
            print()
