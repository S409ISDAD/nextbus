import asyncio
from dateutil import parser
from redis.asyncio import Redis

from backend.config import VEHICLES_BASE
from backend.models.livery import Livery
from backend.models.bus import ScheduledBus, TrackedBus
from backend.services.caching import BUS_CACHE, get_cached
from backend.services.livery import get_livery
from backend.services.prediction import (
    calculate_expected,
    get_started_finished,
    predict_future,
)
from backend.services.services import fetch_active_buses, get_service_info
from backend.utils.fetch_json import fetch_json


async def fetch_bus(bus_id, r: Redis):
    """Fetches specific bus"""

    async def fetch(bus_id):
        data = await fetch_json(VEHICLES_BASE + f"?id={bus_id}")

        return data

    this_bus = await get_cached(
        f"bus:{bus_id}",
        fetch,
        (bus_id,),
        BUS_CACHE,
        r,
    )

    try:
        return this_bus[0]
    except:  # noqa: E722
        return None


def best_bus(buses: list[dict]) -> dict | None:
    valid = []

    for bus in buses:
        progress = bus.get("progress")
        if progress and isinstance(progress.get("sequence"), int):
            print("valid")
            valid.append(bus)

    if not valid:
        return None

    return max(valid, key=lambda b: b["progress"]["sequence"])


async def fetch_buses(services, stop_id, times, r: Redis) -> list[TrackedBus]:
    active = await fetch_active_buses(services, r)

    active_by_trip: dict[int, list[dict]] = {}
    if active:
        for bus in active:
            trip_id = bus.get("trip_id")
            if trip_id:
                active_by_trip.setdefault(trip_id, []).append(bus)

    tasks = []

    for time in times:
        trip_id = time.get("trip_id")
        matched_buses = active_by_trip.get(trip_id, [])

        if matched_buses:
            tasks.append(build_bus_candidates(matched_buses, r, stop_id))
        else:
            tasks.append(build_scheduled(time, r))

    buses = await asyncio.gather(*tasks)
    return [bus for bus in buses if bus is not None]


async def fetch_buses_live(services, stop_id, r: Redis) -> list[TrackedBus]:
    active = await fetch_active_buses(services, r)

    if not active:
        return []

    active_by_trip: dict[int, list[dict]] = {}

    for bus in active:
        trip_id = bus.get("trip_id")
        if trip_id:
            active_by_trip.setdefault(trip_id, []).append(bus)

    tasks = []

    for trip, buses in active_by_trip.items():
        tasks.append(build_bus_candidates(buses, r, stop_id))

    buses = await asyncio.gather(*tasks)
    return [bus for bus in buses if bus is not None]


async def build_scheduled(time, r, include_started=True):
    scheduled = int(parser.isoparse(time.get("aimed_departure_time")).timestamp())
    if time.get("expected_departure_time"):
        expected = int(parser.isoparse(time.get("expected_departure_time")).timestamp())
    else:
        expected = scheduled

    destination = time.get("destination").get("locality")
    line = time.get("service").get("line_name")

    trip_id = time.get("trip_id")

    if include_started:
        started, finished = await get_started_finished(trip_id, r)
    else:
        started = False

    return ScheduledBus(
        destination=destination,
        line=line,
        scheduled=scheduled,
        expected=expected,
        started=started,
        trip=trip_id,
        status="not_tracking",
    )


async def build_bus_candidates(
    buses: list[dict], r: Redis, stop_id: str
) -> TrackedBus | None:
    results = await asyncio.gather(
        *[build_bus(bus["id"], r, stop_id, get_journey=False) for bus in buses]
    )

    valid = [
        bus
        for bus in results
        if bus is not None
        and hasattr(bus, "progress")
        and isinstance(bus.progress.sequence, int)
    ]

    if not valid:
        return None

    # Return the one with the highest progress.sequence
    return max(valid, key=lambda b: b.progress.sequence)


async def build_bus(
    bus_id: int,
    r: Redis,
    stop_id: str = "",
    get_journey: bool = True,
) -> TrackedBus | None:
    this_bus = await fetch_bus(bus_id, r)

    if not this_bus:
        return None

    delay = this_bus.get("delay")

    if not delay:
        return None

    timestamp = (
        int(parser.isoparse(this_bus.get("datetime")).timestamp())
        if this_bus.get("datetime")
        else None
    )

    coords = this_bus.get("coordinates", [0, 0])
    vehicle = this_bus.get("vehicle", {})
    journey_id = this_bus.get("journey_id")
    destination = this_bus.get("destination")
    progress = this_bus.get("progress", {})

    vehicle_name = vehicle["name"].split(" - ")
    fleet_num = vehicle_name[0] if len(vehicle_name) > 1 else "Unknown"
    reg = vehicle_name[-1]

    livery_id = vehicle.get("livery")

    if livery_id:
        livery = await get_livery(livery_id, r)
    else:
        css = vehicle.get("css")
        if css:
            livery = Livery(name="Livery:", css=css)
        else:
            livery = None

    # journey = await get_vehicle_journey(bus_id, journey_id, r)

    delay += 10  # account for stopping and various other things that increase delay

    times, journey = await calculate_expected(
        delay, progress.get("sequence", 0), stop_id, journey_id, r
    )

    service_info = await get_service_info(journey.service_id, r)

    if not times:
        return None
    if not times.include:
        return None

    if times.finished and stop_id:
        return None

    if not times.started:
        delay = 0

    if get_journey:
        predictions = await predict_future(
            journey, delay, timestamp, times.started, 35, r
        )
    else:
        predictions = []

    return TrackedBus(
        id=bus_id,
        service=service_info,
        trip=this_bus.get("trip_id", 0),
        timestamp=timestamp,
        destination=destination,
        reg=reg,
        fleet_num=fleet_num,
        journey_id=journey_id,
        delay=delay,
        expected=times.expected,
        scheduled=times.scheduled,
        started=times.started,
        finished=times.finished,
        progress=progress,
        predictions=predictions,
        journey=journey,
        livery=livery,
        speed=None,
        coords=coords,
        status="tracking",
    )
