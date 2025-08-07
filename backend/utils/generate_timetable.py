from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

from backend.core.db import SessionLocal
from backend.models import Calendar, CalendarDate, Service, StopTime, Trip


def generate_timetable(route_id: int, db: Session):
    today = datetime.now().date() - timedelta(days=1)
    weekday = today.strftime("%A").lower()

    # 1️⃣ get service IDs and exceptions
    service_ids = [
        sid
        for (sid,) in db.query(Service.id)
        .join(Trip, Trip.service_id == Service.id)
        .filter(Trip.route_id == route_id)
        .distinct()
        .all()
    ]

    exceptions = {
        cd.service_id: cd.exception_type
        for cd in db.query(CalendarDate)
        .filter(CalendarDate.service_id.in_(service_ids), CalendarDate.date == today)
        .all()
    }

    # 2️⃣ find active services
    active_service_ids = set()
    for sid in service_ids:
        et = exceptions.get(sid)
        if et == 1:
            active_service_ids.add(sid)
        elif et == 2:
            continue
        else:
            cal = db.query(Calendar).filter(Calendar.service_id == sid).first()
            if (
                cal
                and cal.start_date <= today <= cal.end_date
                and getattr(cal, weekday)
            ):
                active_service_ids.add(sid)

    # 3️⃣ fetch trips for that route and direction=0
    trips = (
        db.query(Trip)
        .filter(
            Trip.route_id == route_id,
            Trip.direction == 0,
            Trip.service_id.in_(active_service_ids),
        )
        .all()
    )

    if not trips:
        print("No active trips found for given route / date.")
        return

    # 4️⃣ Build stop_id→name from all related StopTimes
    stop_id_to_name = {}
    stop_times_q = db.query(StopTime).join(Trip).filter(Trip.route_id == route_id).all()
    for st in stop_times_q:
        stop_id_to_name[st.stop_id] = st.stop.name

    # 5️⃣ Aggregate trip data + stop positions
    stop_positions = defaultdict(list)
    all_trip_data = {}

    for trip in trips:
        sts = (
            db.query(StopTime)
            .filter(StopTime.trip_id == trip.id)
            .order_by(StopTime.stop_sequence)
            .all()
        )
        trip_times = {}
        for idx, st in enumerate(sts):
            sid = st.stop_id
            time = st.departure_time or st.arrival_time
            if time is not None:
                h = time // 3600
                m = (time % 3600) // 60
                trip_times[sid] = f"{h:02d}:{m:02d}"
            else:
                trip_times[sid] = "-"
            stop_positions[sid].append(idx)
        earliest = min(
            (st.departure_time for st in sts if st.departure_time is not None),
            default=None,
        )
        if earliest is not None:
            all_trip_data[(trip.vehicle_journey_code, earliest)] = trip_times

    # 6️⃣ Deduplicate trips by stop times
    unique = {}
    seen = set()
    for key, times in all_trip_data.items():
        tpl = tuple(sorted(times.items()))
        if tpl not in seen:
            seen.add(tpl)
            unique[key] = times
    sorted_trips = dict(sorted(unique.items(), key=lambda x: x[0][1]))

    # 7️⃣ Compute average stop ordering
    # 🔁 Find the trip with the most stops
    longest_trip = max(
        trips,
        key=lambda trip: len(
            [st for st in db.query(StopTime).filter(StopTime.trip_id == trip.id).all()]
        ),
    )

    # 🔁 Get its ordered stop IDs
    longest_sts = (
        db.query(StopTime)
        .filter(StopTime.trip_id == longest_trip.id)
        .order_by(StopTime.stop_sequence)
        .all()
    )
    longest_order = [st.stop_id for st in longest_sts]

    # ✅ Then sort by position in that trip, falling back to average
    avg = {sid: sum(pos) / len(pos) for sid, pos in stop_positions.items()}
    ordered_ids = sorted(
        avg.keys(),
        key=lambda sid: (
            longest_order.index(sid) if sid in longest_order else float("inf"),
            avg[sid],
        ),
    )

    # 8️⃣ Deduplicate stop names in order
    final_ids = []
    seen_names = set()
    for sid in ordered_ids:
        name = stop_id_to_name.get(sid)
        if name and name not in seen_names:
            seen_names.add(name)
            final_ids.append(sid)

    # Build DataFrame
    df = pd.DataFrame.from_dict(
        {k[0]: v for k, v in sorted_trips.items()}, orient="index"
    )
    df = df.rename(columns=stop_id_to_name).fillna("-").transpose()

    # 9️⃣ Reindex only the stops that were served (deduped names)
    final_stop_names = [stop_id_to_name[sid] for sid in final_ids]
    missing = [name for name in df.index if name not in final_stop_names]
    final_stop_names += sorted(missing)
    df = df.reindex(final_stop_names)

    # 1️⃣0️⃣ Save to HTML
    df.to_html("timetable.html", index=True, header=True, justify="center", border=1)
    print("✔ Timetable generated at timetable.html")


if __name__ == "__main__":
    route_id = 93149
    with SessionLocal() as db:
        generate_timetable(route_id, db)
