from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.models import (
    Stop,
)

log = get_logger()


def times_from_stop(stop_id: str, db: Session, limit: int = 10):
    now = datetime.now(tz=LONDON)
    # now = datetime(year=2025, month=9, day=19, hour=7, minute=1, second=0, tzinfo=LONDON)
    seconds_since_midnight = now.hour * 3600 + now.minute * 60 + now.second
    current_time = timedelta(seconds=seconds_since_midnight)

    stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()
    if not stop:
        log.warning(f"Stop with ID {stop_id} not found.")
        return

    stop_times = stop.times_from_stop(db, date=now)

    # 5️⃣ Format results
    results = []
    for st in stop_times[:limit]:
        line_name = st.journey.timetable.line_name if st.journey.timetable else None
        dest = st.headsign
        dep_str = st.departure_time_str
        time_to = st.departure_time - current_time
        mins = int(time_to.total_seconds() // 60)
        if mins < 1:
            time_to_str = "due"
        elif mins < 60:
            time_to_str = f"{mins} min"
        else:
            time_to_str = dep_str
        results.append((line_name, dest, time_to_str, st.journey.id))

    stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()

    if not stop:
        print(f"Stop with ID {stop_id} not found.")
        return

    print(f"Departures from {stop.long_name}:")

    # 6️⃣ Print nicely
    if results:
        longest_dest = max(len(dest or "") for _, dest, _, _ in results)
        longest_line = max(len(line or "") for line, _, _, _ in results)
        for line_name, dest, dep, id in results:
            print(
                f"{line_name:<{longest_line + 1}}to {dest:<{longest_dest + 2}} {dep} ({id})"
            )
    else:
        print("No departures found.")


if __name__ == "__main__":
    setup_logging()
    stop_id = "1900HA110364"
    with SessionLocal() as db:
        times_from_stop(stop_id, db)
