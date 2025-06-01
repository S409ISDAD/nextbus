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
from geopy.distance import geodesic


BASE = "https://bustimes.org"
VEHICLES_BASE = BASE + "/vehicles.json"
STOPS_BASE = BASE + "/stops.json"
API_BASE = BASE + "/api/"


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

        if not bus_id:
            continue

        this_bus = await get_cached(
            f"bus:{bus_id}",
            lambda *args: fetch_bus(*args),
            (bus_id,),
            BUS_CACHE,
            r,
        )

        try:
            this_bus = this_bus[0]
        except TypeError:
            continue

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

        times = await calculate_expected(delay, stop_id, bus_id, journey_id, r)

        if times:
            buses.append(
                Bus(
                    id=bus_id,
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
    data = await fetch_json(VEHICLES_BASE + f"?id={bus_id}")

    return data


async def get_services_from_stop(stop_id):
    """Fetches all services from a stop."""
    data = await fetch_json(API_BASE + f"services/?stops={stop_id}")

    if not data:
        return

    services = []
    ids = set()

    for service in data.get("results"):
        service_id = service.get("id")
        if service_id in ids:
            continue
        ids.add(service_id)
        services.append(
            {
                "id": service_id,
                "line_name": service.get("line_name"),
                "detail": service.get("description"),
            }
        )

    return services


async def fetch_active_buses(service):
    """Fetches all buses on the route"""
    data = await fetch_json(VEHICLES_BASE + f"?service={service}")

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


async def get_stop_details(stop_id):
    data = await fetch_json(
        API_BASE + f"stops/{stop_id}",
    )

    if not data:
        return

    return data


async def get_vehicle_journey(bus_id, journey_id):
    data = await fetch_json(
        BASE + f"/vehicles/{bus_id}/journeys/{journey_id}.json",
    )

    if not data:
        return

    uk_timezone = datetime.timezone(timedelta(hours=1))
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

            data["stops"][i]["aimed_time"] = check_scheduled_time(
                scheduled_time, current_time
            ).timestamp()

        actual_departure = data["stops"][i].get("actual_departure_time")
        if actual_departure:
            departure_time = parser.isoparse(actual_departure)

            data["stops"][i]["actual_time"] = departure_time.timestamp()

    return data


def check_scheduled_time(scheduled: dt, current_time: dt) -> dt:
    time_difference = (scheduled - current_time).total_seconds()

    # time is more than 6h in the future so bus is most likely yesterday, subtract 1 day
    if time_difference / 3600 > 6:
        scheduled -= timedelta(days=1)

    # time is more than 6h in the past so bus is most likely tomorrow, add 1 day
    elif time_difference / 3600 < -6:
        scheduled += timedelta(days=1)

    return scheduled


async def calculate_expected(delay, stop_id, bus_id, journey_id, r):
    journey = await get_cached(
        f"journeys:{bus_id}:{journey_id}",
        lambda *args: get_vehicle_journey(*args),
        (bus_id, journey_id),
        JOURNEY_CACHE,
        r,
    )

    stops = journey.get("stops")
    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    not_started = False

    stop_idx = 0

    for stop_time in stops:
        if stop_idx == 0:
            aimed = stop_time.get("aimed_time")
            scheduled_time = dt.fromtimestamp(aimed).astimezone(uk_timezone)

            if scheduled_time > current_time:
                not_started = True

        if stop_time.get("atco_code") == stop_id:
            aimed = stop_time.get("aimed_time")
            if not aimed:
                return None
            scheduled_time = dt.fromtimestamp(aimed).astimezone(uk_timezone)

            if not_started:
                delay = 0

            expected_time = scheduled_time + timedelta(seconds=delay)

            if expected_time < current_time:
                return None

            return {
                "expected": expected_time.timestamp(),
                "scheduled": scheduled_time.timestamp(),
                "not_started": not_started,
            }
        stop_idx += 1

    return None


async def get_closest_stop(lat, lng):
    buffer = 0.005

    xmin = lng - buffer
    xmax = lng + buffer
    ymin = lat - buffer
    ymax = lat + buffer

    stops = await fetch_json(
        STOPS_BASE + f"?ymax={ymax}&ymin={ymin}&xmax={xmax}&xmin={xmin}"
    )

    if not stops:
        return None

    closest_stop = None
    min_dist = float("inf")

    for stop in stops.get("features", []):
        stop_lat = stop["geometry"]["coordinates"][1]
        stop_lng = stop["geometry"]["coordinates"][0]

        dist = geodesic((lat, lng), (stop_lat, stop_lng)).meters

        if dist < min_dist:
            min_dist = dist
            closest_stop = stop

    if closest_stop is None:
        return {"stop_id": "", "dist": 0, "lat": 0, "lng": 0}

    stop_id = closest_stop["properties"]["url"].split("/")[2]
    print(stop_id)

    return {
        "stop_id": stop_id,
        "dist": min_dist,
        "lat": closest_stop["geometry"]["coordinates"][0],
        "lng": closest_stop["geometry"]["coordinates"][1],
    }


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
