import datetime
from datetime import datetime as dt, timedelta
import math
from fastapi import APIRouter, Depends
from backend.services import bustimes
from backend.deps import get_redis
from backend.services.caching import (
    get_cached,
    SERVICES_CACHE,
    STOPS_CACHE,
)

router = APIRouter()


@router.get("/")
async def stop_details(stop_id: str, redis=Depends(get_redis)):
    services = await get_cached(
        key=f"services:{stop_id}",
        func=lambda *args: bustimes.get_services_from_stop(*args),
        args=(stop_id,),
        exp=SERVICES_CACHE,
        r=redis,
    )

    stop_details = await get_cached(
        f"stops:{stop_id}",
        lambda *args: bustimes.get_stop_details(*args),
        (stop_id,),
        STOPS_CACHE,
        redis,
    )

    return {
        "name": stop_details.get("name"),
        "long_name": stop_details.get("long_name"),
        "active": stop_details.get("active"),
        "coords": stop_details.get("location"),
        "indicator": stop_details.get("indicator", ""),
        "bearing": stop_details.get("bearing", ""),
        "services": services,
    }
