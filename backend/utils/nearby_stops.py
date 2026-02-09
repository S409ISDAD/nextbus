from backend.config import get_logger, setup_logging
from backend.services.stops import get_nearby_stops

import sys


log = get_logger(__name__)


def nearby_stops(lat: float, lon: float):
    stops = get_nearby_stops(lat, lon)

    stops = sorted(stops, key=lambda stop: stop.dist)

    if len(stops) == 0:
        print("No nearby stops in this location")

    for stop in stops:
        print(f"{stop.name} ({stop.stop_id}), {round(stop.dist)}m away")


if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) != 3:
        log.debug("Usage: python nearby_stops.py <lat> <lon>")
        exit(1)
    lat = sys.argv[1]
    lon = sys.argv[2]

    try:
        lat = float(lat)
        lon = float(lon)
        nearby_stops(lat, lon)
    except:
        print("not valid coordinates")
