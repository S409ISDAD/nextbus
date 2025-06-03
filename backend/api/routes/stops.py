from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.models.stop import Stop
from backend.services import stops

router = APIRouter()


@router.get("/")
async def stop_details(stop_id: str, redis=Depends(get_redis)) -> Stop:
    services = await stops.get_services_from_stop(stop_id, redis)

    stop_details = await stops.get_stop_details(stop_id, redis)

    location = stop_details.get("location")
    try:
        coords = list(location)
    except TypeError:
        coords = [0.0, 0.0]
    coords.reverse()

    return Stop(
        stop_id=stop_id,
        name=stop_details.get("name"),
        long_name=stop_details.get("long_name"),
        active=stop_details.get("active"),
        coords=coords,
        indicator=stop_details.get("indicator", ""),
        bearing=stop_details.get("bearing", ""),
        services=services,
    )
