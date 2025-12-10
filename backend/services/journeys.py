from datetime import datetime as dt
from datetime import timedelta

from dateutil.parser import isoparse
from geopy.distance import geodesic
from redis import Redis

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


def seconds_to_datetime(seconds: float, current_time: dt) -> dt:
    """converts seconds since midnight to a datetime relative to the current time

    Args:
        seconds (float): seconds since midnight
        current_time (dt): the current datetime to inherit date

    Returns:
        dt: the converted datetime
    """
    time = timedelta(seconds=seconds)
    time = (dt.min + time).replace(
        tzinfo=LONDON,
        day=current_time.day,
        month=current_time.month,
        year=current_time.year,
    )

    return check_scheduled_time(time, current_time)


def process_times(times: list[dict]) -> list[dict]:
    """processes a list of StopTime objects from bustimes.org, into my own StopTimes

    Args:
        times (list[dict]): list of StopTime dicts from bustimes.org

    Returns:
        list[dict]: the processed list of StopTime dicts
    """

    prev_time = 0
    total_delay = 0

    for i, stop in enumerate(times):
        aimed_key = (
            "aimed_arrival_time" if i == len(times) - 1 else "aimed_departure_time"
        )  # the last stop has no departure time

        aimed = stop.get(aimed_key)
        if aimed:
            aimed_dt = dt.strptime(aimed, "%H:%M")
            scheduled_time = timedelta(
                hours=aimed_dt.hour, minutes=aimed_dt.minute
            )  # convert to timedelta (seconds since midnight)

            expt_time = scheduled_time
            old_expt = expt_time

            track_dist = 0.0

            prev_coords = None
            for coords in stop.get("track", []) or []:
                # get cumulative distance along the track between stops, to get an accurate road distance
                if prev_coords is not None:
                    track_dist += geodesic(prev_coords, tuple(coords)).meters
                prev_coords = tuple(coords)

            if prev_time == expt_time:
                # if 2 stops have the same scheduled time, this adds a small delay based on distance to make times more realistic
                delay_factor = 18  # value i tuned for best results

                extra_delay = round(track_dist / delay_factor)
                total_delay = total_delay + extra_delay
                expt_time += timedelta(seconds=total_delay)
            else:
                total_delay = 0

            prev_time = old_expt

            stop["aimed_time"] = scheduled_time.total_seconds()
            stop["expt_time"] = expt_time.total_seconds()
            stop["track_distance"] = track_dist

    return times


def process_stops(
    json_stops: list[dict], delay: int, current_time: dt
) -> list[StopTime]:
    stops: list[StopTime] = []

    started = False

    for stop_idx, stop in enumerate(json_stops):
        if stop.get("track"):
            track = [[lon_lat[1], lon_lat[0]] for lon_lat in stop.get("track")]
        else:
            track = None

        coords = stop["stop"].get("location", [0, 0])

        coords = [coords[1], coords[0]]

        expt = seconds_to_datetime(float(stop.get("expt_time", 0)), current_time)

        aimed = seconds_to_datetime(float(stop.get("aimed_time", 0)), current_time)

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
                track_distance=stop.get("track_distance", 0.0),
            )
        )

    return stops


def get_vehicle_journey(journey_id: int, delay: int, r: Redis) -> Journey:
    """retrives and parses the bustimes.org Journey

    Args:
        journey_id (int): the journey ID to fetch
        delay (int): the lateness of the vehicle in seconds
        r (Redis): redis instance

    Returns:
        Journey: the parsed Journey object
    """

    def fetch(journey_id: int):
        data = fetch_json(
            API_BASE + f"/vehiclejourneys/{journey_id}/",
        )  # get bustimes.org journey data

        if not data:
            return

        data["times"] = process_times(data["times"])
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

    stops = process_stops(json_stops, delay, current_time)

    return Journey(
        route_name=journey.get("route_name"),
        destination=journey.get("destination"),
        service_id=journey.get("service").get("id"),
        stops=stops,
    )


def get_live_journey(journey_id: int, r: Redis) -> LiveJourney | None:
    """retrives and parses a live vehicle journey from bustimes.org

    Args:
        journey_id (int): ID of the journey
        r (Redis): redis instance

    Returns:
        LiveJourney | None: the parsed LiveJourney object, or None if not found
    """

    def fetch(journey_id):
        """
        Simplified version of process_times
        """
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
            location["coords"] = [
                coords[1],
                coords[0],
            ]  # geojson coords are backwards (lon, lat) instead of (lat, lon)
            location["timestamp"] = isoparse(location["datetime"])

        return data

    live_journey = get_cached(
        key=f"live_journeys:{journey_id}",
        func=fetch,
        args=(journey_id,),
        exp=JOURNEY_CACHE,
        r=r,
    )  # cache to not bombard the API

    if not live_journey:
        log.warning(f"Live journey with ID {journey_id} not found.")
        return None

    json_stops = live_journey.get("stops")
    stops: list[StopTime] = []
    locations: list[Location] = []

    for stop in json_stops:
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
            )  # some values are defaults as they are not provided or needed
        )

    for location in live_journey.get("locations"):
        # generate list of Location objects
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

        data["times"] = process_times(data["times"])
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

    stops = process_stops(json_stops, delay, current_time)

    return Trip(
        route_name=trip.get("service").get("line_name"),
        destination=trip.get("headsign"),
        service_id=trip.get("service").get("id"),
        vehicle_journey_code=trip.get("vehicle_journey_code"),
        ticket_machine_code=trip.get("ticket_machine_code"),
        block=trip.get("block"),
        stops=stops,
    )
