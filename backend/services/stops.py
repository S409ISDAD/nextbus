from datetime import datetime, timedelta
from geopy.distance import geodesic
from redis import Redis

from backend.config import API_BASE, BASE, STOPS_BASE
from backend.deps import LONDON
from backend.schemas.service import Service
from backend.schemas.stop import Stop
from backend.services.caching import (
    SERVICES_CACHE,
    STOPS_CACHE,
    TRIPS_CACHE,
    get_cached,
)
from dateutil.parser import isoparse
from backend.utils.fetch_json import fetch_json

from backend.deps import get_logger

log = get_logger(__name__)


def get_stop_details(stop_id, r: Redis):
    def fetch(stop_id):
        data = fetch_json(
            API_BASE + f"/stops/{stop_id}",
        )

        if not data:
            return

        return data

    stop_details = get_cached(
        f"stops:{stop_id}",
        fetch,
        (stop_id,),
        STOPS_CACHE,
        r,
    )

    return stop_details


def get_services_from_stop(stop_id, r: Redis):
    """Fetches all services from a stop."""

    def fetch(stop_id):
        data = fetch_json(API_BASE + f"/services/?stops={stop_id}")

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

    services = get_cached(
        key=f"services:{stop_id}",
        func=fetch,
        args=(stop_id,),
        exp=SERVICES_CACHE,
        r=r,
    )

    return services


def get_times(stop_id, r: Redis):
    """Fetches departures from a stop."""

    def fetch(stop_id):
        now = datetime.now(tz=LONDON)

        data = fetch_json(BASE + f"/stops/{stop_id}/times.json")

        if not data:
            return

        times = data.get("times", [])

        for time in times:
            dep = time.get("expected_departure_time")
            time["dayshift"] = 0

            if dep:
                dep = isoparse(dep)
                if dep.date() > now.date():
                    time["dayshift"] = 1

        return times

    times = get_cached(
        key=f"times:{stop_id}",
        func=fetch,
        args=(stop_id,),
        exp=TRIPS_CACHE,
        r=r,
    )

    return times


def get_nearby_stops(lat, lon, dist=0.005):
    xmin = lon - dist
    xmax = lon + dist
    ymin = lat - dist
    ymax = lat + dist

    stops = fetch_json(STOPS_BASE + f"?ymax={ymax}&ymin={ymin}&xmax={xmax}&xmin={xmin}")

    if not stops:
        return []

    nearby_stops = []
    for stop in stops.get("features", []):
        stop_lat = stop["geometry"]["coordinates"][1]
        stop_lon = stop["geometry"]["coordinates"][0]

        bearing = stop["properties"].get("bearing", None)
        indicator = stop["properties"].get("indicator", "")

        dist = geodesic((lat, lon), (stop_lat, stop_lon)).meters

        nearby_stops.append(
            Stop(
                stop_id=stop["properties"]["url"].split("/")[2],
                coords=[stop_lon, stop_lat],
                long_name="",
                name=stop["properties"]["name"],
                indicator=indicator,
                bearing=bearing,
                active=stop["properties"].get("active", True),
                services=None,  # Services will be fetched separately if needed
                dist=dist,
            )
        )

    return nearby_stops


def get_closest_stop(lat, lon, ignore, dist=0.005, limit=1):
    stops = get_nearby_stops(lat, lon, dist)

    closest_stops = []

    for stop in stops:
        stop_lat = stop.coords[1]
        stop_lon = stop.coords[0]

        dist = geodesic((lat, lon), (stop_lat, stop_lon)).meters

        if ignore != stop.stop_id:
            closest_stops.append(
                {
                    "stop_id": stop.stop_id,
                    "dist": stop.dist,
                    "lat": stop_lat,
                    "lon": stop_lon,
                    "active_now": True,
                }
            )

    if closest_stops is None:
        return {"stop_id": "", "dist": 0, "lat": 0, "lon": 0}

    # r = get_redis()

    closest_stops.sort(key=lambda x: x["dist"])
    closest_stops = closest_stops[:limit]

    # for stop in closest_stops:
    #     times, _ = get_scheduled(stop["stop_id"], r)
    #     if not times or len(times) == 0:
    #         stop["active_now"] = False  # no upcoming departures
    return closest_stops


def get_nearby_services(lat, lon, r, dist=0.005):
    stops = get_nearby_stops(lat, lon, dist)

    nearby_services = []
    seen_services = set()

    for stop in stops:
        stop_lat = stop.coords[1]
        stop_lon = stop.coords[0]

        dist = geodesic((lat, lon), (stop_lat, stop_lon)).meters

        stop_id = stop.stop_id

        services = get_services_from_stop(stop_id, r=r)

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
                description=service.get("description"),
                detail=service.get("detail"),
            )
            nearby_services.append(nearby_service)

    if not nearby_services:
        return []

    return nearby_services


def get_closest_stop_for_service(lat, lon, service_id, r, dist=0.005):
    stops = get_nearby_stops(lat, lon, dist)

    closest_stop = None
    min_dist = float("inf")

    for stop in stops:
        stop_lat = stop.coords[1]
        stop_lon = stop.coords[0]

        dist = geodesic((lat, lon), (stop_lat, stop_lon)).meters

        stop_id = stop.stop_id

        services = get_services_from_stop(stop_id, r=r)

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
        "lon": closest_stop.coords[0],
    }
