from datetime import timedelta
import datetime
from backend.models.times import Times
from backend.services.journeys import get_vehicle_journey
from datetime import datetime as dt


async def calculate_expected(delay, sequence, stop_id, bus_id, journey_id, r):
    journey = await get_vehicle_journey(bus_id, journey_id, delay, r)

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
    )
