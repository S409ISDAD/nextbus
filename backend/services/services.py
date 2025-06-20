from backend.config import API_BASE, VEHICLES_BASE
from backend.models.service import Service
from backend.services.caching import SERVICE_CACHE, TRIPS_CACHE, get_cached
from backend.utils.fetch_json import fetch_json
from redis.asyncio import Redis


async def get_service_info(service, r: Redis):
    async def fetch(service):
        data = await fetch_json(API_BASE + f"/services/{service}")

        if not data:
            return None

        return {
            "id": service,
            "line_name": data.get("line_name"),
            "detail": data.get("description").split("via")[1].lstrip()
            if "via" in data.get("description")
            else "",
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
