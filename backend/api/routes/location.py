from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.services import stops

router = APIRouter()


@router.get("/closest")
async def closest_stops(lat: float, lng: float, ignore: str, redis=Depends(get_redis)):
    # stop = await get_cached(
    #     f"closest_stop:{round(lat * 1000)}:{round(lng * 1000)}",
    #     lambda *args: bustimes.get_closest_stop(*args),
    #     (lat, lng),
    #     STOPS_CACHE,
    #     redis,
    # )

    return await stops.get_closest_stop(lat, lng, ignore)
