import asyncio
from dateutil import parser
from redis.asyncio import Redis

from backend.config import VEHICLES_BASE
from backend.db.db import SessionLocal
from backend.deps import LONDON, UTC
from backend.models import (
    DirectionType,
    Journey,
    Line,
    StopTime,
)
from backend.schemas.livery import Livery
from backend.schemas.bus import ScheduledBus, TrackedBus
from backend.schemas.progress import Progress
from backend.services.caching import BUS_CACHE, get_cached
from backend.services.livery import get_livery
from backend.services.prediction import (
    calculate_expected,
    get_started_finished,
    predict_future,
)
from backend.services.services import fetch_active_buses, get_service_info
from backend.utils.fetch_json import fetch_json
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from backend.utils.match_bt import match_trip_journey


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


async def fetch_bus_trip(service_id, trip_id, r: Redis):
    """Fetches specific bus by service and trip"""

    async def fetch(service_id, trip_id):
        data = await fetch_json(VEHICLES_BASE + f"?service={service_id}&trip={trip_id}")
        if not data:
            return None

        exact_bus = [bus for bus in data if bus.get("trip_id") == trip_id]

        return exact_bus[0] if exact_bus else None

    this_bus = await get_cached(
        f"bus:{service_id}:{trip_id}",
        fetch,
        (service_id, trip_id),
        BUS_CACHE,
        r,
    )

    # if this_bus:
    #     await r.set(
    #         f"bus:{this_bus.get('id')}",
    #         value=json.dumps(
    #             {"data": this_bus},
    #             cls=DateTimeEncoder,
    #             default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o),
    #         ),
    #         ex=BUS_CACHE,
    #     )

    return this_bus


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


async def fetch_buses(
    services, stop_id, times, r: Redis, use_db=False, is_tomorrow=False
) -> list[TrackedBus]:
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
            with SessionLocal() as db:
                journey = await match_trip_journey(db, trip_id, r)
                journey_id = journey.id if journey else None
            use_db = journey_id is not None
            if use_db:
                tasks.append(
                    build_scheduled_db(stop_id, trip_id, journey_id, is_tomorrow, r)
                )
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
    scheduled = parser.isoparse(time.get("aimed_departure_time"))

    if time.get("expected_departure_time"):
        expected = parser.isoparse(time.get("expected_departure_time"))

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


async def build_scheduled_db(
    stop_id, trip_id, journey_id, is_tomorrow, r, include_started=True
):
    with SessionLocal() as db:
        stop_time: StopTime = (
            db.query(StopTime)
            .filter(StopTime.journey_id == journey_id, StopTime.stop_id == stop_id)
            .options(
                joinedload(StopTime.journey)
                .joinedload(Journey.line)
                .joinedload(Line.service)
            )
            .first()
        )

        if not stop_time:
            return None

        if include_started:
            started, finished = await get_started_finished(trip_id, r)
        else:
            started = False

        today = datetime.today().astimezone(LONDON)
        if is_tomorrow:
            today += timedelta(days=1)

        today_midnight = datetime.combine(today, datetime.min.time()).astimezone(LONDON)
        scheduled = today_midnight + stop_time.departure_time

        if (scheduled - datetime.now(tz=LONDON)).total_seconds() > 11 * 3600:
            return None

        dest = (
            stop_time.journey.line.service.destination
            if stop_time.journey.direction == DirectionType.outbound
            else stop_time.journey.line.service.origin
        )

        scheduled_bus = ScheduledBus(
            destination=dest,
            line=stop_time.journey.line.line_name,
            scheduled=scheduled,
            expected=scheduled,
            started=started,
            trip=trip_id,
            status="not_tracking",
        )

        prev_journey = stop_time.journey.get_previous_journey(db, today.date())

        if not prev_journey:
            return scheduled_bus

        layover_time = (
            stop_time.journey.start_time - prev_journey.end_time
            if prev_journey
            else timedelta(0)
        )

        prev_trip = await prev_journey.get_bt_trip_id(db)

        prev_service_id = await prev_journey.line.get_bt_service_id(db)
        this_service_id = await stop_time.journey.line.get_bt_service_id(db)

        if not prev_trip or not prev_service_id or not this_service_id:
            return scheduled_bus

        service_info = await get_service_info(this_service_id, r)

        potential_bus = await fetch_bus_trip(prev_service_id, prev_trip, r)

        if potential_bus:
            print("Found bus from previous trip")

            bus = await build_bus(potential_bus["id"], r, get_journey=False)
            if not bus:
                print("Failed to build bus")
            else:
                delay = max(
                    bus.delay - int(layover_time.total_seconds()), 0
                )  # account for layover
                bus.destination = dest
                bus.scheduled = scheduled
                bus.expected = scheduled + timedelta(seconds=delay)
                bus.delay = delay
                bus.trip = trip_id
                bus.started = started
                bus.status = "on_prev_trip"
                service = service_info if service_info else bus.service
                bus.service = service

                # Don't show if expected is more than 2 hours away
                if (bus.expected - datetime.now(tz=LONDON)).total_seconds() < 4 * 3600:
                    return bus
                print("Bus expected too far in future")

        return ScheduledBus(
            destination=dest,
            line=stop_time.journey.line.line_name,
            scheduled=scheduled,
            expected=scheduled,
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

    tracking = True

    if not delay:
        delay = 0
        tracking = False

    # Ignore buses with a delay of over 2 hours, they are likely broken down or similar
    if delay > 2 * 60 * 60:
        print(f"ignoring bus with delay of {round(delay / 60)} minutes")
        return None

    await r.sadd("total_buses", bus_id)

    timestamp = this_bus.get("datetime")

    coords = this_bus.get("coordinates", [0, 0])
    vehicle = this_bus.get("vehicle", {})
    journey_id = this_bus.get("journey_id")
    destination = this_bus.get("destination")
    progress = this_bus.get("progress", {})

    vehicle_name = vehicle.get("name", "").split(" - ")
    fleet_num = vehicle_name[0] if len(vehicle_name) > 1 else "Unknown"
    reg = vehicle_name[-1]
    bus_type = vehicle.get("features", "")
    if not bus_type:
        bus_type = "Single decker"
    elif "double" not in bus_type.lower():
        bus_type = f"Single decker, {bus_type}"
    if bus_type:
        bus_type = bus_type.replace("<br>", ", ")
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

    target_seq, times, journey = await calculate_expected(
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

    status = "tracking"

    if not tracking:
        status = "not_tracking"
    if not times.started:
        status = "waiting"

    return TrackedBus(
        type="tracked",
        id=bus_id,
        service=service_info,
        trip=this_bus.get("trip_id", 0),
        timestamp=timestamp,
        destination=destination,
        reg=reg,
        bus_type=bus_type,
        fleet_num=fleet_num,
        journey_id=journey_id,
        delay=delay,
        expected=times.expected,
        scheduled=times.scheduled,
        started=times.started,
        finished=times.finished,
        target_seq=target_seq,
        progress=progress
        if progress
        else Progress(sequence=0, next_stop="", prev_stop="", progress=0),
        predictions=predictions,
        journey=journey,
        livery=livery,
        speed=None,
        coords=coords,
        status=status,
    )
