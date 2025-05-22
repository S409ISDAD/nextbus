import asyncio
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
    buses: list[Bus] = []

    services = await get_cached(
        f"services:{stop_id}",
        lambda a: bustimes.get_services_from_stop(a),
        (stop_id),
        SERVICES_CACHE,
        redis,
    )

    stop_name = await get_cached(
        f"stops:{stop_id}",
        lambda a: bustimes.get_stop_name(a),
        (stop_id),
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

    return {"stop_name": stop_name, "buses": buses, "timestamp": buses[0].timestamp}
