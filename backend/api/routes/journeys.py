from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.services import journeys
from backend.services import bus
from backend.services.caching import BUS_CACHE, get_cached

router = APIRouter()


@router.get("/")
async def get_journey(bus_id: int, journey_id: int, redis=Depends(get_redis)):
    this_bus = await bus.fetch_bus(bus_id, redis)

    if not this_bus:
        return None

    journey = await journeys.get_vehicle_journey(
        bus_id, journey_id, this_bus.get("delay"), redis
    )

    return journey
