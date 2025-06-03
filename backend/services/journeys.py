import datetime
from backend.config import BASE
from datetime import datetime as dt
from datetime import timedelta

from backend.models.journey import Journey
from backend.models.stop import StopTime
from backend.services.caching import (
    get_cached,
    BUS_CACHE,
)
from backend.utils.fetch_json import fetch_json
from dateutil import parser

from backend.utils.time import check_scheduled_time


async def get_vehicle_journey(bus_id, journey_id, delay, r) -> Journey:
    async def fetch(bus_id, journey_id, delay):
        data = await fetch_json(
            BASE + f"/vehicles/{bus_id}/journeys/{journey_id}.json",
        )

        if not data:
            return

        uk_timezone = datetime.timezone(datetime.timedelta(hours=1))
        current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

        for i, stop in enumerate(data["stops"]):
            if i == len(data["stops"]) - 1:
                aimed = data["stops"][i].get("aimed_arrival_time")
            else:
                aimed = data["stops"][i].get("aimed_departure_time")
            if aimed:
                scheduled_time = dt.strptime(aimed, "%H:%M").replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day,
                    tzinfo=current_time.tzinfo,
                )

                scheduled_time = check_scheduled_time(scheduled_time, current_time)

                expt_time = scheduled_time + timedelta(seconds=int(delay))

                data["stops"][i]["aimed_time"] = scheduled_time.timestamp()
                data["stops"][i]["expt_time"] = expt_time.timestamp()

            actual_departure = data["stops"][i].get("actual_departure_time")
            if actual_departure:
                departure_time = parser.isoparse(actual_departure)

                data["stops"][i]["actual_time"] = departure_time.timestamp()

        return data

    journey = await get_cached(
        key=f"journeys:{bus_id}:{journey_id}",
        func=lambda *args: fetch(*args),
        args=(bus_id, journey_id, delay),
        exp=BUS_CACHE,
        r=r,
    )

    json_stops = journey.get("stops")
    stops: list[StopTime] = []

    for stop in json_stops:
        stops.append(
            StopTime(
                stop_id=stop.get("atco_code"),
                name=stop.get("name"),
                aimed_time=stop.get("aimed_time"),
                expt_time=stop.get("expt_time"),
                actual_time=stop.get("actual_time"),
                minor=stop.get("minor"),
            )
        )

    return Journey(
        route_name=journey.get("route_name"),
        destination=journey.get("destination"),
        stops=stops,
    )
