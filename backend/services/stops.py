from geopy.distance import geodesic
from backend.config import API_BASE, STOPS_BASE
from backend.services.caching import SERVICES_CACHE, STOPS_CACHE, get_cached
from backend.utils.fetch_json import fetch_json
from redis.asyncio import Redis


async def get_stop_details(stop_id, r: Redis):
    async def fetch(stop_id):
        data = await fetch_json(
            API_BASE + f"/stops/{stop_id}",
        )

        if not data:
            return

        return data

    stop_details = await get_cached(
        f"stops:{stop_id}",
        lambda *args: fetch(*args),
        (stop_id,),
        STOPS_CACHE,
        r,
    )

    return stop_details


async def get_services_from_stop(stop_id, r: Redis):
    """Fetches all services from a stop."""

    async def fetch(stop_id):
        data = await fetch_json(API_BASE + f"/services/?stops={stop_id}")

        if not data:
            return

        services = []
        ids = set()

        for service in data.get("results"):
            service_id = service.get("id")
            if service_id in ids:
                continue
            ids.add(service_id)
            services.append(
                {
                    "id": service_id,
                    "line_name": service.get("line_name"),
                    "detail": service.get("description"),
                }
            )

        return services

    services = await get_cached(
        key=f"services:{stop_id}",
        func=lambda *args: fetch(*args),
        args=(stop_id,),
        exp=SERVICES_CACHE,
        r=r,
    )

    return services


async def get_closest_stop(lat, lng, ignore, dist=0.005):
    xmin = lng - dist
    xmax = lng + dist
    ymin = lat - dist
    ymax = lat + dist

    stops = await fetch_json(
        STOPS_BASE + f"?ymax={ymax}&ymin={ymin}&xmax={xmax}&xmin={xmin}"
    )

    if not stops:
        return None

    closest_stop = None
    min_dist = float("inf")

    for stop in stops.get("features", []):
        stop_lat = stop["geometry"]["coordinates"][1]
        stop_lng = stop["geometry"]["coordinates"][0]

        dist = geodesic((lat, lng), (stop_lat, stop_lng)).meters

        if dist < min_dist and ignore != stop["properties"]["url"].split("/")[2]:
            min_dist = dist
            closest_stop = stop

    if closest_stop is None:
        return {"stop_id": "", "dist": 0, "lat": 0, "lng": 0}

    stop_id = closest_stop["properties"]["url"].split("/")[2]
    print(stop_id)

    return {
        "stop_id": stop_id,
        "dist": min_dist,
        "lat": closest_stop["geometry"]["coordinates"][0],
        "lng": closest_stop["geometry"]["coordinates"][1],
    }
