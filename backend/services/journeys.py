import datetime
from datetime import datetime as dt
from datetime import timedelta

from geopy.distance import geodesic

from backend.config import API_BASE
from backend.deps import LONDON, UTC
from backend.schemas.journey import Journey, Trip
from backend.schemas.stop import StopTime
from backend.services.caching import (
    JOURNEY_CACHE,
    get_cached,
)
from backend.utils.fetch_json import fetch_json
from backend.utils.time import check_scheduled_time


async def get_vehicle_journey(journey_id, delay, r) -> Journey:
    async def fetch(journey_id):
        data = await fetch_json(
            API_BASE + f"/vehiclejourneys/{journey_id}/",
        )

        if not data:
            return

        current_time = dt.now(tz=UTC)
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

        # data["stops"] = await recalculate_timetable(data["stops"], journey_id, r)

        # for i, stop in enumerate(data["stops"]):
        #     data["stops"][i]["expt_time"] = data["stops"][i]["aimed_time"] + delay

        return data

    journey = await get_cached(
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
            track = [[lng_lat[1], lng_lat[0]] for lng_lat in stop.get("track")]
        else:
            track = None

        coords = stop["stop"].get("location", [0, 0])

        coords = [coords[1], coords[0]]

        expt = stop.get("expt_time")
        expt = timedelta(seconds=expt)
        expt = (dt.min + expt).replace(
            tzinfo=UTC,
            day=current_time.day,
            month=current_time.month,
            year=current_time.year,
        )
        expt = check_scheduled_time(expt, current_time)

        aimed = stop.get("aimed_time")
        aimed = timedelta(seconds=aimed)
        aimed = (dt.min + aimed).replace(
            tzinfo=UTC,
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

        stops.append(
            StopTime(
                stop_id=stop["stop"].get("atco_code"),
                name=stop["stop"].get("name"),
                aimed_time=aimed,
                expt_time=expt,
                departed=departed,
                track=track,
                coords=coords,
                set_down=stop.get("set_down"),
                timing_status=stop.get("timing_status", "OTH"),
            )
        )

    return Journey(
        route_name=journey.get("route_name"),
        destination=journey.get("destination"),
        service_id=journey.get("service").get("id"),
        stops=stops,
    )


async def get_trip(trip_id, delay, r) -> Trip:
    async def fetch(trip_id):
        data = await fetch_json(
            API_BASE + f"/trips/{trip_id}/",
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

        # data["stops"] = await recalculate_timetable(data["stops"], journey_id, r)

        # for i, stop in enumerate(data["stops"]):
        #     data["stops"][i]["expt_time"] = data["stops"][i]["aimed_time"] + delay

        return data

    trip = await get_cached(
        key=f"trips:{trip_id}",
        func=fetch,
        args=(trip_id,),
        exp=JOURNEY_CACHE,
        r=r,
    )

    json_stops = trip.get("times")
    stops: list[StopTime] = []

    current_time = dt.now(tz=UTC)
    started = False

    for stop_idx, stop in enumerate(json_stops):
        if stop.get("track"):
            track = [[lng_lat[1], lng_lat[0]] for lng_lat in stop.get("track")]
        else:
            track = None

        coords = stop["stop"].get("location", [0, 0])

        coords = [coords[1], coords[0]]

        expt = stop.get("expt_time")
        expt = timedelta(seconds=expt)
        expt = (dt.min + expt).replace(
            tzinfo=UTC,
            day=current_time.day,
            month=current_time.month,
            year=current_time.year,
        )
        expt = check_scheduled_time(expt, current_time)

        aimed = stop.get("aimed_time")
        aimed = timedelta(seconds=aimed)
        aimed = (dt.min + aimed).replace(
            tzinfo=UTC,
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

        stops.append(
            StopTime(
                stop_id=stop["stop"].get("atco_code"),
                name=stop["stop"].get("name"),
                aimed_time=aimed,
                expt_time=expt,
                departed=departed,
                track=track,
                coords=coords,
                set_down=stop.get("set_down"),
            )
        )

    return Trip(
        service_id=trip.get("service").get("id"),
        vehicle_journey_code=trip.get("vehicle_journey_code"),
        ticket_machine_code=trip.get("ticket_machine_code"),
        block=trip.get("block"),
        stops=stops,
    )
