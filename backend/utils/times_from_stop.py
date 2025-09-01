from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload

from backend.db.db import SessionLocal
from backend.deps import UTC
from backend.models import (
    Calendar,
    DirectionType,
    Line,
    Stop,
    StopTime,
    Journey,
)


def times_from_stop(stop_id: str, db: Session, limit: int = 10):
    now = datetime.now(tz=UTC)
    # now = datetime(year=2025, month=8, day=10, hour=11, minute=1, second=0)
    weekday_attr = now.strftime("%A").lower()
    today_date = now.date()
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    current_time = timedelta(seconds=seconds_since_midnight)

    # 1️⃣ Get all StopTimes for this stop (with Journey+Calendar preloaded)
    stop_times = (
        db.query(StopTime)
        .filter(StopTime.stop_id == stop_id)
        .join(Journey)
        .join(Calendar)
        .options(
            joinedload(StopTime.journey).joinedload(Journey.calendar),
            joinedload(StopTime.journey)
            .joinedload(Journey.line)
            .joinedload(Line.service),
        )
        .all()
    )

    # 2️⃣ Filter by active calendars
    active_stop_times = []
    for st in stop_times:
        cal = st.journey.calendar
        # Check calendar valid date range
        if not (
            cal.start_date <= today_date
            and (cal.end_date is None or cal.end_date >= today_date)
        ):
            continue

        # Check weekday flag
        if not getattr(cal, weekday_attr):
            continue

        # Check exceptions
        has_exception = False
        for exc in cal.calendar_exceptions:
            if exc.start_date <= today_date <= exc.end_date:
                if not exc.operating:
                    has_exception = True
                else:
                    has_exception = False
                break

        if has_exception:
            continue

        active_stop_times.append(st)

    # 3️⃣ Keep only future departures
    future_stop_times = [
        st
        for st in active_stop_times
        if st.departure_time and st.departure_time >= current_time
    ]

    # 4️⃣ Sort by departure time
    future_stop_times.sort(key=lambda st: st.departure_time)

    # 5️⃣ Format results
    results = []
    for st in future_stop_times[:limit]:
        line_name = st.journey.line.line_name if st.journey.line else None
        outbound = st.journey.direction == DirectionType.outbound
        dest = st.journey.service.destination if outbound else st.journey.service.origin
        dep_str = st.departure_time_str
        time_to = st.departure_time - current_time
        mins = int(time_to.total_seconds() // 60)
        if mins < 1:
            time_to_str = "due"
        elif mins < 60:
            time_to_str = f"{mins} min"
        else:
            time_to_str = dep_str
        results.append((line_name, dest, time_to_str))

    stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()

    if not stop:
        print(f"Stop with ID {stop_id} not found.")
        return

    print(
        f"Departures from {stop.common_name if stop else stop_id} ({stop.indicator}):"
    )

    # 6️⃣ Print nicely
    if results:
        longest_dest = max(len(dest or "") for _, dest, _ in results)
        longest_line = max(len(line or "") for line, _, _ in results)
        for line_name, dest, dep in results:
            print(f"{line_name:<{longest_line + 1}}to {dest:<{longest_dest + 2}} {dep}")
    else:
        print("No departures found.")


if __name__ == "__main__":
    stop_id = "1900HA020331"
    with SessionLocal() as db:
        times_from_stop(stop_id, db)
