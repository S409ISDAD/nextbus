from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session, joinedload

from backend.core.db import SessionLocal
from backend.models import Calendar, CalendarDate, Route, Service, StopTime, Trip


def times_from_stop(stop_id: str, db: Session):
    today = datetime.now()
    weekday = today.date().strftime("%A").lower()
    seconds_since_midnight = today.hour * 3600 + today.minute * 60 + today.second

    # 1️⃣ Get all service_ids for this stop with preloaded relationships
    stop_times = (
        db.query(StopTime)
        .filter(StopTime.stop_id == stop_id)
        .join(Trip, StopTime.trip_id == Trip.id)
        .join(Service, Trip.service_id == Service.id)
        .options(joinedload(StopTime.trip).joinedload(Trip.service))
        .limit(10)
        .all()
    )
    service_ids = {st.trip.service_id for st in stop_times}

    if not service_ids:
        return []  # Early exit if no services are found

    # 2️⃣ Find exceptions for today in a single query
    exceptions = {
        cd.service_id: cd.exception_type
        for cd in db.query(CalendarDate)
        .filter(CalendarDate.service_id.in_(service_ids), CalendarDate.date == today)
        .all()
    }

    # 3️⃣ Find active services for today
    active_service_ids = {
        sid
        for sid in service_ids
        if exceptions.get(sid) == 1
        or (
            exceptions.get(sid) is None
            and db.query(Calendar)
            .filter(
                Calendar.service_id == sid,
                Calendar.start_date <= today.date(),
                Calendar.end_date >= today.date(),
                getattr(Calendar, weekday),
            )
            .first()
        )
    }

    if not active_service_ids:
        return []  # Early exit if no active services are found

    # 4️⃣ Get today's stop_times for this stop and active services
    stop_times = (
        db.query(StopTime)
        .distinct(StopTime.departure_time)
        .filter(
            StopTime.stop_id == stop_id,
            StopTime.departure_time >= seconds_since_midnight,
        )
        .join(Trip, StopTime.trip_id == Trip.id)
        .filter(Trip.service_id.in_(active_service_ids))
        .join(Route, Trip.route_id == Route.id)
        .options(joinedload(StopTime.trip).joinedload(Trip.route))
        .order_by(StopTime.departure_time)
        .limit(10)
        .all()
    )

    stop_times_df = pd.DataFrame(
        [
            (
                st.trip.route.short_name if hasattr(st.trip, "route") else None,
                st.trip.headsign if hasattr(st, "trip") else None,
                st.get_departure_time,
            )
            for st in stop_times
        ],
        columns=["route_num", "dest", "departure_time"],
    )
    stop_times_df.set_index("route_num", inplace=True)
    stop_times_df.index.name = None  # Remove the index (route_num) title

    longest_dest = stop_times_df["dest"].str.len().max()

    for departure in stop_times_df.itertuples():
        print(
            f"{departure.Index:<3} {departure.dest:<{longest_dest + 2}} {departure.departure_time}"
        )


if __name__ == "__main__":
    stop_id = "1980SN120841"
    with SessionLocal() as db:
        times_from_stop(stop_id, db)
