from datetime import timedelta
import datetime
from backend.models.prediction import Prediction
from backend.models.trains import ServiceLocation, TrainService
from datetime import datetime as dt


async def calculate_sequence(
    stops: list[ServiceLocation],
    future_time: dt,
) -> int:
    sequence = 0
    for stop in stops:
        if sequence >= len(stops) - 1:
            return sequence - 1
        if stop.expectedDeparture and stop.expectedDeparture > future_time:
            return sequence - 1

        sequence += 1

    return max(0, sequence)


async def calculate_progress(prev_dep: dt, next_arr: dt, future_time: dt) -> float:
    stops_diff = abs(next_arr - prev_dep)

    current_diff = abs(future_time - prev_dep)

    if stops_diff == 0:
        return 0

    progress = round(
        current_diff / stops_diff, 5
    )  # 0-1 value of current time between prev departure and next arrival
    return min(progress, 1)


async def predict_future(
    service: TrainService,
    timestamp: int | None,
    started: bool,
    ahead: int,
    r,
) -> list[Prediction]:
    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    stops = service.locations

    predictions = []

    if not started:
        return predictions

    for seconds_ahead in range(ahead + 1):
        future_time = current_time + timedelta(seconds=seconds_ahead)

        sequence = await calculate_sequence(stops, future_time)

        if sequence >= len(stops) - 1:
            break

        prev_dep = stops[sequence].expectedDeparture
        next_arr = stops[sequence + 1].expectedArrival
        if not next_arr:
            next_arr = stops[sequence + 1].expectedDeparture

        if prev_dep and next_arr:
            if not stops[sequence].departed:
                progress = 0
            else:
                progress = await calculate_progress(prev_dep, next_arr, future_time)

            prediction = Prediction(
                timestamp=future_time,
                sequence=sequence,
                progress=progress,
                location=[0],
            )

            predictions.append(prediction)
    return predictions


async def get_started_finished(service: TrainService, r):
    uk_timezone = datetime.timezone(timedelta(hours=1))
    current_time = dt.now(datetime.timezone.utc).astimezone(uk_timezone)

    not_started = False
    finished = False

    stop_idx = 0

    for stop_time in service.locations:
        if stop_idx == 0:
            scheduled_time_start = stop_time.expectedDeparture

            if scheduled_time_start and scheduled_time_start > current_time:
                not_started = True

        if stop_idx == len(service.locations) - 1:
            scheduled_time_end = stop_time.expectedArrival

            if (
                scheduled_time_end
                and scheduled_time_end + timedelta(seconds=60) < current_time
            ):
                finished = True

        stop_idx += 1

    return not not_started, finished
