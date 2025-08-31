from geopy.distance import geodesic
from backend.config import API_BASE, BASE, STOPS_BASE
from backend.schemas.stop import Stop
from backend.schemas.service import Service
from backend.services.caching import (
    SERVICES_CACHE,
    STOPS_CACHE,
    TRIPS_CACHE,
    get_cached,
)
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
        fetch,
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
            description_full = service.get("description", "")
            if "via" in description_full:
                desc, detail = description_full.split("via", 1)
                description = desc.strip()
                detail = detail.strip()
            else:
                description = description_full.strip()
                detail = ""

            services.append(
                {
                    "id": service_id,
                    "line_name": service.get("line_name"),
                    "description": description,
                    "detail": detail,
                }
            )

        return services

    services = await get_cached(
        key=f"services:{stop_id}",
        func=fetch,
        args=(stop_id,),
        exp=SERVICES_CACHE,
        r=r,
    )

    return services


async def get_times(stop_id, r: Redis):
    """Fetches departures from a stop."""

    async def fetch(stop_id):
        data = await fetch_json(BASE + f"/stops/{stop_id}/times.json")

        if not data:
            return

        return data.get("times")

    times = await get_cached(
        key=f"times:{stop_id}",
        func=fetch,
        args=(stop_id,),
        exp=TRIPS_CACHE,
        r=r,
    )

    return times


async def get_nearby_stops(lat, lng, dist=0.005):
    xmin = lng - dist
    xmax = lng + dist
    ymin = lat - dist
    ymax = lat + dist

    stops = await fetch_json(
        STOPS_BASE + f"?ymax={ymax}&ymin={ymin}&xmax={xmax}&xmin={xmin}"
    )

    if not stops:
        return []

    nearby_stops = []
    for stop in stops.get("features", []):
        stop_lat = stop["geometry"]["coordinates"][1]
        stop_lng = stop["geometry"]["coordinates"][0]

        bearing = stop["properties"].get("bearing", None)
        indicator = stop["properties"].get("indicator", "")

        nearby_stops.append(
            Stop(
                stop_id=stop["properties"]["url"].split("/")[2],
                coords=[stop_lng, stop_lat],
                long_name="",
                name=stop["properties"]["name"],
                indicator=indicator,
                bearing=bearing,
                active=stop["properties"].get("active", True),
                services=None,  # Services will be fetched separately if needed
            )
        )

    return nearby_stops


async def get_closest_stop(lat, lng, ignore, dist=0.005):
    stops = await get_nearby_stops(lat, lng, dist)

    closest_stop = None
    min_dist = float("inf")

    for stop in stops:
        stop_lat = stop.coords[1]
        stop_lng = stop.coords[0]

        dist = geodesic((lat, lng), (stop_lat, stop_lng)).meters

        if dist < min_dist and ignore != stop.stop_id:
            min_dist = dist
            closest_stop = stop

    if closest_stop is None:
        return {"stop_id": "", "dist": 0, "lat": 0, "lng": 0}

    stop_id = closest_stop.stop_id
    print(stop_id)

    return {
        "stop_id": stop_id,
        "dist": min_dist,
        "lat": closest_stop.coords[1],
        "lng": closest_stop.coords[0],
    }


async def get_nearby_services(lat, lng, r, dist=0.005):
    stops = await get_nearby_stops(lat, lng, dist)

    nearby_services = []
    seen_services = set()

    for stop in stops:
        stop_lat = stop.coords[1]
        stop_lng = stop.coords[0]

        dist = geodesic((lat, lng), (stop_lat, stop_lng)).meters

        stop_id = stop.stop_id

        services = await get_services_from_stop(stop_id, r=r)

        if not services:
            continue

        for service in services:
            service_id = service.get("id")
            if service_id in seen_services:
                continue
            seen_services.add(service_id)

            nearby_service = Service(
                id=service_id,
                line_name=service.get("line_name"),
                detail=service.get("detail"),
            )
            nearby_services.append(nearby_service)

    if not nearby_services:
        return []

    return nearby_services


async def get_closest_stop_for_service(lat, lng, service_id, r, dist=0.005):
    stops = await get_nearby_stops(lat, lng, dist)

    closest_stop = None
    min_dist = float("inf")

    for stop in stops:
        stop_lat = stop.coords[1]
        stop_lng = stop.coords[0]

        dist = geodesic((lat, lng), (stop_lat, stop_lng)).meters

        stop_id = stop.stop_id

        services = await get_services_from_stop(stop_id, r=r)

        if not services:
            continue

        service_ids = {service.get("id") for service in services}
        if service_id in service_ids:
            if dist < min_dist:
                min_dist = dist
                closest_stop = stop

    if not closest_stop:
        return None

    return {
        "stop_id": closest_stop.stop_id,
        "dist": min_dist,
        "lat": closest_stop.coords[1],
        "lng": closest_stop.coords[0],
    }
