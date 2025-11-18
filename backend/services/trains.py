from typing import List

from fastapi import HTTPException
from backend.schemas.trains import (
    ServiceLocation,
    StationResponse,
    Train,
    TrainService,
)
from backend.services.caching import TRAIN_CACHE, get_cached
from redis import Redis

from backend.services.train_prediction import predict_future, get_started_finished
from backend.utils.fetch_json import fetch_rtt_json
from backend.utils.trains import operator_map
from datetime import datetime
from datetime import timezone, timedelta
import asyncio
from backend.deps import LONDON, UTC

from backend.deps import get_logger

log = get_logger(__name__)


def parse_operator(atocName: str):
    if not atocName:
        return {"code": "Unknown", "color": "#888888"}
    if atocName == "Unknown":
        return {"code": "Unknown", "color": "#888888"}
    if operator_map.get(atocName):
        return operator_map[atocName]
    code = "".join([w[:1].upper() for w in atocName.split(" ")])
    log.warning("Unknown operator:", atocName)
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

    now = datetime.now(tz=LONDON)
    date = now.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)

    # If the time is more than 12 hours behind now, assume it's for the next day (overnight trains)
    if (date - now).total_seconds() < -12 * 60 * 60:
        date += timedelta(days=1)

    return date


def parse_trains(trains: dict) -> StationResponse | None:
    try:
        if not trains.get("services"):
            trains_dict = dict(trains)
            trains_dict.update(
                {
                    "services": [],
                }
            )
            return StationResponse(**trains_dict)

        def process_train(train):
            atoc_name = train.get("atocName")
            if atoc_name == "Unknown" and train.get("atocCode") == "LD":
                atoc_name = "Lumo"

            operator = parse_operator(atoc_name)

            location = train.get("locationDetail", {})
            expected_departure = parse_time(location.get("realtimeDeparture"))
            scheduled_departure = parse_time(location.get("gbttBookedDeparture"))

            expected_arrival = parse_time(location.get("realtimeArrival"))
            scheduled_arrival = parse_time(location.get("gbttBookedArrival"))

            if not expected_departure:
                expected_departure = scheduled_departure
            if not expected_arrival:
                expected_arrival = scheduled_arrival

            if not expected_arrival or not scheduled_arrival:
                delay = (
                    (expected_departure - scheduled_departure).total_seconds()
                    if expected_departure and scheduled_departure
                    else 0
                )
            else:
                delay = (
                    (expected_arrival - scheduled_arrival).total_seconds()
                    if expected_arrival and scheduled_arrival
                    else 0
                )

            if train.get("serviceType") == "train":
                train_dict = dict(train)
                train_dict.update(
                    {
                        "atocCode": operator["code"],
                        "atocColor": operator["color"],
                        "delay": round(delay),
                        "timeTo": "",
                    }
                )
                train_dict["locationDetail"].update(
                    {
                        "expectedDeparture": expected_departure,
                        "scheduledDeparture": scheduled_departure,
                        "expectedArrival": expected_arrival,
                        "scheduledArrival": scheduled_arrival,
                    }
                )
                return Train(**train_dict)
            return None

        processed_trains = [process_train(train) for train in trains["services"]]
        updated_trains = [train for train in processed_trains if train]

        trains_dict = dict(trains)
        trains_dict.update(
            {
                "services": updated_trains,
            }
        )
        return StationResponse(**trains_dict)
    except Exception as error:
        log.error("failed to get departures", error)
        return None


def parse_train(train) -> TrainService | None:
    try:
        atoc_name = train.get("atocName", "")
        if atoc_name == "Unknown" and train.get("atocCode") == "LD":
            atoc_name = "Lumo"
            train["atocName"] = atoc_name
        operator = parse_operator(atoc_name)

        updated_stops: List[ServiceLocation] = []
        now = datetime.now(tz=UTC)

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
            departure_actual = location.get("realtimeDepartureActual")
            if departure_actual is not None:
                departed = departure_actual
            else:
                if expected_departure and expected_departure < now:
                    departed = True

            delay = 0

            if not expected_arrival or not scheduled_arrival:
                delay = (
                    (expected_departure - scheduled_departure).total_seconds()
                    if expected_departure and scheduled_departure
                    else 0
                )
            else:
                delay = (
                    (expected_arrival - scheduled_arrival).total_seconds()
                    if expected_arrival and scheduled_arrival
                    else 0
                )

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
        required_fields = {
            "serviceUid": train.get("serviceUid", ""),
            "runDate": train.get("runDate", ""),
            "serviceType": train.get("serviceType", ""),
            "isPassenger": train.get("isPassenger", False),
            "trainIdentity": train.get("trainIdentity", ""),
            "atocName": train.get("atocName", ""),
            "origin": train.get("origin", []),
            "destination": train.get("destination", []),
        }
        train_dict.update(required_fields)
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
        log.error("failed to get departures", error)
        return None


def get_departures(station_code: str, r: Redis) -> StationResponse | None:
    def fetch(station_code):
        url = f"https://api.rtt.io/api/v1/json/search/{station_code}"
        trains = fetch_rtt_json(url)

        if not trains:
            raise HTTPException(status_code=404, detail="No departures found")

        updated_trains = parse_trains(trains)

        return updated_trains

    trains = get_cached(
        f"trains:departures:{station_code}",
        fetch,
        (station_code,),
        TRAIN_CACHE,
        r,
    )

    return trains


def get_arrivals(station_code: str, r: Redis) -> StationResponse | None:
    def fetch(station_code):
        url = f"https://api.rtt.io/api/v1/json/search/{station_code}/arrivals"
        trains = fetch_rtt_json(url)

        if not trains:
            raise HTTPException(status_code=404, detail="No arrivals found")

        updated_trains = parse_trains(trains)

        return updated_trains

    trains = get_cached(
        f"trains:arrivals:{station_code}",
        fetch,
        (station_code,),
        TRAIN_CACHE,
        r,
    )

    return trains


def get_detailed_route_trains(from_station: str, to_station: str, r: Redis):
    route_result = get_route_trains(from_station, to_station, r)

    if not route_result or not route_result.services:
        return []

    services = route_result.services[:10]

    def fetch_and_process(train):
        service_id = train.serviceUid
        full_train = get_service(
            service_id, r, do_predictions=False, running_date=train.runDate
        )
        if not full_train:
            return None

        locations = full_train.locations

        from_stop = next((loc for loc in locations if loc.crs == from_station), None)
        to_stop = next((loc for loc in locations if loc.crs == to_station), None)
        if not from_stop or not to_stop:
            return None

        if locations.index(from_stop) >= locations.index(to_stop):
            return None

        dep = from_stop.expectedDeparture or from_stop.scheduledDeparture
        arr = to_stop.expectedArrival or to_stop.scheduledArrival

        duration = round((arr - dep).total_seconds()) if dep and arr else None

        full_train.fromStop = from_stop
        full_train.toStop = to_stop
        full_train.duration = duration

        return full_train

    detailed_services = [fetch_and_process(train) for train in services]

    detailed_services = [train for train in detailed_services if train]

    def get_sort_time(x):
        if not x.toStop or not x.toStop.expectedDeparture:
            return datetime.max.replace(tzinfo=timezone.utc)
        return x.toStop.expectedDeparture or x.toStop.scheduledDeparture

    detailed_services.sort(key=get_sort_time)

    return detailed_services


def get_route_trains(
    from_station: str, to_station: str, r: Redis
) -> StationResponse | None:
    def fetch(from_station, to_station):
        url = f"https://api.rtt.io/api/v1/json/search/{from_station}/to/{to_station}"
        trains = fetch_rtt_json(url)

        if not trains:
            raise HTTPException(status_code=404, detail="No route found")

        updated_trains = parse_trains(trains)

        return updated_trains

    trains = get_cached(
        f"trains:route:{from_station}:to:{to_station}",
        fetch,
        (from_station, to_station),
        TRAIN_CACHE,
        r,
    )

    if type(trains) is dict:
        trains = StationResponse(**trains)

    return trains


def get_service(
    service_id: str,
    r: Redis,
    do_predictions: bool = True,
    running_date: str | None = None,
) -> TrainService | None:
    def fetch(service_id):
        if running_date:
            date_str = running_date.replace("-", "/")
        else:
            today = datetime.now(tz=UTC)
            date_str = today.strftime("%Y/%m/%d")
        url = f"https://api.rtt.io/api/v1/json/service/{service_id}/{date_str}"
        train = fetch_rtt_json(url)

        if not train:
            raise HTTPException(status_code=404, detail="Train service not found")

        updated_train = parse_train(train)

        if not updated_train:
            return None

        started, finished = get_started_finished(updated_train, r)

        predictions = None
        if do_predictions:
            predictions = predict_future(updated_train, None, started, 35, r)

        updated_train.started = started
        updated_train.finished = finished
        updated_train.predictions = predictions

        return updated_train

    train = get_cached(
        f"trains:service:{service_id}",
        fetch,
        (service_id,),
        TRAIN_CACHE,
        r,
    )

    if type(train) is dict:
        train = TrainService(**train)

    return train
