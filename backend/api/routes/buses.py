from fastapi import APIRouter, Depends
from backend.services import bustimes
from backend.deps import get_redis
from backend.services.caching import get_cached, BUS_CACHE

router = APIRouter()


@router.get("/")
async def get_bus(bus_id: int, redis=Depends(get_redis)):
    bus = await get_cached(
        f"bus:{bus_id}",
        lambda *args: bustimes.fetch_bus(*args),
        (bus_id,),
        BUS_CACHE,
        redis,
    )

    return bus
