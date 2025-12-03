from backend.services import bus, stops
from backend.db.db import SessionLocal
from backend.models import Stop, to_dict
from datetime import datetime
from backend.services.caching import get_cached
from backend.deps import LONDON
from backend.models import StopTime
from redis import Redis

from backend.deps import get_logger
from backend.utils.time_taken import time_taken

log = get_logger(__name__)


def get_scheduled(stop_id: str, redis, services=None):
    # if not services:
    #     services = stops.get_services_from_stop(stop_id, redis)

    # line_names = {service.get("line_name") for service in services}

    def fetch_times(stop_id: str, redis: Redis) -> list[dict]:
        """fetch scheduled departure times for a given stop ID

        Args:
            stop_id (str): ATCO code of bus stop
            redis (Redis): Redis connection for caching

        Returns:
            list[dict]: a list of scheduled departure times
        """
        times = stops.get_times(stop_id, redis)  # fetch times from bustimes.org

        if not times:
            log.error("times is none")
            line_names = set()
        else:
            line_names = {
                time.get("service", {}).get("line_name") for time in times
            }  # generate set of line names

        scheduled_times = []
        db_line_names = []
        db_times = []

        with SessionLocal() as db:  # open a database session
            stop = (
                db.query(Stop).filter(Stop.atco_code == stop_id).first()
            )  # fetch stop from the database

            if stop:
                db_lines = Stop.lines_served(stop, db)  # fetch lines served by the stop
                db_line_names = [
                    line.line_name for line in db_lines
                ]  # extract line names
                with time_taken("fetching db times"):
                    db_times = stop.times_from_stop(
                        db
                    )  # fetch StopTime objects from the database
            else:
                log.warning(f"Stop {stop_id} not found in database")
                return []

            if len(line_names) == 0:
                # if no line names from bustimes.org API, use DB line names
                line_names = db_line_names

            for line_name in line_names:
                if line_name in db_line_names:
                    # prefer database times if available for that line
                    filtered_st = [
                        st
                        for st in db_times
                        if st.journey
                        and st.journey.timetable
                        and st.journey.timetable.line_name == line_name
                    ]  # only include StopTimes with that line name

                    for st in filtered_st:
                        journey = st.journey
                        trip_id = journey.get_bt_trip_id(
                            db
                        )  # get bustimes.org trip ID for that journey
                        if not trip_id:
                            log.warning(
                                f"No trip ID for journey {journey.id}, stop {stop_id}"
                            )

                        dayshift = 0
                        if st._dep_dt.date() > datetime.now(tz=LONDON).date():
                            dayshift = 1  # departure is the next day
                        scheduled_times.append(
                            {
                                "line_name": line_name,
                                "dest": st.journey.headsign,
                                "trip_id": trip_id,
                                "journey_id": journey.id,
                                "dayshift": dayshift,
                                "source": "db",
                                "st": to_dict(st),
                                "dep_dt": st._dep_dt,
                            }
                        )

                else:
                    # otherwise, use bustimes.org API times
                    filtered_times = [
                        t
                        for t in times
                        if t.get("service", {}).get("line_name") == line_name
                    ]  # filter times for that line name
                    for t in filtered_times:
                        scheduled_times.append({**t, "source": "api"})
        return scheduled_times

    scheduled_times = get_cached(
        key=f"scheduled_times:{stop_id}",
        func=fetch_times,
        args=(stop_id, redis),
        exp=10,
        r=redis,
    )  # cache for 10 seconds because this function is called frequently

    for item in scheduled_times:
        if item.get("source") == "db" and isinstance(
            item.get("st"), dict
        ):  # ensure st is a StopTime object
            item["st"] = StopTime(**item["st"])  # reconstruct StopTime object
            dep_dt = item.get("dep_dt")
            if type(dep_dt) is str:
                # convert dep_dt to datetime object if it's a string
                try:
                    dep_dt = datetime.fromisoformat(dep_dt)
                except ValueError:
                    log.error(f"Invalid dep_dt format: {dep_dt}")
                    dep_dt = None
            setattr(item["st"], "_dep_dt", dep_dt)

    log.debug(f"got {len(scheduled_times)} scheduled times")

    return scheduled_times


def get_departures(stop_id: str, redis):
    services = stops.get_services_from_stop(
        stop_id, redis
    )  # fetch services for the stop from bustimes.org

    service_ids = [service.get("id") for service in services]  # extract service IDs

    times = get_scheduled(stop_id, redis, services)  # fetch scheduled times (see above)

    buses = bus.fetch_buses(
        service_ids,
        stop_id,
        times,
        redis,
    )  # fetch all buses (live and scheduled combined)
    log.debug(f"got {len(buses)} buses")

    return buses
