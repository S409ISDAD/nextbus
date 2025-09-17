from pydantic import BaseModel

from backend.schemas.confidence import Confidence
from backend.services.journeys import get_trip, get_live_journey
from backend.schemas.journey import Trip, LiveJourney
from redis.asyncio import Redis
from datetime import datetime as dt
from geopy import distance

broken_down_weight = 0.1
log_off_weight = 0.1
diversion_weight = 0.1
broken_tracking_weight = 0.1


async def calculate_confidence(delay: int, location: list[float], journey_id: int,  trip_id: int, redis: Redis):
    trip = await get_trip(trip_id, delay, redis)
    live_journey = await get_live_journey(journey_id, redis)

    broken_down_confidence = check_broken_down(live_journey, delay)
    log_off_confidence = check_log_off(trip, live_journey)
    diversion_confidence = check_diversion(trip, live_journey)
    broken_tracking_confidence = check_broken_tracking(trip, live_journey)

    final_confidence: float = 0.0

    return Confidence(
        final_confidence=final_confidence,
        broken_down_confidence=broken_down_confidence,
        log_off_confidence=log_off_confidence,
        diversion_confidence=diversion_confidence,
        broken_tracking_confidence=broken_tracking_confidence,
    )


def check_broken_down(live_journey: LiveJourney, delay: int) -> float:
    return 0.0

def check_log_off(trip: Trip, live_journey: LiveJourney) -> float:
    return 0.0

def check_diversion(trip: Trip, live_journey: LiveJourney) -> float:
    return 0.0

def check_broken_tracking(trip: Trip, live_journey: LiveJourney) -> float:
    loc_history = live_journey.generate_location_history()
    similarity = track_location_similarity(loc_history, trip.generate_full_track())
    print(f"Similarity: {similarity}")

    dist_moved = 0
    for loc in loc_history:
        dist_moved += distance.distance(loc, loc_history[loc_history.index(loc) - 1]).m

    print(dist_moved)

    return similarity * (1 - dist_moved / 1000)


def track_location_similarity(track: list[list[float]], locations: list[list[float]]) -> float:
    deviation = []

    for loc1, loc2 in zip(track, locations):
        loc1 = [round(loc1[0], 6), round(loc1[1], 6)]
        dist = distance.geodesic(loc1, loc2).m
        deviation.append(dist)

    total_deviation = sum(deviation)
    max_allowed_deviation = 1000 * len(deviation)  # 1km per point maximum deviation

    normalised = 1 - min(total_deviation / max_allowed_deviation, 1.0)
    return normalised