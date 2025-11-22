from datetime import datetime

from sqlalchemy.orm import Session

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.models import (
    Stop,
)
import sys

from backend.utils.time_taken import time_taken

log = get_logger(__name__)


def times_from_stop(stop_id: str, db: Session, limit: int = 10):
    now = datetime.now(tz=LONDON)
    # now = datetime(
    #     year=2025, month=11, day=20, hour=18, minute=2, second=0, tzinfo=LONDON
    # )

    stop: Stop | None = db.query(Stop).filter(Stop.atco_code == stop_id).first()
    if not stop:
        log.warning(f"Stop with ID {stop_id} not found.")
        return

    with time_taken("fetching stop times"):
        stop_times = stop.times_from_stop(db, date_time=now)

    results = []
    for st in stop_times:
        line_name = st.journey.timetable.line_name if st.journey.timetable else None
        dest = st.headsign
        dep_str = st.departure_time_str
        time_to = st._dep_dt - now
        mins = int(time_to.total_seconds() // 60)
        if mins < 1:
            time_to_str = "due"
        elif mins < 60:
            time_to_str = f"{mins} min"
        else:
            time_to_str = dep_str + (
                " (tomorrow)" if st._dep_dt.date() > now.date() else ""
            )
        results.append((line_name, dest, time_to_str, st.journey.id))

    stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()

    if not stop:
        print(f"Stop with ID {stop_id} not found.")
        return

    print(f"Departures from {stop.long_name} at {now.strftime('%H:%M:%S')}:")

    if results:
        longest_dest = max(len(dest or "") for _, dest, _, _ in results)
        longest_line = max(len(line or "") for line, _, _, _ in results)
        for line_name, dest, dep, id in results:
            print(
                f"{line_name:<{longest_line + 1}}to {dest:<{longest_dest + 2}} {dep} (id: {id})"
            )
    else:
        print("No departures found.")


if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) != 2:
        log.debug("Usage: python times_from_stop.py <stop_id>")
        exit(1)
    stop_id = sys.argv[1]
    with SessionLocal() as db:
        times_from_stop(stop_id, db)
