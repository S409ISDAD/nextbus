import asyncio
import datetime
import math
import time
from datetime import datetime as dt
from datetime import timedelta

from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.models.bus import TrackedBus
from backend.services import bus, stops

router = APIRouter()


@router.get("/")
async def departures_for_stop(stop_id: str, redis=Depends(get_redis)):
    buses: list[TrackedBus] = []

    services = await stops.get_services_from_stop(stop_id, redis)

    service_ids = [service.get("id") for service in services]

    stop_details = await stops.get_stop_details(stop_id, redis)

    stop_name = stop_details.get("name")

    times = await stops.get_times(stop_id, redis)

    buses = await bus.fetch_buses(service_ids, stop_id, times, redis)

    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = math.floor(
        dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
    )
    return {"stop_name": stop_name, "buses": buses, "timestamp": current_time}
