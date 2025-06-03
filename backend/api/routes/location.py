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
    STOPS_CACHE,
)

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

    return await bustimes.get_closest_stop(lat, lng, ignore)
