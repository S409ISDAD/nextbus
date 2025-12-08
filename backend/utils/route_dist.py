from geopy.distance import geodesic
from redis import Redis

from backend.config import setup_logging
from backend.deps import get_logger, get_redis
from backend.services.journeys import get_trip
from backend.utils.time_taken import time_taken

log = get_logger(__name__)


def compute_distance(
    atco_on: str, atco_off: str, trip_id: int, r: Redis
) -> float | None:
    trip = get_trip(trip_id, 0, r)

    if not trip:
        return None

    total_distance = 0.0
    found_start = False

    for stop in trip.stops:
        if not stop:
            continue

        # only start once we reach the boarding stop
        if not found_start:
            if stop.stop_id == atco_on:
                found_start = True
            else:
                continue

        if stop.track and len(stop.track) >= 2:
            prev_coords = None
            for coords in stop.track:
                if prev_coords is not None:
                    total_distance += geodesic(prev_coords, coords).meters
                prev_coords = coords

        # stop once we reach the alighting stop
        if stop.stop_id == atco_off:
            break

    distance_km = total_distance / 1000

    log.debug(
        f"Distance from {atco_on} to {atco_off} on trip {trip_id}: "
        f"{round(total_distance)}m ({distance_km:.2f}km)"
    )

    return round(total_distance)


if __name__ == "__main__":
    r = get_redis()
    setup_logging()

    with time_taken("compute distance"):
        compute_distance("1900HA110364", "1900HA020637", 552633449, r)
