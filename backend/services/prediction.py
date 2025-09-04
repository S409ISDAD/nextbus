from datetime import timedelta
import datetime
from geopy.distance import geodesic
from backend.deps import UTC
from backend.schemas.journey import Journey
from backend.schemas.prediction import Prediction
from backend.schemas.stop import StopTime
from backend.schemas.times import Times
from backend.services.journeys import get_trip, get_vehicle_journey
from datetime import datetime as dt


async def calculate_sequence(stops: list[StopTime], future_time: dt, extra: int) -> int:
    sequence = 0
    for stop in stops:
        if stop.expt_time and stop.expt_time + timedelta(seconds=extra) > future_time:
            return sequence - 1

        sequence += 1

    return max(0, sequence)


async def calculate_progress(prev_expt: dt, next_expt: dt, future_time: dt) -> float:
    stops_diff = abs(next_expt - prev_expt - timedelta(seconds=5))

    current_diff = abs(future_time - prev_expt + timedelta(seconds=5))

    if stops_diff == 0:
        return 0

    progress = round(
        current_diff / stops_diff, 5
    )  # 0-1 value of current time between prev and next time
    return min(progress, 1)


async def calculate_loc(progress: float, track: list[list[float]]) -> list[float]:
    progress = max(0.0, min(progress, 1.0))

    full_track = track
    if len(full_track) < 2:
        return full_track[0] if full_track else [0.0, 0.0]

    distances = []
    cumulative = [0.0]

    for i in range(len(full_track) - 1):
        d = geodesic(full_track[i], full_track[i + 1]).m
        distances.append(d)
        cumulative.append(cumulative[-1] + d)

    total_dist = cumulative[-1]
    target_dist = total_dist * progress

    for i in range(len(distances)):
        if cumulative[i + 1] >= target_dist:
            seg_dist = distances[i]
            if seg_dist == 0:
                return full_track[i]
            seg_prog = (target_dist - cumulative[i]) / seg_dist

            lat1, lng1 = full_track[i]
            lat2, lng2 = full_track[i + 1]

            interp_lat = lat1 + (lat2 - lat1) * seg_prog
            interp_lng = lng1 + (lng2 - lng1) * seg_prog

            return [interp_lat, interp_lng]

    return full_track[-1]


async def predict_future(
    journey: Journey,
    delay: int,
    timestamp: int | None,
    started: bool,
    ahead: int,
    r,
) -> list[Prediction]:
    current_time = dt.now(tz=UTC)

    stops = journey.stops

    predictions = []

    if not started:
        return predictions

    ideal_age = 45  # seconds
    sensitivity = 0.2  # multiplier for adjustment
    max_offset = 20  # cap adjustment to ±20s

    for seconds_ahead in range(ahead + 1):
        future_time = current_time + timedelta(seconds=seconds_ahead)

        timestamp = None

        if timestamp:
            age = int(
                (
                    datetime.datetime.fromtimestamp(future_time, uk_timezone)
                    - datetime.datetime.fromtimestamp(timestamp, uk_timezone)
                ).total_seconds()
            )
            raw_offset = int((ideal_age - age) * sensitivity)
            extra = max(-max_offset, min(max_offset, raw_offset))
            print(f"data is {age}s old, adding {extra}s")
        else:
            extra = 0

        sequence = await calculate_sequence(stops, future_time, extra)

        if sequence >= len(stops) - 1:
            break

        prev_expt = stops[sequence].expt_time + timedelta(seconds=extra)
        next_expt = stops[sequence + 1].expt_time + timedelta(seconds=extra)

        if prev_expt and next_expt:
            progress = await calculate_progress(prev_expt, next_expt, future_time)

            track = stops[sequence + 1].track

            if track:
                loc = await calculate_loc(progress, track)

                prediction = Prediction(
                    timestamp=future_time,
                    sequence=sequence,
                    progress=progress,
                    location=loc,
                )

                predictions.append(prediction)

    return predictions


async def calculate_expected(delay, sequence, stop_id, journey_id, r):
    journey = await get_vehicle_journey(journey_id, delay, r)

    current_time = dt.now(tz=UTC)

    not_started = False
    finished = False
    include = True

    expected_time = None
    scheduled_time = None

    stop_idx = 0
    target_seq = None

    for stop_time in journey.stops:
        if stop_idx == 0:
            scheduled_time_start = stop_time.aimed_time

            time_till_start = (scheduled_time_start - current_time).total_seconds()

            if (scheduled_time_start > current_time) and (time_till_start > 300):
                not_started = True

        if stop_time.stop_id == stop_id:
            aimed = stop_time.aimed_time
            target_seq = stop_idx
            if not aimed:
                include = False
                break
            scheduled_time = aimed

            if not_started:
                delay = 0

            expected_time = scheduled_time + timedelta(seconds=delay)

            if expected_time + timedelta(minutes=1) < current_time:
                include = False
                break
        if stop_idx == len(journey.stops) - 1:
            scheduled_time_end = stop_time.aimed_time

            if scheduled_time_end + timedelta(seconds=delay + 60) < current_time:
                finished = True

        stop_idx += 1

    return (
        target_seq,
        Times(
            expected=expected_time,
            scheduled=scheduled_time,
            started=not not_started,
            finished=finished,
            include=include,
        ),
        journey,
    )


async def get_started_finished(trip_id, r):
    trip = await get_trip(trip_id, 0, r)

    current_time = dt.now(tz=UTC)

    not_started = False
    finished = False

    stop_idx = 0

    for stop_time in trip.stops:
        if stop_idx == 0:
            scheduled_time_start = stop_time.aimed_time.astimezone(UTC)

            if scheduled_time_start > current_time:
                not_started = True

        if stop_idx == len(trip.stops) - 1:
            scheduled_time_end = stop_time.aimed_time

            if scheduled_time_end + timedelta(seconds=60) < current_time:
                finished = True

        stop_idx += 1

    return not not_started, finished
