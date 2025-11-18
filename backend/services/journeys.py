from datetime import datetime as dt
from datetime import timedelta

from dateutil.parser import isoparse
from geopy.distance import geodesic

from backend.config import API_BASE, BASE
from backend.deps import LONDON, UTC
from backend.schemas.journey import Journey, Trip, LiveJourney, Location
from backend.schemas.stop import StopTime
from backend.services.caching import (
    JOURNEY_CACHE,
    get_cached,
)
from backend.utils.fetch_json import fetch_json
from backend.utils.time import check_scheduled_time

from backend.deps import get_logger

log = get_logger(__name__)


def get_vehicle_journey(journey_id, delay, r) -> Journey:
    def fetch(journey_id):
        data = fetch_json(
            API_BASE + f"/vehiclejourneys/{journey_id}/",
        )

        if not data:
            return

        prev_time = 0
        total_delay = 0
        times = data["times"]
        for i, stop in enumerate(times):
            aimed_key = (
                "aimed_arrival_time" if i == len(times) - 1 else "aimed_departure_time"
            )

            aimed = stop.get(aimed_key)
            if aimed:
                aimed_dt = dt.strptime(aimed, "%H:%M")
                scheduled_time = timedelta(hours=aimed_dt.hour, minutes=aimed_dt.minute)

                expt_time = scheduled_time
                old_expt = expt_time

                if prev_time == expt_time:
                    coords_prev = tuple(times[i - 1]["stop"]["location"])
                    coords_next = tuple(stop["stop"]["location"])
                    dist_m = geodesic(coords_prev, coords_next).m

                    delay_factor = 18

                    extra_delay = round(dist_m / delay_factor)
                    total_delay = total_delay + extra_delay
                    expt_time += timedelta(seconds=total_delay)
                else:
                    total_delay = 0

                prev_time = old_expt

                stop["aimed_time"] = scheduled_time.total_seconds()
                stop["expt_time"] = expt_time.total_seconds()

        # data["stops"] = recalculate_timetable(data["stops"], journey_id, r)

        # for i, stop in enumerate(data["stops"]):
        #     data["stops"][i]["expt_time"] = data["stops"][i]["aimed_time"] + delay

        return data

    journey = get_cached(
        key=f"journeys:{journey_id}",
        func=fetch,
        args=(journey_id,),
        exp=JOURNEY_CACHE,
        r=r,
    )

    json_stops = journey.get("times")
    stops: list[StopTime] = []

    current_time = dt.now(tz=UTC)

    started = False

    for stop_idx, stop in enumerate(json_stops):
        if stop.get("track"):
            track = [[lon_lat[1], lon_lat[0]] for lon_lat in stop.get("track")]
        else:
            track = None

        coords = stop["stop"].get("location", [0, 0])

        coords = [coords[1], coords[0]]

        expt = stop.get("expt_time")
        expt = timedelta(seconds=expt)
        expt = (dt.min + expt).replace(
            tzinfo=LONDON,
            day=current_time.day,
            month=current_time.month,
            year=current_time.year,
        )
        expt = check_scheduled_time(expt, current_time)

        aimed = stop.get("aimed_time")
        aimed = timedelta(seconds=aimed)
        aimed = (dt.min + aimed).replace(
            tzinfo=LONDON,
            day=current_time.day,
            month=current_time.month,
            year=current_time.year,
        )

        aimed = check_scheduled_time(aimed, current_time)

        if stop_idx == 0:
            if aimed < current_time:
                started = True

        reset_early = True if stop["timing_status"] == "PTP" else False

        if delay < 0 and reset_early:
            delay = 0

        if started:
            expt += timedelta(seconds=delay)

        departed = False
        if expt < current_time:
            departed = True

        if stop.get("timing_status") == "":
            stop["timing_status"] = "OTH"

        stops.append(
            StopTime(
                stop_id=stop["stop"].get("atco_code"),
                name=stop["stop"].get("name"),
                aimed_time=aimed,
                expt_time=expt,
                departed=departed,
                track=track,
                coords=coords,
                set_down=stop.get("set_down", True),
                pick_up=stop.get("pick_up", True),
                timing_status=stop.get("timing_status", "OTH"),
                call_condition=stop.get("call_condition", None),
            )
        )

    return Journey(
        route_name=journey.get("route_name"),
        destination=journey.get("destination"),
        service_id=journey.get("service").get("id"),
        stops=stops,
    )


def get_live_journey(journey_id, r) -> LiveJourney | None:
    def fetch(journey_id):
        data = fetch_json(
            BASE + f"/journeys/{journey_id}.json",
        )

        if not data:
            return

        locations = data["locations"]
        times = data["stops"]
        for i, stop in enumerate(times):
            aimed_key = (
                "aimed_arrival_time" if i == len(times) - 1 else "aimed_departure_time"
            )

            aimed = stop.get(aimed_key)
            if aimed:
                aimed_dt = dt.strptime(aimed, "%H:%M")
                scheduled_time = timedelta(hours=aimed_dt.hour, minutes=aimed_dt.minute)

                expt_time = scheduled_time

                stop["aimed_time"] = scheduled_time.total_seconds()
                stop["expt_time"] = expt_time.total_seconds()

        for i, location in enumerate(locations):
            coords = location["coordinates"]
            location["coords"] = [coords[1], coords[0]]  # geojson is backwards
            location["timestamp"] = isoparse(location["datetime"])

        return data

    live_journey = get_cached(
        key=f"live_journeys:{journey_id}",
        func=fetch,
        args=(journey_id,),
        exp=JOURNEY_CACHE,
        r=r,
    )

    if not live_journey:
        log.warning(f"Live journey with ID {journey_id} not found.")
        return None

    json_stops = live_journey.get("stops")
    stops: list[StopTime] = []
    locations: list[Location] = []

    for stop_idx, stop in enumerate(json_stops):
        departed = False
        if stop.get("actual_departure_time"):
            departed = True
        stops.append(
            StopTime(
                stop_id=stop.get("atco_code"),
                name=stop.get("name"),
                aimed_time=stop.get("aimed_time"),
                expt_time=stop.get("expt_time"),
                departed=departed,
                track=None,
                coords=[0, 0],
                set_down=False,
                pick_up=False,
                timing_status="OTH",
            )
        )

    for location in live_journey.get("locations"):
        locations.append(
            Location(
                coords=location.get("coords"),
                direction=location.get("direction") or 0,
                timestamp=location.get("timestamp"),
            )
        )

    return LiveJourney(
        current=live_journey.get("current"),
        vehicle_id=live_journey.get("vehicle_id"),
        trip_id=live_journey.get("trip_id"),
        start_time=isoparse(live_journey.get("datetime")),
        route_name=live_journey.get("route_name"),
        destination=live_journey.get("destination"),
        service_id=live_journey.get("service_id"),
        locations=locations,
        stops=stops,
    )


def get_trip(trip_id, delay, r) -> Trip | None:
    def fetch(trip_id):
        data = fetch_json(
            API_BASE + f"/trips/{trip_id}/",
        )

        if not data:
            return None

        prev_time = 0
        total_delay = 0
        times = data["times"]
        for i, stop in enumerate(times):
            aimed_key = (
                "aimed_arrival_time" if i == len(times) - 1 else "aimed_departure_time"
            )

            aimed = stop.get(aimed_key)
            if aimed:
                aimed_dt = dt.strptime(aimed, "%H:%M")
                scheduled_time = timedelta(hours=aimed_dt.hour, minutes=aimed_dt.minute)

                expt_time = scheduled_time
                old_expt = expt_time

                if prev_time == expt_time:
                    coords_prev = tuple(times[i - 1]["stop"]["location"])
                    coords_next = tuple(stop["stop"]["location"])
                    dist_m = geodesic(coords_prev, coords_next).m

                    delay_factor = 18

                    extra_delay = round(dist_m / delay_factor)
                    total_delay = total_delay + extra_delay
                    expt_time += timedelta(seconds=total_delay)
                else:
                    total_delay = 0

                prev_time = old_expt

                stop["aimed_time"] = scheduled_time.total_seconds()
                stop["expt_time"] = expt_time.total_seconds()

        # data["stops"] = recalculate_timetable(data["stops"], journey_id, r)

        # for i, stop in enumerate(data["stops"]):
        #     data["stops"][i]["expt_time"] = data["stops"][i]["aimed_time"] + delay

        return data

    trip = get_cached(
        key=f"trips:{trip_id}",
        func=fetch,
        args=(trip_id,),
        exp=JOURNEY_CACHE,
        r=r,
    )

    if not trip:
        log.warning(f"Trip with ID {trip_id} not found.")
        return None

    json_stops = trip.get("times")
    stops: list[StopTime] = []

    current_time = dt.now(tz=UTC)
    started = False

    for stop_idx, stop in enumerate(json_stops):
        if stop.get("track"):
            track = [[lon_lat[1], lon_lat[0]] for lon_lat in stop.get("track")]
        else:
            track = None

        coords = stop["stop"].get("location", [0, 0])

        coords = [coords[1], coords[0]]

        expt = stop.get("expt_time")
        expt = timedelta(seconds=expt)
        expt = (dt.min + expt).replace(
            tzinfo=LONDON,
            day=current_time.day,
            month=current_time.month,
            year=current_time.year,
        )
        expt = check_scheduled_time(expt, current_time)

        aimed = stop.get("aimed_time")
        aimed = timedelta(seconds=aimed)
        aimed = (dt.min + aimed).replace(
            tzinfo=LONDON,
            day=current_time.day,
            month=current_time.month,
            year=current_time.year,
        )

        aimed = check_scheduled_time(aimed, current_time)

        if stop_idx == 0:
            if aimed < current_time:
                started = True

        if started:
            expt += timedelta(seconds=delay)

        departed = False
        if expt < current_time:
            departed = True

        if stop.get("timing_status") == "":
            stop["timing_status"] = "OTH"

        stops.append(
            StopTime(
                stop_id=stop["stop"].get("atco_code"),
                name=stop["stop"].get("name"),
                aimed_time=aimed,
                expt_time=expt,
                departed=departed,
                track=track,
                coords=coords,
                set_down=stop.get("set_down", True),
                pick_up=stop.get("pick_up", True),
                timing_status=stop.get("timing_status", "OTH"),
                call_condition=stop.get("call_condition", None),
            )
        )

    return Trip(
        route_name=trip.get("service").get("line_name"),
        destination=trip.get("headsign"),
        service_id=trip.get("service").get("id"),
        vehicle_journey_code=trip.get("vehicle_journey_code"),
        ticket_machine_code=trip.get("ticket_machine_code"),
        block=trip.get("block"),
        stops=stops,
    )
