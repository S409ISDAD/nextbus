from shapely.geometry import Point
from geoalchemy2.shape import from_shape
from backend.db.db import SessionLocal
from backend.models import Service
from geoalchemy2 import functions as geofunc


from backend.deps import get_logger

log = get_logger(__name__)


def get_nearby_services(lat: float, lon: float, dist: int = 200) -> list[Service]:
    """gets services close to the user's location by finding nearby route geometries.

    Args:
        lat (float)
        lon (float)
        dist (int, optional): maximum range to search. Defaults to 200.

    Returns:
        list[Service]: list of nearby services
    """
    point = Point(lon, lat)

    user_geom = from_shape(point, srid=4326)  # convert to postgis geometry

    with SessionLocal() as db:
        nearby_services = (
            db.query(
                Service,
                geofunc.ST_Distance(Service.geometry, user_geom).label(
                    "distance"
                ),  # calculate and attach distance
            )
            .filter(
                Service.geometry is not None,
                geofunc.ST_DWithin(
                    Service.geometry, user_geom, dist / 10000
                ),  # convert from meters
            )  # limit to within max distance
            .order_by("distance")  # order by closest first
            .all()
        )
        for service, distance in nearby_services:
            setattr(
                service,
                "_user_distance",
                round(distance * 10000, 5),  # attach distance to user in meters
            )  # convert to meters

    return [
        service for service, _ in nearby_services
    ]  # return only services and not distances
