import asyncio
import datetime
from datetime import datetime as dt, timedelta
import math
import time
from fastapi import APIRouter, Depends
from backend.models.bus import Bus
from backend.services import bustimes
from backend.deps import get_redis
from backend.services.caching import (
    get_cached,
    SERVICES_CACHE,
    STOPS_CACHE,
)

router = APIRouter()


@router.get("/")
async def departures_for_stop(stop_id: str, redis=Depends(get_redis)):
    start_time = time.time()
    buses: list[Bus] = []

    services = await get_cached(
        key=f"services:{stop_id}",
        func=lambda *args: bustimes.get_services_from_stop(*args),
        args=(stop_id,),
        exp=SERVICES_CACHE,
        r=redis,
    )

    stop_name = await get_cached(
        f"stops:{stop_id}",
        lambda *args: bustimes.get_stop_name(*args),
        (stop_id,),
        STOPS_CACHE,
        redis,
    )

    tasks = [
        bustimes.fetch_buses_for_service(service, stop_id, redis)
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
