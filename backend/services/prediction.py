from datetime import timedelta
import datetime
from backend.services.journeys import get_vehicle_journey
from datetime import datetime as dt


async def calculate_expected(delay, sequence, stop_id, bus_id, journey_id, r):
    journey = await get_vehicle_journey(bus_id, journey_id, delay, r)

    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    not_started = False

    stop_idx = 0

    for stop_time in journey.stops:
        if stop_idx == 0:
            scheduled_time = dt.fromtimestamp(stop_time.aimed_time).astimezone(
                uk_timezone
            )

            if (scheduled_time > current_time) and (sequence < 2):
                not_started = True

        if stop_time.stop_id == stop_id:
            aimed = stop_time.aimed_time
            if not aimed:
                return None
            scheduled_time = dt.fromtimestamp(aimed).astimezone(uk_timezone)

            delay += (
                45  # account for stopping and various other things that increase delay
            )

            if not_started:
                delay = 0

            expected_time = scheduled_time + timedelta(seconds=delay)

            if expected_time < current_time:
                return None

            return {
                "expected": expected_time.timestamp(),
                "scheduled": scheduled_time.timestamp(),
                "not_started": not_started,
            }
        stop_idx += 1

    return None
