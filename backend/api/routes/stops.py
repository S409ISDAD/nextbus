from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import get_redis, limiter
from backend.schemas.stop import Stop
from backend.services import stops
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.get("/", response_model=Stop)
@limiter.limit("90/minute")
async def stop_details(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        if not stop_id:
            raise HTTPException(400, detail="stop_id is required")
        services = await stops.get_services_from_stop(stop_id, redis)

        stop_details = await stops.get_stop_details(stop_id, redis)

        location = stop_details.get("location")
        try:
            coords = list(location)
        except TypeError:
            coords = [0.0, 0.0]
        coords.reverse()

        bearing = stop_details.get("bearing", None)
        if bearing in (None, ""):
            bearing = None
        elif isinstance(bearing, int):
            pass
        elif isinstance(bearing, str) and bearing.isnumeric():
            bearing = int(bearing)
        else:
            bearing = None

        return Stop(
            stop_id=stop_id,
            name=stop_details.get("name"),
            long_name=stop_details.get("long_name"),
            active=stop_details.get("active"),
            coords=coords,
            indicator=stop_details.get("indicator", ""),
            bearing=bearing,
            services=services,
            dist=0,
        )

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
