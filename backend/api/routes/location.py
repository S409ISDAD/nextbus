from fastapi import APIRouter, Depends, HTTPException, Request
import logging
from backend.deps import get_redis, limiter
from backend.schemas.service import Service
from backend.services import stops
import traceback

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/closest")
@limiter.limit("30/minute")
async def closest_stops(
    request: Request,
    lat: float,
    lng: float,
    dist: float,
    ignore: str,
    redis=Depends(get_redis),
):
    try:
        # stop = await get_cached(
        #     f"closest_stop:{round(lat * 1000)}:{round(lng * 1000)}",
        #     lambda *args: bustimes.get_closest_stop(*args),
        #     (lat, lng),
        #     STOPS_CACHE,
        #     redis,
        # )

        return await stops.get_closest_stop(lat, lng, ignore, dist)
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/closestforservice")
@limiter.limit("15/minute")
async def closest_stop_for_service(
    request: Request,
    lat: float,
    lng: float,
    dist: float,
    service_id: int,
    redis=Depends(get_redis),
):
    try:
        # stop = await get_cached(
        #     f"closest_stop:{round(lat * 1000)}:{round(lng * 1000)}",
        #     lambda *args: bustimes.get_closest_stop(*args),
        #     (lat, lng),
        #     STOPS_CACHE,
        #     redis,
        # )

        return await stops.get_closest_stop_for_service(
            lat, lng, service_id, redis, dist
        )
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        tb = traceback.format_exc()
        log.error(f"Unexpected error: {e}\n{tb}")
        raise HTTPException(500, detail=f"An unexpected error occurred: {e}")


@router.get("/nearby", response_model=list[Service] | None)
@limiter.limit("10/minute")
async def nearby_services(
    request: Request,
    lat: float,
    lng: float,
    dist: float,
    redis=Depends(get_redis),
):
    try:
        # stop = await get_cached(
        #     f"closest_stop:{round(lat * 1000)}:{round(lng * 1000)}",
        #     lambda *args: bustimes.get_closest_stop(*args),
        #     (lat, lng),
        #     STOPS_CACHE,
        #     redis,
        # )

        return await stops.get_nearby_services(lat, lng, redis, dist)

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
