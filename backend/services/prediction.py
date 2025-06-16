from datetime import timedelta
import datetime
import math
from backend.models.journey import Journey
from backend.models.prediction import Prediction
from backend.models.stop import StopTime
from backend.models.times import Times
from backend.services.journeys import get_vehicle_journey
from datetime import datetime as dt


async def calculate_sequence(stops: list[StopTime], future_time: int) -> int:
    sequence = 0
    for stop in stops:
        if stop.expt_time and stop.expt_time > future_time:
            return sequence - 1

        sequence += 1

    return max(0, sequence)


async def calculate_progress(prev_expt: int, next_expt: int, future_time: int) -> float:
    stops_diff = abs(next_expt - prev_expt - 5)

    current_diff = abs(future_time - prev_expt + 5)

    if stops_diff == 0:
        return 0

    progress = round(
        current_diff / stops_diff, 5
    )  # 0-1 value of current time between prev and next time
    return min(progress, 1)


async def calculate_loc(
    progress: float, track: list[list[float]], next_track: list[list[float]]
) -> list[float]:
    rough_idx = len(track) * progress
    track.extend(next_track)

    loc1 = track[math.floor(rough_idx)]
    loc2 = track[math.ceil(rough_idx)]

    diff_lat = loc2[0] - loc1[0]
    diff_lng = loc2[1] - loc1[1]

    idx_prog = rough_idx - math.floor(rough_idx)

    loc = [diff_lat * idx_prog, diff_lng * idx_prog]

    return loc


async def predict_future(
    journey: Journey,
    delay: int,
    timestamp: dt | None,
    started: bool,
    ahead: int,
    r,
) -> list[Prediction]:
    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    stops = journey.stops

    predictions = []

    if not started:
        return predictions

    for seconds_ahead in range(ahead + 1):
        future_time = int(current_time.timestamp() + seconds_ahead)

        sequence = await calculate_sequence(stops, future_time)

        if sequence >= len(stops) - 1:
            break

        prev_expt = stops[sequence].expt_time
        next_expt = stops[sequence + 1].expt_time

        if prev_expt and next_expt:
            progress = await calculate_progress(prev_expt, next_expt, future_time)

            track = stops[sequence].track
            next_track = stops[sequence + 1].track

            if track and next_track:
                loc = await calculate_loc(progress, track, next_track)

                prediction = Prediction(
                    timestamp=future_time,
                    sequence=sequence,
                    progress=progress,
                    location=loc,
                )

                predictions.append(prediction)

    return predictions


async def calculate_expected(delay, sequence, stop_id, bus_id, journey_id, r):
    journey = await get_vehicle_journey(journey_id, delay, r)

    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    not_started = False
    finished = False
    include = True

    expected_time = None
    scheduled_time = None

    stop_idx = 0

    for stop_time in journey.stops:
        if stop_idx == 0:
            scheduled_time_start = dt.fromtimestamp(stop_time.aimed_time).astimezone(
                uk_timezone
            )

            if (scheduled_time_start > current_time) and (sequence < 2):
                not_started = True

        if stop_time.stop_id == stop_id:
            aimed = stop_time.aimed_time
            if not aimed:
                include = False
                break
            scheduled_time = dt.fromtimestamp(aimed).astimezone(uk_timezone)

            if not_started:
                delay = 0

            expected_time = scheduled_time + timedelta(seconds=delay)

            if expected_time < current_time:
                include = False
                break
        if stop_idx == len(journey.stops) - 1:
            scheduled_time_end = dt.fromtimestamp(stop_time.aimed_time).astimezone(
                uk_timezone
            )

            if scheduled_time_end + timedelta(seconds=delay + 45) < current_time:
                finished = True

        stop_idx += 1

    if expected_time:
        expected_time = int(expected_time.timestamp())

    if scheduled_time:
        scheduled_time = int(scheduled_time.timestamp())

    return Times(
        expected=expected_time,
        scheduled=scheduled_time,
        started=not not_started,
        finished=finished,
        include=include,
    ), journey
