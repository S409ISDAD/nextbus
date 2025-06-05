import datetime
from datetime import datetime as dt
from datetime import timedelta

from dateutil import parser
from geopy.distance import geodesic

from backend.config import API_BASE, BASE
from backend.models.journey import Journey
from backend.models.stop import StopTime
from backend.services.caching import (
    BUS_CACHE,
    get_cached,
)
from backend.utils.fetch_json import fetch_json
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

        tracks = await fetch_tracks(journey_id)
        prev_time = 0
        total_delay = 0
        for i, stop in enumerate(data["stops"]):
            if tracks:
                data["stops"][i]["track"] = tracks[i]

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
                old_expt = expt_time

                if prev_time == expt_time:
                    coords_prev = tuple(data["stops"][i - 1]["coordinates"])
                    coords_next = tuple(data["stops"][i]["coordinates"])
                    dist_m = geodesic(coords_prev, coords_next).m

                    delay_factor = 20

                    extra_delay = round(dist_m / delay_factor)
                    total_delay = total_delay + extra_delay
                    expt_time += timedelta(seconds=total_delay)
                else:
                    total_delay = 0

                prev_time = old_expt

                data["stops"][i]["aimed_time"] = scheduled_time.timestamp()
                data["stops"][i]["expt_time"] = expt_time.timestamp()

            actual_departure = data["stops"][i].get("actual_departure_time")
            if actual_departure:
                departure_time = parser.isoparse(actual_departure)

                data["stops"][i]["actual_time"] = departure_time.timestamp()

        return data

    async def fetch_tracks(journey_id):
        data = await fetch_json(
            API_BASE + f"/vehiclejourneys/{journey_id}/",
        )

        if not data:
            return

        tracks = []

        for stop in data["times"]:
            tracks.append(stop.get("track", None))

        return tracks

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
                track=stop.get("track"),
                minor=stop.get("minor"),
            )
        )

    return Journey(
        route_name=journey.get("route_name"),
        destination=journey.get("destination"),
        stops=stops,
    )
