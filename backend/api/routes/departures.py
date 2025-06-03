import asyncio
import datetime
import math
import time
from datetime import datetime as dt
from datetime import timedelta

from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.models.trackedbus import TrackedBus
from backend.services import bus, stops

router = APIRouter()


@router.get("/")
async def departures_for_stop(stop_id: str, redis=Depends(get_redis)):
    start_time = time.time()
    buses: list[TrackedBus] = []

    services = await stops.get_services_from_stop(stop_id, redis)

    stop_details = await stops.get_stop_details(stop_id, redis)

    stop_name = stop_details.get("name")

    tasks = [
        bus.fetch_buses_for_service(service.get("id"), stop_id, redis)
        for service in services
    ]
    for task in asyncio.as_completed(tasks):
        result = await task
        buses.extend(result)
    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = math.floor(
        dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
    )
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"took {round(elapsed, 2)}s")
    return {"stop_name": stop_name, "buses": buses, "timestamp": current_time}
