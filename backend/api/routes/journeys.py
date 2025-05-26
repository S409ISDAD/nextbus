from fastapi import APIRouter, Depends
from backend.services import bustimes
from backend.deps import get_redis
from backend.services.caching import get_cached, BUS_CACHE

router = APIRouter()


@router.get("/")
async def get_journey(bus_id: int, journey_id: int, redis=Depends(get_redis)):
    journey = await get_cached(
        key=f"journeys:{bus_id}:{journey_id}",
        func=lambda *args: bustimes.get_vehicle_journey(*args),
        args=(bus_id, journey_id),
        exp=BUS_CACHE,
        r=redis,
    )

    return journey
