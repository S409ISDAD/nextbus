import logging
import math
from datetime import datetime as dt, timedelta

from geopy.distance import geodesic
from pyproj import Geod
from redis.asyncio import Redis
from shapely.geometry import LineString, Point

from backend.deps import LONDON
from backend.schemas.confidence import Confidence
from backend.schemas.journey import Trip, LiveJourney
from backend.services.journeys import get_trip, get_live_journey

log = logging.getLogger(__name__)

geod = Geod(ellps="WGS84")

broken_down_weight = 0.1
log_off_weight = 0.1
diversion_weight = 0.1
broken_tracking_weight = 0.1


async def calculate_confidence(
    delay: int, location: list[float], journey_id: int, trip_id: int, redis: Redis
):
    trip = await get_trip(trip_id, delay, redis)
    live_journey = await get_live_journey(journey_id, redis)

    broken_down_confidence = check_broken_down(live_journey, delay)
    log_off_confidence = check_log_off(trip, live_journey)
    diversion_confidence = check_diversion(trip, live_journey, delay)
    broken_tracking_confidence = check_broken_tracking(trip, live_journey, delay)

    final_confidence: float = min(
        broken_tracking_confidence
        + diversion_confidence
        + log_off_confidence
        + broken_down_confidence,
        1,
    )

    return Confidence(
        final_confidence=final_confidence,
        broken_down_confidence=broken_down_confidence,
        log_off_confidence=log_off_confidence,
        diversion_confidence=diversion_confidence,
        broken_tracking_confidence=broken_tracking_confidence,
    )


def check_broken_down(live_journey: LiveJourney, delay: int) -> float:
    if len(live_journey.locations) < 5:
        return 0.0
    loc_history = LineString(live_journey.generate_location_history()[-10:])

    dist_moved = geod.geometry_length(loc_history)

    if dist_moved >= 15:
        return 0.0

    confidence = 1 - (dist_moved / 15)
    return max(0.0, min(1.0, confidence))


def check_log_off(trip: Trip, live_journey: LiveJourney) -> float:
    if len(live_journey.locations) < 5:
        return 0.0
    end_time = trip.stops[-1].aimed_time
    now = dt.now(LONDON)

    ended_ago = now - end_time

    if len(live_journey.locations) < 2:
        return 0.0

    if (
        ended_ago.total_seconds() < 60 * 15
    ):  # if it hasn't ended yet, we don't need to check
        return 0.0

    last_locs = live_journey.generate_location_history()[-5:]
    last_headings = [loc.direction for loc in live_journey.locations[-5:]]

    track = LineString(trip.generate_full_track())

    diffs = []

    fwd_dist = 50  # meters ahead to calculate bearing

    for loc, heading in zip(last_locs, last_headings):
        p = Point(loc)
        nearest = track.interpolate(track.project(p))

        end_dist = track.project(nearest) + fwd_dist
        if end_dist > track.length:
            end_dist = track.length
        fwd_point = track.interpolate(end_dist)

        fwd_azimuth, _, _ = geod.inv(nearest.x, nearest.y, fwd_point.x, fwd_point.y)

        track_bearing = fwd_azimuth % 360

        diff = round((heading - track_bearing + 180) % 360 - 180, 5)
        diffs.append(diff)
    log.debug(diffs)

    # avg_diff = sum(abs(d) for d in diffs) / len(diffs)

    rms_diff = math.sqrt(sum(d * d for d in diffs) / len(diffs))

    confidence = max(0.0, rms_diff / 180.0)

    return round(confidence, 5)


def check_diversion(trip: Trip, live_journey: LiveJourney, delay) -> float:
    """
    Return confidence of diversion if similarity is less than 92%
    :param trip:
    :param live_journey:
    :return float:
    """
    if len(live_journey.locations) < 8:
        return 0.0

    end_time = trip.stops[-1].aimed_time
    now = dt.now(LONDON)

    delay_secs = max(0, int(delay or 0))

    ended_ago = now - (end_time + timedelta(seconds=delay_secs))

    if ended_ago.total_seconds() > 60 * 15:  # trip has ended, no need to check
        return 0.0

    loc_history = LineString(live_journey.generate_location_history(exclude_start=True))
    track = LineString(trip.generate_full_track())
    similarity = track_location_similarity(track, loc_history)

    top_end = 0.92
    bottom_end = 0.65

    if similarity > 0.92:
        return 0.0
    confidence = 1 - (similarity * 1 - (top_end - similarity) / (top_end - bottom_end))
    return max(0.0, min(1.0, confidence))


def check_broken_tracking(trip: Trip, live_journey: LiveJourney, delay) -> float:
    now = dt.now(LONDON)

    started_ago = now - live_journey.start_time

    end_time = trip.stops[-1].aimed_time
    now = dt.now(LONDON)

    delay_secs = max(0, int(delay or 0))

    ended_ago = now - (end_time + timedelta(seconds=delay_secs))

    if started_ago.total_seconds() < 60 * 5:  # dont bother if started recently
        log.debug("Started recently, skipping")
        return 0.0

    if ended_ago.total_seconds() > 60 * 15:  # trip has ended, no need to check
        log.debug("Trip ended recently, skipping")
        return 0.0

    if len(live_journey.locations) < 2:
        log.debug("Not enough locations, skipping")
        return 0.0

    loc_history = LineString(live_journey.generate_location_history(exclude_start=True))
    track = LineString(trip.generate_full_track())
    similarity = track_location_similarity(track, loc_history)

    total_dist = geod.geometry_length(track)

    dist_moved = geod.geometry_length(loc_history)

    completion = dist_moved / total_dist

    return 1 - (similarity * 1 - completion / 10)


def track_location_similarity(track: LineString, locations: LineString) -> float:
    deviation = []

    for lon, lat in locations.coords:
        p = Point(lon, lat)
        nearest_point = track.interpolate(track.project(p))  # closest point on route
        d = geodesic(
            (lat, lon), (nearest_point.y, nearest_point.x)
        ).meters  # distance to the closest point
        deviation.append(d)

    total_deviation = sum(deviation)
    max_allowed_deviation = 1000 * len(deviation)  # 1km per point maximum deviation

    if max_allowed_deviation == 0:  # prevent division by zero
        return 1.0
    normalised = 1 - min(total_deviation / max_allowed_deviation, 1.0)
    return normalised
