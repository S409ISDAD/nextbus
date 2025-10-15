from fastapi import APIRouter, Depends, HTTPException, Request
from backend.deps import get_redis, limiter
from backend.services import location, stops
from backend.schemas.location import LocationRequest
import traceback
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.post("/closest")
@limiter.limit("30/minute")
async def closest_stop(
    request: Request,
    body: LocationRequest,
    dist: float,
    ignore: str,
    limit: int = 1,
    redis=Depends(get_redis),
):
    try:
        # stop = await get_cached(
        #     f"closest_stop:{round(lat * 1000)}:{round(lon * 1000)}",
        #     lambda *args: bustimes.get_closest_stop(*args),
        #     (lat, lon),
        #     STOPS_CACHE,
        #     redis,
        # )

        return await stops.get_closest_stop(body.lat, body.lon, ignore, dist, limit)
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.post("/closestforservice")
@limiter.limit("15/minute")
async def closest_stop_for_service(
    request: Request,
    body: LocationRequest,
    dist: float,
    service_id: int,
    redis=Depends(get_redis),
):
    try:
        # stop = await get_cached(
        #     f"closest_stop:{round(lat * 1000)}:{round(lon * 1000)}",
        #     lambda *args: bustimes.get_closest_stop(*args),
        #     (lat, lon),
        #     STOPS_CACHE,
        #     redis,
        # )

        return await stops.get_closest_stop_for_service(
            body.lat, body.lon, service_id, redis, dist
        )
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        tb = traceback.format_exc()
        log.error(f"Unexpected error: {e}\n{tb}")
        raise HTTPException(500, detail=f"An unexpected error occurred: {e}")


@router.post("/nearby")
@limiter.limit("20/minute")
async def nearby_services(
    request: Request,
    body: LocationRequest,
    dist: int = 200,
):
    try:
        services = location.get_nearby_services(body.lat, body.lon, dist)

        for service in services:
            del service.geometry

        return services

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
