from backend.services import bus, stops
from backend.db.db import SessionLocal
from backend.models import Stop
from datetime import datetime, timedelta
from backend.deps import LONDON, UTC
import logging

log = logging.getLogger(__name__)


async def get_scheduled(stop_id: str, redis, services=None):
    times = []

    if not services:
        services = await stops.get_services_from_stop(stop_id, redis)

    line_names = {service.get("line_name") for service in services}

    use_db_method = False
    with SessionLocal() as db:
        stop = db.query(Stop).filter(Stop.atco_code == stop_id).first()

        if stop:
            db_lines = Stop.lines_served(stop, db)
            db_line_names = [line.line_name for line in db_lines]
            if set(line_names).issubset(set(db_line_names)):
                use_db_method = True

        if use_db_method:
            log.debug("Using DB method for departures")
            db_times = stop.times_from_stop(db)
            # if len(db_times) == 0 and datetime.now(tz=LONDON).hour > 20:
            #     log.debug("trying tomorrow")
            #     tomorrow = datetime.now(tz=UTC) + timedelta(days=1)
            #     tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            #     db_times = stop.times_from_stop(db, date_time=tomorrow)

            #     if len(db_times) == 0:
            #         log.debug(
            #             "No times found in DB tomorrow, falling back to old method"
            #         )
            #         times = await stops.get_times(stop_id, redis)
            #         use_db_method = False

            if use_db_method:
                times = []
                for st, _ in db_times:
                    journey = st.journey
                    trip_id = await journey.get_bt_trip_id(db)
                    if not trip_id:
                        log.warning(
                            f"No trip ID for journey {journey.id}, stop {stop_id}"
                        )
                        use_db_method = False
                        break
                    times.append(
                        {
                            "trip_id": int(trip_id),
                            "journey_id": journey.id,
                            "st": st,
                        }
                    )
    if not use_db_method or times is None or len(times) == 0:
        log.warning("Not all data in db, using old method")
        times = await stops.get_times(stop_id, redis)

    log.debug(f"got {len(times)} scheduled times")

    return times, use_db_method


async def get_departures(stop_id: str, redis):
    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    times, use_db_method = await get_scheduled(stop_id, redis, services=services)

    buses = await bus.fetch_buses(
        service_ids,
        stop_id,
        times,
        redis,
        use_db=use_db_method,
        is_tomorrow=False,
    )
    log.debug(f"got {len(buses)} buses")

    return buses
