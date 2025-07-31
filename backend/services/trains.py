from typing import List
from backend.models.trains import (
    LocationDetail,
    ServiceLocation,
    StationResponse,
    Train,
    TrainService,
)
from backend.services.caching import TRAIN_CACHE, get_cached
from redis.asyncio import Redis

from backend.services.train_prediction import predict_future, get_started_finished
from backend.utils.fetch_json import fetch_rtt_json
from backend.utils.trains import operator_map
from datetime import datetime
from datetime import timezone, timedelta


async def parse_operator(atocName: str):
    if not atocName:
        return {"code": "Unknown", "color": "#888888"}
    if atocName == "Unknown":
        return {"code": "Unknown", "color": "#888888"}
    if operator_map[atocName]:
        return operator_map[atocName]
    code = "".join([w[:1].upper() for w in atocName.split(" ")])
    print("Unknown operator:", atocName)
    return {"code": code, "color": "#1447E6"}


def parse_time(time_str: str):
    if not time_str:
        return None

    padded = time_str.ljust(6, "0")
    try:
        hours = int(padded[:2])
        minutes = int(padded[2:4])
        seconds = int(padded[4:6])
    except ValueError:
        return None

    uk_timezone = timezone(timedelta(hours=1))
    now = datetime.now(timezone.utc).astimezone(uk_timezone)
    date = now.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)

    # If the time is more than 12 hours behind now, assume it's for the next day (overnight trains)
    if (date - now).total_seconds() < -12 * 60 * 60:
        date += timedelta(days=1)

    return date


async def parse_trains(trains: dict) -> StationResponse | None:
    try:
        if not trains.get("services"):
            return StationResponse(**trains, services=[])

        updated_trains = []

        for train in trains["services"]:
            atoc_name = train.get("atocName")
            operator = await parse_operator(atoc_name)

            location = train.get("locationDetail", {})
            expected_departure = parse_time(location.get("realtimeDeparture"))
            scheduled_departure = parse_time(location.get("gbttBookedDeparture"))

            expected_arrival = parse_time(location.get("realtimeArrival"))
            scheduled_arrival = parse_time(location.get("gbttBookedArrival"))

            if not expected_departure:
                expected_departure = scheduled_departure
            if not expected_arrival:
                expected_arrival = scheduled_arrival

            if not expected_departure or not scheduled_departure:
                delay = (
                    (expected_arrival - scheduled_arrival).total_seconds()
                    if expected_arrival and scheduled_arrival
                    else 0
                )
            else:
                delay = (
                    (expected_departure - scheduled_departure).total_seconds()
                    if expected_departure and scheduled_departure
                    else 0
                )

            if train.get("serviceType") == "train":
                train_dict = dict(train)
                train_dict.update(
                    {
                        "atocCode": operator["code"],
                        "atocColor": operator["color"],
                    }
                )
                train_dict["locationDetail"].update(
                    {
                        "expectedDeparture": expected_departure,
                        "scheduledDeparture": scheduled_departure,
                        "expectedArrival": expected_arrival,
                        "scheduledArrival": scheduled_arrival,
                        "timeto": "",
                        "delay": round(delay),
                    }
                )
                updated_trains.append(Train(**train_dict))

        trains_dict = dict(trains)
        trains_dict.update(
            {
                "services": updated_trains,
            }
        )
        return StationResponse(**trains_dict)
    except Exception as error:
        print("failed to get departures", error)
        return None


async def parse_train(train) -> TrainService | None:
    try:
        operator = await parse_operator(train.get("atocName", ""))

        updated_stops: List[ServiceLocation] = []
        uk_timezone = timezone(timedelta(hours=1))
        now = datetime.now(timezone.utc).astimezone(uk_timezone)

        for location in train.get("locations", []):
            expected_departure = parse_time(location.get("realtimeDeparture"))
            scheduled_departure = parse_time(location.get("gbttBookedDeparture"))

            expected_arrival = parse_time(location.get("realtimeArrival"))
            scheduled_arrival = parse_time(location.get("gbttBookedArrival"))

            if not expected_departure:
                expected_departure = scheduled_departure

            if not expected_arrival:
                expected_arrival = scheduled_arrival

            departed = False
            if expected_departure and expected_departure < now:
                departed = True

            delay = 0

            if not expected_departure or not scheduled_departure:
                if expected_arrival and scheduled_arrival:
                    delay = (expected_arrival - scheduled_arrival).total_seconds()
            else:
                if expected_departure and scheduled_departure:
                    delay = (expected_departure - scheduled_departure).total_seconds()

            stop = ServiceLocation(
                **location,
                expectedDeparture=expected_departure,
                scheduledDeparture=scheduled_departure,
                expectedArrival=expected_arrival,
                scheduledArrival=scheduled_arrival,
                delay=round(delay),
                departed=departed,
                timeTo="",
            )
            updated_stops.append(stop)

        next_station = next((stop for stop in updated_stops if not stop.departed), None)
        sequence = (
            updated_stops.index(next_station) if next_station else len(updated_stops)
        )
        delay = (
            next_station.delay
            if next_station
            else (updated_stops[-1].delay if updated_stops else 0)
        )

        train_dict = dict(train)
        train_dict.update(
            {
                "locations": updated_stops,
                "atocCode": operator["code"],
                "atocColor": operator["color"],
                "delay": delay,
                "sequence": sequence,
                "nextStation": next_station,
            }
        )
        return TrainService(**train_dict)
    except Exception as error:
        print("failed to get departures", error)
        return None


async def get_departures(station_code: str, r: Redis):
    async def fetch(station_code):
        url = f"https://api.rtt.io/api/v1/json/search/{station_code}"
        trains = await fetch_rtt_json(url)

        if not trains:
            return None

        updated_trains = await parse_trains(trains)

        return updated_trains

    trains = await get_cached(
        f"trains:departures:{station_code}",
        fetch,
        (station_code,),
        TRAIN_CACHE,
        r,
    )

    return trains


async def get_arrivals(station_code: str, r: Redis):
    async def fetch(station_code):
        url = f"https://api.rtt.io/api/v1/json/search/{station_code}/arrivals"
        trains = await fetch_rtt_json(url)

        if not trains:
            return None

        updated_trains = await parse_trains(trains)

        return updated_trains

    trains = await get_cached(
        f"trains:arrivals:{station_code}",
        fetch,
        (station_code,),
        TRAIN_CACHE,
        r,
    )

    return trains


async def get_service(service_id: str, r: Redis):
    async def fetch(service_id):
        today = datetime.now()
        date_str = today.strftime("%Y/%m/%d")
        url = f"https://api.rtt.io/api/v1/json/service/{service_id}/{date_str}"
        train = await fetch_rtt_json(url)

        if not train:
            return None

        updated_train = await parse_train(train)

        if not updated_train:
            return None

        started, finished = await get_started_finished(updated_train, r)

        predictions = await predict_future(updated_train, None, started, 35, r)

        updated_train.started = started
        updated_train.finished = finished
        updated_train.predictions = predictions

        return updated_train

    trains = await get_cached(
        f"trains:service:{service_id}",
        fetch,
        (service_id,),
        TRAIN_CACHE,
        r,
    )

    return trains
