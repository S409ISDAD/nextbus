from shapely.geometry import Point
from geoalchemy2.shape import from_shape
from backend.db.db import SessionLocal
from backend.models import Service
from geoalchemy2 import functions as geofunc

import logging

log = logging.getLogger(__name__)


def get_nearby_services(lat: float, lon: float, dist: int = 200) -> list[Service]:
    point = Point(lon, lat)

    user_geom = from_shape(point, srid=4326)

    with SessionLocal() as db:
        nearby_services = (
            db.query(
                Service,
                geofunc.ST_Distance(Service.geometry, user_geom).label("distance"),
            )
            .filter(
                Service.geometry != None,
                geofunc.ST_DWithin(
                    Service.geometry, user_geom, dist / 10000
                ),  # convert from meters
            )
            .order_by("distance")
            .all()
        )
        for service, distance in nearby_services:
            setattr(
                service, "_user_distance", round(distance * 10000, 5)
            )  # convert to meters

    return [service for service, _ in nearby_services]
