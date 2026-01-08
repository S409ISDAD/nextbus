from fastapi import Response
from redis import Redis
from shapely.geometry import shape, MultiLineString
from staticmap import StaticMap, Line, CircleMarker
from PIL import Image
import base64

from backend.config import BASE, get_logger, setup_logging
from backend.deps import get_redis
from backend.services.caching import SERVICE_CACHE, get_cached
from backend.utils.fetch_json import fetch_json
from backend.utils.time_taken import time_taken

log = get_logger(__name__)


def get_service_data(service_id: int, r: Redis):
    def fetch(service_id):
        data = fetch_json(f"{BASE}/services/{service_id}.json")

        if not data:
            return None

        raw_coords = data["geometry"]["coordinates"]
        clean_coords = [c for c in raw_coords if len(c) > 0]

        data["geometry"]["coordinates"] = clean_coords

        return data

    service_data = get_cached(
        f"service_geojson:{service_id}",
        fetch,
        (service_id,),
        SERVICE_CACHE,
        r,
    )

    return service_data


def get_line_pixels(p1, p2):
    """Bresenham's Line Algorithm to yield all pixels between two points."""
    x0, y0 = p1
    x1, y1 = p2
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy

    pixels = []
    while True:
        pixels.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pixels


def process_route(
    service_data,
    screen_w=256,
    screen_h=64,
    padding=4,
):

    route_geom = shape(service_data["geometry"])
    # route_geom = route_geom.simplify(0.0001)

    stop_geoms = [shape(f["geometry"]) for f in service_data["stops"]["features"]]

    min_x, min_y, max_x, max_y = route_geom.bounds

    draw_w, draw_h = screen_w - (padding * 2), screen_h - (padding * 2)
    geo_w, geo_h = max_x - min_x, max_y - min_y

    scale = min(
        draw_w / geo_w, draw_h / geo_h
    )  # calculate the relative scale to fit on the screen

    # center the map
    offset_x = (draw_w - (geo_w * scale)) / 2 + padding
    offset_y = (draw_h - (geo_h * scale)) / 2 + padding

    def to_pixels(lon, lat):
        # convert the coordinates to pixel coordinates, and centered.
        px = int((lon - min_x) * scale + offset_x)
        py = int(screen_h - ((lat - min_y) * scale + offset_y))
        return (px, py)

    route_pixels = set()
    if isinstance(route_geom, MultiLineString):
        for line in route_geom.geoms:
            coords = list(line.coords)
            for i in range(len(coords) - 1):
                start_px = to_pixels(*coords[i])
                end_px = to_pixels(*coords[i + 1])

                # Interpolate all pixels between these two GPS nodes
                line_pixels = get_line_pixels(start_px, end_px)
                route_pixels.update(line_pixels)
    else:
        for pt in route_geom.coords:
            route_pixels.add(to_pixels(pt[0], pt[1]))

    stop_pixels = list({to_pixels(s.coords[0][0], s.coords[0][1]) for s in stop_geoms})

    return {
        "route": list(route_pixels),
        "stops": stop_pixels,
    }


def process_route_map(
    service_data,
    screen_w=256,
    screen_h=64,
    padding=4,
):
    m = StaticMap(
        screen_w * 4,
        screen_h * 4,
        tile_size=512,
        url_template="https://tiles.snubs.dev/styles/transport-dark/512/{z}/{x}/{y}.png",
    )

    coords = service_data["geometry"]["coordinates"]
    # Filter empty and add lines to map
    for segment in [c for c in coords if len(c) > 0]:
        # Convert [[lon, lat], ...] to [(lon, lat), ...]
        line_coords = [tuple(p) for p in segment]
        m.add_line(Line(line_coords, "white", 3))

    for feature in service_data["stops"]["features"]:
        p = feature["geometry"]["coordinates"]
        m.add_marker(CircleMarker(tuple(p), "red", 6))

    image = m.render()

    image = image.resize((screen_w, screen_h), resample=Image.Resampling.LANCZOS)

    # Ensure image is in RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")

    raw_buffer = bytearray()
    for y in range(64):
        for x in range(256):
            r, g, b = image.getpixel((x, y))[:3]
            # Send 4 bytes per pixel to match your 65536 buffer
            raw_buffer.append(b)  # B
            raw_buffer.append(g)  # G
            raw_buffer.append(r)  # R
            raw_buffer.append(0)  # A (or Padding)

    return raw_buffer


if __name__ == "__main__":
    r = get_redis()
    setup_logging()

    with time_taken("generate display"):
        service_data = get_service_data(1895, r)
        route = process_route_map(service_data)
        print(route)
