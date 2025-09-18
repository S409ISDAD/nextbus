from geoalchemy2.shape import from_shape
from shapely.geometry.point import Point


def generate_point(lat, lon):
    """Generate a Point object from latitude and longitude."""
    return from_shape(Point(lon, lat), srid=4326)
