import asyncio
from typing import Optional
from dateutil import parser
from redis.asyncio import Redis

from backend.config import VEHICLES_BASE
from backend.models.livery import Livery
from backend.models.trackedbus import TrackedBus
from backend.services.caching import BUS_CACHE, get_cached
from backend.services.livery import get_livery
from backend.services.prediction import calculate_expected, predict_future
from backend.services.services import fetch_active_buses, get_service_info
from backend.utils.fetch_json import fetch_json


async def fetch_bus(bus_id, r: Redis):
    """Fetches specific bus"""

    async def fetch(bus_id):
        data = await fetch_json(VEHICLES_BASE + f"?id={bus_id}")

        return data

    this_bus = await get_cached(
        f"bus:{bus_id}",
        lambda *args: fetch(*args),
        (bus_id,),
        BUS_CACHE,
        r,
    )

    try:
        return this_bus[0]
    except:
        return None


async def fetch_buses(services, stop_id, r: Redis) -> list[TrackedBus]:
    active = await fetch_active_buses(services, r)

    if not active:
        return []

    tasks = [
        build_bus(bus.get("id"), r, stop_id, get_journey=False)
        for bus in active
        if bus.get("id") is not None
    ]

    buses = await asyncio.gather(*tasks)

    return [bus for bus in buses if bus is not None]


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
        parser.isoparse(this_bus.get("datetime")) if this_bus.get("datetime") else None
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
        delay, progress.get("sequence", 0), stop_id, bus_id, journey_id, r
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
