from fastapi import APIRouter, Depends, Request

from backend.deps import get_redis, limiter
from backend.services import stops

router = APIRouter()


@router.get("/closest")
@limiter.limit("5/minute")
async def closest_stops(
    request: Request,
    lat: float,
    lng: float,
    dist: float,
    ignore: str,
    redis=Depends(get_redis),
):
    # stop = await get_cached(
    #     f"closest_stop:{round(lat * 1000)}:{round(lng * 1000)}",
    #     lambda *args: bustimes.get_closest_stop(*args),
    #     (lat, lng),
    #     STOPS_CACHE,
    #     redis,
    # )

    return await stops.get_closest_stop(lat, lng, ignore, dist)
