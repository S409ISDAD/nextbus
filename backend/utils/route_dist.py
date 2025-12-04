from redis import Redis
from backend.services.journeys import get_trip
from backend.deps import get_redis
from geopy.distance import geodesic

from backend.utils.time_taken import time_taken
from backend.deps import get_logger
from backend.config import setup_logging

log = get_logger(__name__)


def compute_distance(atco_on, atco_off, trip_id, r: Redis) -> float:
    trip = get_trip(trip_id, 0, r)

    if not trip:
        return None

    total_distance = 0.0

    found_start = False

    for stop in trip.stops:
        if not stop:
            continue

        if not found_start:
            if stop.stop_id == atco_on:
                found_start = True
            else:
                continue

        if not stop.track or len(stop.track) < 2:
            continue
        previous_coords = None
        for coords in stop.track:
            if previous_coords is not None:
                total_distance += geodesic(previous_coords, coords).meters
            previous_coords = coords

        if stop.stop_id == atco_off:
            break

    log.debug(
        f"Computed distance from {atco_on} to {atco_off} on trip {trip_id}: {round(total_distance)} meters, {round(total_distance / 1000, 2)} km"
    )
    return round(total_distance)


if __name__ == "__main__":
    r = get_redis()
    setup_logging()
    with time_taken("compute distance"):
        compute_distance("1900HA110055", "1900HA020369", 552633449, r)
