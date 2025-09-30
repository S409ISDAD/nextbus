from backend.services import bus, stops
from backend.db.db import SessionLocal
from backend.models import Stop
from datetime import datetime, timedelta
from backend.deps import LONDON, UTC
import logging

log = logging.getLogger(__name__)


async def get_scheduled(stop_id: str, redis, services=None):
    # if not services:
    #     services = await stops.get_services_from_stop(stop_id, redis)

    # line_names = {service.get("line_name") for service in services}

    times = await stops.get_times(stop_id, redis)

    line_names = {time.get("service", {}).get("line_name") for time in times}

    scheduled_times = []

    with SessionLocal() as db:
        stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()

        if stop:
            db_lines = Stop.lines_served(stop, db)
            db_line_names = [line.line_name for line in db_lines]
            db_times = stop.times_from_stop(db)

        for line_name in line_names:
            if line_name in db_line_names:
                log.debug(f"Using DB method for {line_name}")

                filtered_st = [
                    st
                    for st in db_times
                    if st.journey
                    and st.journey.timetable
                    and st.journey.timetable.line_name == line_name
                ]

                for st in filtered_st:
                    journey = st.journey
                    trip_id = await journey.get_bt_trip_id(db)
                    if not trip_id:
                        log.warning(
                            f"No trip ID for journey {journey.id}, stop {stop_id}"
                        )

                    dayshift = 0
                    if st._dep_dt.date() > datetime.now(tz=LONDON).date():
                        dayshift = 1
                    scheduled_times.append(
                        {
                            "trip_id": trip_id,
                            "journey_id": journey.id,
                            "dayshift": dayshift,
                            "source": "db",
                            "st": st,
                        }
                    )

            else:
                log.debug(f"Not using DB method for {line_name}")
                filtered_times = [
                    t
                    for t in times
                    if t.get("service", {}).get("line_name") == line_name
                ]
                for t in filtered_times:
                    scheduled_times.append({**t, "source": "api"})

    log.debug(f"got {len(scheduled_times)} scheduled times")

    return scheduled_times


async def get_departures(stop_id: str, redis):
    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    times = await get_scheduled(stop_id, redis, services=services)

    buses = await bus.fetch_buses(
        service_ids,
        stop_id,
        times,
        redis,
    )
    log.debug(f"got {len(buses)} buses")

    return buses
