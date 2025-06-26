import asyncio
import datetime
import math
from datetime import datetime as dt
from datetime import timedelta

from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.services import bus, stops

router = APIRouter()


@router.get("/scheduled")
async def departures_scheduled(stop_id: str, redis=Depends(get_redis)):
    times = await stops.get_times(stop_id, redis)

    tasks = []
    for _time in times:
        tasks.append(bus.build_scheduled(_time, redis))

    buses = await asyncio.gather(*tasks)
    buses = [bus for bus in buses if bus is not None]

    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = math.floor(
        dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
    )
    return {"buses": buses, "timestamp": current_time}


@router.get("/live")
async def departures_live(stop_id: str, redis=Depends(get_redis)):
    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    buses = await bus.fetch_buses_live(service_ids, stop_id, redis)

    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = math.floor(
        dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
    )
    return {"buses": buses, "timestamp": current_time}


@router.get("/")
async def departures(stop_id: str, redis=Depends(get_redis)):
    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    times = await stops.get_times(stop_id, redis)

    buses = await bus.fetch_buses(service_ids, stop_id, times, redis)

    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = math.floor(
        dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
    )
    return {"buses": buses, "timestamp": current_time}
