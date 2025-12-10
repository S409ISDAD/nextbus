import datetime
import math
from datetime import datetime as dt
from datetime import timedelta

from dateutil.parser import isoparse
from geopy.distance import geodesic
from redis import Redis

from backend.deps import LONDON, UTC
from backend.config import PREDICTION_DISABLED
from backend.schemas.journey import Journey
from backend.schemas.prediction import Prediction
from backend.schemas.stop import StopTime
from backend.schemas.times import Times
from backend.services.journeys import get_trip, get_vehicle_journey

from backend.deps import get_logger

log = get_logger(__name__)


def calculate_sequence(stops: list[StopTime], future_time: dt, extra: int) -> int:
    sequence = 0
    for stop in stops:
        if stop.expt_time and stop.expt_time + timedelta(seconds=extra) > future_time:
            return sequence - 1

        sequence += 1

    return max(0, sequence)


def calculate_progress(prev_expt: dt, next_expt: dt, future_time: dt) -> float:
    stops_diff = abs(next_expt - prev_expt)

    current_diff = abs(future_time - prev_expt)

    if stops_diff == 0:
        return 0

    progress = round(
        current_diff / stops_diff, 5
    )  # 0-1 value of current time between prev and next time
    return min(progress, 1)


def calculate_loc(progress: float, track: list[list[float]]) -> list[float]:
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

            lat1, lon1 = full_track[i]
            lat2, lon2 = full_track[i + 1]

            interp_lat = lat1 + (lat2 - lat1) * seg_prog
            interp_lon = lon1 + (lon2 - lon1) * seg_prog

            return [interp_lat, interp_lon]

    return full_track[-1]


def calculate_heading(progress: float, track: list[list[float]]) -> int:
    progress = max(0.0, min(progress, 1.0))

    full_track = track
    if len(full_track) < 2:
        return 0

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
            lat1, lon1 = full_track[i]
            lat2, lon2 = full_track[i + 1]

            delta_lon = lon2 - lon1
            x = math.sin(math.radians(delta_lon)) * math.cos(math.radians(lat2))
            y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - (
                math.sin(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.cos(math.radians(delta_lon))
            )
            initial_bearing = math.atan2(x, y)
            initial_bearing = math.degrees(initial_bearing)
            compass_bearing = (initial_bearing + 360) % 360
            return int(compass_bearing)


def predict_future(
    journey: Journey,
    delay: int,
    timestamp: int | None,
    started: bool,
    ahead: int,
    r,
) -> list[Prediction]:
    if PREDICTION_DISABLED:
        return []
    current_time = dt.now(tz=UTC)

    stops = journey.stops

    predictions = []

    if not started:
        return predictions

    ideal_age = 45  # seconds
    sensitivity = 0.2  # multiplier for adjustment
    max_offset = 20  # cap adjustment to +-20s

    for seconds_ahead in range(ahead + 1):
        future_time = current_time + timedelta(seconds=seconds_ahead)

        timestamp = None

        if timestamp:
            age = int(
                (
                    datetime.datetime.fromtimestamp(future_time, LONDON)
                    - datetime.datetime.fromtimestamp(timestamp, LONDON)
                ).total_seconds()
            )
            raw_offset = int((ideal_age - age) * sensitivity)
            extra = max(-max_offset, min(max_offset, raw_offset))
            log.debug(f"data is {age}s old, adding {extra}s")
        else:
            extra = 0

        sequence = calculate_sequence(stops, future_time, extra)

        if sequence >= len(stops) - 1:
            break

        prev_expt = stops[sequence].expt_time + timedelta(seconds=extra)
        next_expt = stops[sequence + 1].expt_time + timedelta(seconds=extra)

        if prev_expt and next_expt:
            progress = calculate_progress(prev_expt, next_expt, future_time)

            track = stops[sequence + 1].track

            if track:
                loc = calculate_loc(progress, track)
                heading = calculate_heading(progress, track)

                prediction = Prediction(
                    timestamp=future_time,
                    sequence=sequence,
                    progress=progress,
                    location=loc,
                    heading=heading,
                )

                predictions.append(prediction)

    return predictions


def calculate_expected(
    delay: int,
    sequence: int,
    stop_id: str,
    journey_id: int,
    r: Redis,
    bus_seen_count: int = 1,
    pick_up_only: bool = False,
):
    journey: Journey | None = get_vehicle_journey(
        journey_id, delay, r
    )  # get journey data from bustimes.org

    if not journey:
        log.warning(f"no journey found for journey_id {journey_id}")
        return None, None, None

    current_time = dt.now(tz=UTC)

    not_started = False
    finished = False
    include = True

    expected_time = None
    scheduled_time = None

    call_condition = (
        None  # determines if the bus is stopping at the stop or not, e.g. cancelled
    )

    seen = bus_seen_count

    stop_idx = 0
    target_seq = None

    for stop_time in journey.stops:
        call_condition = stop_time.call_condition
        if stop_idx == 0:  # first stop
            scheduled_time_start = stop_time.aimed_time

            time_till_start = (scheduled_time_start - current_time).total_seconds()

            if scheduled_time_start > current_time and (
                time_till_start > 300 or sequence < 4
            ):
                # if more than 5 minutes before start, bus hasn't started yet.
                # if less than 5 minutes before start, only started if bus is very close to start
                not_started = True

        if stop_time.stop_id == stop_id:
            if seen > 1:
                seen -= 1
                log.warning(
                    f"Skipping stop {stop_id} for journey {journey_id}, bus has been seen {bus_seen_count} times"
                )
                continue  # skip to next occurrence of the stop
            target_seq = stop_idx

        if stop_time.stop_id == stop_id and not sequence > stop_idx:
            if pick_up_only and stop_time.pick_up is False:
                # only include stop if the bus picks up passengers there
                include = False
                break
            aimed = stop_time.aimed_time

            if not aimed:
                log.warning(f"not including bus, no scheduled time for stop {stop_id}")
                include = False
                break
            scheduled_time = aimed

            if not_started:
                delay = 0

            expected_time = scheduled_time + timedelta(seconds=delay)

        if stop_idx == len(journey.stops) - 1:
            expected_time_end = stop_time.aimed_time + timedelta(seconds=delay)

            if expected_time_end + timedelta(seconds=delay + 60) < current_time:
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
            call_condition=call_condition,
        ),
        journey,
    )


def calculate_expected_difference(timestamp: str, expected: dt, scheduled: dt):
    def func(x):
        return 5 + math.sqrt(x) * 7

    if not timestamp or not expected:
        return None, None

    age = int(
        (dt.now(tz=LONDON) - isoparse(timestamp).astimezone(LONDON)).total_seconds()
    )

    diff = func(age)

    # log.debug(f"age: {age}, diff: {diff}")

    max_expected = expected + timedelta(
        seconds=diff + 60
    )  # add 1 min buffer, as "max" means "definitely not later than this"
    min_expected = max(
        expected - timedelta(seconds=diff), scheduled
    )  # don't go earlier than scheduled

    return min_expected, max_expected


def get_started_finished(
    trip_id: int,
    r: Redis,
    delay: int = 0,
) -> tuple[bool, bool]:
    """calculate if the trip has started or ended based on the current time

    Args:
        trip_id (int): ID of the bustimes trip
        r (Redis): redis instance
        delay (int, optional): delay in seconds to apply to the trip. Defaults to 0.

    Returns:
        tuple(bool, bool): has started, has finished
    """
    trip = get_trip(trip_id, 0, r)

    if not trip:
        return False, False

    current_time = dt.now(tz=UTC)

    started = False
    finished = False

    stop_idx = 0

    for stop_time in trip.stops:
        if stop_idx == 0:
            scheduled_time_start = stop_time.aimed_time.astimezone(UTC)

            if scheduled_time_start <= current_time:
                started = True

        if stop_idx == len(trip.stops) - 1:
            scheduled_time_end = stop_time.aimed_time + timedelta(seconds=delay)

            if scheduled_time_end + timedelta(seconds=60) < current_time:
                finished = True

        stop_idx += 1

    return started, finished
