from backend.config import API_BASE, VEHICLES_BASE
from backend.schemas.service import Service
from backend.services.caching import SERVICE_CACHE, TRIPS_CACHE, get_cached
from backend.utils.fetch_json import fetch_json
from redis.asyncio import Redis

from backend.deps import get_logger

log = get_logger(__name__)


async def get_service_info(service, r: Redis):
    async def fetch(service):
        data = await fetch_json(API_BASE + f"/services/{service}")

        if not data:
            return None

        description_full = data.get("description", "")
        if "via" in description_full:
            desc, detail = description_full.split("via", 1)
            description = desc.strip()
            detail = detail.strip()
        else:
            description = description_full.strip()
            detail = ""

        return {
            "id": service,
            "line_name": data.get("line_name"),
            "description": description,
            "detail": detail,
        }

    service_info = await get_cached(
        f"service_info:{service}",
        fetch,
        (service,),
        SERVICE_CACHE,
        r,
    )

    return Service(
        id=service_info.get("id"),
        line_name=service_info.get("line_name"),
        description=service_info.get("description"),
        detail=service_info.get("detail"),
    )


async def fetch_active_buses(services, r: Redis):
    """Fetches all buses"""

    service_ids = ",".join(str(service) for service in services)

    async def fetch(services):
        data = await fetch_json(VEHICLES_BASE + f"?service={service_ids}")

        if not data:
            return None

        return data

    active = await get_cached(
        f"service:{service_ids}:trips",
        fetch,
        (services,),
        TRIPS_CACHE,
        r,
    )

    return active
