import datetime
from datetime import datetime as dt
from datetime import timedelta

import redis.asyncio as redis
from backend.services.caching import (
    JOURNEY_CACHE,
    SERVICE_CACHE,
    get_cached,
    BUS_CACHE,
    TRIPS_CACHE,
)
from backend.utils.fetch_json import fetch_json
from dateutil import parser

from backend.models.bus import Bus
# from geopy.distance import geodesic


JSON_BASE = "https://bustimes.org/vehicles.json"
API_BASE = "https://bustimes.org/api/"


async def fetch_buses_for_service(service, stop_id, r: redis.Redis) -> list[Bus]:
    buses: list[Bus] = []

    active = await get_cached(
        f"service:{service}:trips",
        lambda *args: fetch_active_buses(*args),
        (service,),
        TRIPS_CACHE,
        r,
    )

    if not active:
        return []

    for trip in active:
        bus_id = trip.get("id")
        print(f"bus id: {bus_id}")

        if not bus_id:
            continue

        this_bus = await get_cached(
            f"bus:{bus_id}",
            lambda *args: fetch_bus(*args),
            (bus_id,),
            BUS_CACHE,
            r,
        )

        this_bus = this_bus[0]

        if not this_bus:
            continue

        delay = this_bus.get("delay")

        if not delay:
            continue

        timestamp = (
            parser.isoparse(this_bus.get("datetime"))
            if this_bus.get("datetime")
            else None
        )

        coords = this_bus.get("coordinates", [0, 0])
        vehicle = this_bus.get("vehicle", {})
        journey_id = this_bus.get("journey_id")
        destination = this_bus.get("destination")
        progress = this_bus.get("progress", 0)

        vehicle_name = vehicle["name"].split(" - ")
        fleet_num = vehicle_name[0] if len(vehicle_name) > 1 else "Unknown"
        reg = vehicle_name[-1]

        lateness = format_delay(delay)

        service_info = await get_cached(
            f"service_info:{service}",
            lambda *args: get_service_info(*args),
            (service,),
            SERVICE_CACHE,
            r,
        )

        times = await calculate_expected(delay, stop_id, journey_id, r)

        if times:
            buses.append(
                Bus(
                    service=service_info,
                    destination=destination,
                    reg=reg,
                    fleet_num=fleet_num,
                    journey_id=journey_id,
                    times=times,
                    delay=delay,
                    lateness=lateness,
                    progress=progress,
                    coords=coords,
                    timestamp=timestamp,
                )
            )

    return buses


def format_delay(delay):
    delay_min = int(round(delay / 60))

    formatted_delay = ""

    if delay == 0:
        formatted_delay = "on time"
    elif delay < 0 and delay > -60:
        formatted_delay = f"{abs(delay)}s early"
    elif delay <= -60:
        formatted_delay = f"{abs(delay_min)}m early"
    elif delay > 0 and delay < 60:
        formatted_delay = f"{abs(delay)}s late"
    elif delay >= 60:
        formatted_delay = f"{abs(delay_min)}m late"

    return formatted_delay


async def fetch_bus(bus_id):
    """Fetches specific bus"""
    data = await fetch_json(JSON_BASE + f"?id={bus_id}")

    return data


async def get_services_from_stop(stop_id):
    """Fetches all services from a stop."""
    data = await fetch_json(API_BASE + f"services/?stops={stop_id}")

    if not data:
        return

    services = set()

    for service in data.get("results"):
        services.add(service.get("id"))

    return list(services)


async def fetch_active_buses(service):
    """Fetches all buses on the route"""
    data = await fetch_json(JSON_BASE + f"?service={service}")

    if not data:
        return None

    return data


async def get_service_info(service):
    data = await fetch_json(API_BASE + f"services/{service}")

    if not data:
        return None

    return {
        "line_name": data.get("line_name", service),
        "detail": data.get("description").split("via")[1].lstrip()
        if "via" in data.get("description")
        else "",
    }


async def get_stop_name(stop_id):
    data = await fetch_json(
        API_BASE + f"stops/{stop_id}",
    )

    if not data:
        return

    name = data.get("name")
    return name


def get_vehicle_journey(journey_id):
    data = fetch_json(
        API_BASE + f"vehiclejourneys/{journey_id}",
    )

    return data


async def calculate_expected(delay, stop_id, journey_id, r):
    journey = await get_cached(
        f"journeys:{journey_id}",
        lambda *args: get_vehicle_journey(*args),
        (journey_id,),
        JOURNEY_CACHE,
        r,
    )

    times = journey.get("times")
    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    not_started = False

    stop_idx = 0

    for stop_time in times:
        if stop_idx == 0:
            aimed = stop_time.get("aimed_departure_time")
            scheduled_time = dt.strptime(aimed, "%H:%M").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day,
                tzinfo=current_time.tzinfo,
            )

            if scheduled_time > current_time:
                not_started = True

        if stop_time.get("stop").get("atco_code") == stop_id:
            aimed = stop_time.get("aimed_departure_time")
            if not aimed:
                return None
            scheduled_time = dt.strptime(aimed, "%H:%M").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day,
                tzinfo=current_time.tzinfo,
            )

            if not_started:
                delay = 0

            expected_time = scheduled_time + timedelta(seconds=delay)

            if expected_time < current_time:
                return None

            return {
                "expected": dt.strftime(expected_time, "%H:%M:%S"),
                "scheduled": dt.strftime(scheduled_time, "%H:%M:%S"),
                "not_started": not_started,
            }
        stop_idx += 1

    return None


# def calculate_speed(self, vehicle, coords, timestamp):
#     lat = coords[0]
#     lon = coords[1]

#     if vehicle in self.loc_history:
#         prev_coords = self.loc_history[vehicle]["coords"]
#         prev_time = self.loc_history[vehicle]["time"]

#         self.loc_history[vehicle]["coords"] = (lat, lon)
#         self.loc_history[vehicle]["time"] = timestamp

#         time_diff = (
#             timestamp - prev_time
#         ).total_seconds() / 3600  # time difference in hours

#         distance = geodesic(prev_coords, (lat, lon)).miles  # distance in miles

#         # print(f"Distance: {distance} miles, Time: {time_diff} hours")

#         speed = (
#             distance / time_diff
#             if time_diff > 0
#             else self.loc_history[vehicle].get("speed", 0)
#         )  # speed in mph

#         old_speed = self.loc_history[vehicle].get("speed", 0)

#         avg_speed = (speed + old_speed) / 2

#         self.loc_history[vehicle]["speed"] = avg_speed

#         return avg_speed
#         return speed
#     else:
#         self.loc_history[vehicle] = {"coords": (lat, lon), "time": timestamp}
#         return 0
