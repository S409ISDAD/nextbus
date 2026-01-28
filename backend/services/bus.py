from datetime import datetime, timedelta

from dateutil import parser
from redis import Redis
from sqlalchemy.orm import selectinload

from backend.config import VEHICLES_BASE, API_BASE
from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.models import (
    Journey,
    Service,
    StopTime,
    Stop,
)
from backend.schemas.bus import ScheduledBus, TrackedBus
from backend.schemas.vehicle import Vehicle, VehicleType
from backend.schemas.livery import Livery
from backend.schemas.progress import Progress
from backend.services import stops
from backend.services.caching import BUS_CACHE, get_cached, DAY
from backend.services.prediction import (
    calculate_expected,
    calculate_expected_difference,
    get_started_finished,
    predict_future,
)
from backend.services.services import fetch_active_buses, get_service_info
from backend.services.tracking_confidence import calculate_confidence
from backend.utils.fetch_json import fetch_json
from backend.utils.match_bt import match_trip_journey
from backend.utils.time_taken import time_taken

from backend.deps import get_logger

log = get_logger(__name__)


MANUFACTURERS = [
    "DAF ",
    "ADL ",
    "Volvo ",
    "Wright ",
    "Scania ",
    "VDL ",
    # "Optare ",
    "ADL/TransBus ",
    "Dennis Trident Alexander ",  # wtf
]  # bus manufacturers to strip from bus type names


# from bustimes.org
def format_reg(reg):
    if "-" not in reg:
        if reg[-3:].isalpha():
            return reg[:-3] + " " + reg[-3:]
        if reg[:3].isalpha():
            return reg[:3] + " " + reg[3:]
        if reg[-2:].isalpha():
            return reg[:-2] + " " + reg[-2:]
        if reg[:2].isalpha():
            return reg[:2] + " " + reg[2:]

    return reg


# end from bustimes.org


def get_bus_type(btype):
    for manu in MANUFACTURERS:
        btype = btype.replace(manu, "")  # remove manufacturer from bus type

    return btype


def fetch_vehicle(bus_id, r: Redis) -> Vehicle | None:
    """Fetches specific vehicle from the api"""

    def fetch(bus_id):
        data = fetch_json(API_BASE + f"/vehicles/{bus_id}")

        return data

    # use caching to avoid repeated calls, vehicles don't change often
    data = get_cached(
        f"bus:{bus_id}",
        fetch,
        (bus_id,),
        DAY,
        r,
    )

    if not data:
        return None

    this_bus = Vehicle(
        id=data["id"],
        reg=format_reg(data["reg"]),
        fleet_num=str(data.get("fleet_number", data.get("fleet_code", "Unknown"))),
        vehicle_type=(
            VehicleType(
                id=data["vehicle_type"]["id"],
                name=get_bus_type(data["vehicle_type"]["name"]),
                style=data["vehicle_type"].get("style", None),
                fuel=data["vehicle_type"].get("fuel", "Unknown"),
                double_decker=data["vehicle_type"].get("double_decker", False),
                coach=data["vehicle_type"].get("coach", False),
                electric=data["vehicle_type"].get("electric", False),
            )
            if data.get("vehicle_type")
            else None
        ),
        livery=Livery(
            id=data["livery"].get("id", 0) or 0,
            name=data["livery"].get("name", None),
            left_css=data["livery"].get("left", None),
            right_css=data["livery"].get("right", None),
        ),
        name=data.get("name", None),
        special_features=data.get("special_features", None),
    )

    try:
        return this_bus
    except:  # noqa: E722
        return None


def fetch_active_bus(bus_id, r: Redis):
    """Fetches specific bus"""

    def fetch(bus_id):
        data = fetch_json(VEHICLES_BASE + f"?id={bus_id}")

        return data

    this_bus = get_cached(
        f"livebus:{bus_id}",
        fetch,
        (bus_id,),
        BUS_CACHE,
        r,
    )

    if not this_bus:
        return None

    try:
        return this_bus[0]
    except:  # noqa: E722
        return None


def fetch_bus_trip(service_id, trip_id, r: Redis):
    """Fetches specific bus by service and trip IDs"""

    def fetch(service_id, trip_id):
        data = fetch_json(VEHICLES_BASE + f"?service={service_id}&trip={trip_id}")
        if not data:
            return None

        exact_bus = [
            bus for bus in data if bus.get("trip_id") == trip_id
        ]  # filter exact trip match, as passing in trip_id does not filter. this is because bustimes.org api has quirks

        return exact_bus[0] if exact_bus else None

    this_bus = get_cached(
        f"bus:{service_id}:{trip_id}",
        fetch,
        (service_id, trip_id),
        BUS_CACHE,
        r,
    )

    return this_bus


def fetch_buses(services, stop_id, times, r: Redis) -> list[TrackedBus | ScheduledBus]:
    with SessionLocal() as db:  # open a database session
        active = fetch_active_buses(
            services, r
        )  # fetch all live buses for the given services

        bustimes_times = stops.get_times(
            stop_id, r
        )  # fetch all scheduled times for the stop from bustimes.org

        active_by_trip: dict[int, list[dict]] = (
            {}
        )  # deal with multiple buses on same trip
        if active:
            for bus in active:
                trip_id = bus.get("trip_id")
                active_by_trip.setdefault(trip_id, []).append(bus)
        else:
            log.debug("No active buses")
            active = []

        bus_seen_counts = (
            {bus["id"]: 0 for bus in active} if active else {}
        )  # keep track of how many times we've seen each bus

        final_buses = []

        scheduled_trip_ids = {t["trip_id"] for t in times if t.get("trip_id")}
        not_included = [
            bus
            for bus in bustimes_times
            if bus.get("trip_id") not in scheduled_trip_ids
        ]

        for time in not_included:
            # add buses that are late, and so the scheduled departure time has passed; not included in the main list of times
            # e.g. these buses only appear in the active buses list from bustimes.org
            buses = active_by_trip.get(time.get("trip_id"), [])

            journey = match_trip_journey(
                db, time.get("trip_id"), r
            )  # match bustime.org trip to database journey
            journey_id = journey.id if journey else None
            final_buses.append(
                build_bus_candidates(
                    buses,
                    r,
                    stop_id,
                    journey_id,
                    "api",
                    bus_seen_counts,
                )  # handle multiple buses on same trip
            )

        # preload all StopTime objects beforehand to speed up processing
        stop_time_ids = [t["st"].id for t in times if t.get("source") == "db"]
        preloaded = (
            db.query(StopTime)
            .filter(StopTime.id.in_(stop_time_ids))
            .options(
                selectinload(StopTime.journey).selectinload(Journey.timetable),
                selectinload(StopTime.journey)
                .selectinload(Journey.service)
                .selectinload(Service.operators),
                selectinload(StopTime.journey)
                .selectinload(Journey.destination)
                .selectinload(Stop.locality),
            )
            .all()
        )

        stop_time_map = {
            st.id: st for st in preloaded
        }  # map of StopTime id to StopTime object

        for time in times:
            trip_id = time.get("trip_id")
            journey_id = time.get("journey_id")
            source = time.get("source", "api")
            matched_buses = active_by_trip.get(trip_id, [])
            if matched_buses:
                for bus in matched_buses:
                    bus_seen_counts[
                        bus["id"]
                    ] += 1  # keep track of how many times we've seen each bus
                final_buses.append(
                    build_bus_candidates(
                        matched_buses,
                        r,
                        stop_id,
                        journey_id,
                        source,
                        bus_seen_counts,
                        st_map=stop_time_map,
                    )  #
                )
            else:
                if time.get("source") == "db":
                    final_buses.append(
                        build_scheduled_db(
                            time=time,
                            trip_id=trip_id,
                            st=time.get("st", None),
                            st_map=stop_time_map,
                            r=r,
                        )  # handle multiple buses on same trip
                    )
                else:
                    final_buses.append(build_scheduled(time, r))  # scheduled from api

        final_buses = [
            bus for bus in final_buses if bus is not None
        ]  # filter out ignored buses

        final_map = {}

        # merge scheduled and tracked results as sometimes duplicate entries appear
        # e.g. when there is no bustimes trip ID for a db journey

        for sb in [b for b in final_buses if isinstance(b, ScheduledBus)]:
            # create the base key with common values
            base_key = (
                sb.line,
                sb.started,
                sb.scheduled.replace(second=0, microsecond=0),
            )

            # check if this bus matches an existing bus by trip or journey ID
            matched = False
            for existing_key, existing_bus in list(final_map.items()):
                existing_base = existing_key[:3]
                if existing_base == base_key:
                    # if same line, started, status and time, check if it's the same journey
                    if (
                        sb.trip and existing_bus.trip and sb.trip == existing_bus.trip
                    ) or (
                        sb.db_journey
                        and existing_bus.db_journey
                        and sb.db_journey == existing_bus.db_journey
                    ):
                        matched = True
                        # keep existing, no need to replace scheduled with scheduled
                        break

            if not matched:
                # use destination if journey/trip ID not available
                key = base_key + (sb.trip or 0, sb.db_journey or 0, sb.destination)
                log.debug(f"scheduled bus key: {key}")
                final_map[key] = sb

        for tb in [b for b in final_buses if isinstance(b, TrackedBus)]:
            # create the base key with common values
            base_key = (
                tb.service.line_name,
                tb.started,
                tb.scheduled.replace(second=0, microsecond=0),
            )

            # check if this bus matches an existing bus by trip or journey ID
            matched_key = None
            for existing_key, existing_bus in list(final_map.items()):
                existing_base = existing_key[:3]
                if existing_base == base_key:
                    # if same line, started, status and time, check if it's the same journey
                    if (
                        tb.trip and existing_bus.trip and tb.trip == existing_bus.trip
                    ) or (
                        tb.db_journey
                        and existing_bus.db_journey
                        and tb.db_journey == existing_bus.db_journey
                    ):
                        matched_key = existing_key
                        break

            if matched_key:
                # replace scheduled with tracked
                log.debug(f"tracked bus replacing scheduled with key: {matched_key}")
                tb.journey = None  # to save data transfer
                final_map[matched_key] = tb
            else:
                # new entry, use destination if journey/trip ID not available
                key = base_key + (tb.trip or 0, tb.db_journey or 0, tb.destination)
                log.debug(f"tracked bus key: {key}")
                tb.journey = None  # to save data transfer
                final_map[key] = tb

        to_sort: list[TrackedBus | ScheduledBus] = list(
            final_map.values()
        )  # ignore keys, return values (buses) as list

        return sorted(
            to_sort,
            key=lambda b: (
                b.expected if hasattr(b, "expected") and b.expected else datetime.max
            ),
        )


def fetch_buses_live(services, stop_id, r: Redis) -> list[TrackedBus]:
    # same as fetch_buses but only actively tracked buses
    active = fetch_active_buses(services, r)

    if not active:
        return []

    active_by_trip: dict[int, list[dict]] = {}

    for bus in active:
        trip_id = bus.get("trip_id")
        if trip_id:
            active_by_trip.setdefault(trip_id, []).append(bus)

    final_buses = []

    for trip, buses in active_by_trip.items():
        final_buses.append(build_bus_candidates(buses, r, stop_id))

    return [bus for bus in final_buses if bus is not None]


def build_scheduled(departure: dict, r: Redis, include_started=True):
    """builds a scheduled bus from bustimes.org api response

    Args:
        departure (dict): the departure data from bustimes.org
        r (Redis): redis instance
        include_started (bool, optional): whether to calculate started flag. Defaults to True.

    Returns:
        _type_: _description_
    """

    aimed = departure.get("aimed_departure_time")
    expected_time = departure.get("expected_departure_time")

    if not aimed:
        log.warning("No aimed departure time in scheduled bus")
        return None

    scheduled = parser.isoparse(aimed)

    if expected_time:
        expected = parser.isoparse(expected_time)

    else:
        expected = scheduled  # default to scheduled if expected not provided

    destination = departure.get("destination", {}).get("locality")
    line = departure.get("service", {}).get("line_name")

    trip_id = departure.get("trip_id")

    if include_started:
        started, _ = get_started_finished(
            trip_id, r
        )  # determine if the bus has started the journey
    else:
        started = False

    return ScheduledBus(
        destination=destination,
        line=line,
        scheduled=scheduled,
        expected=expected,
        started=started,
        trip=trip_id,
        db_journey=None,
        status="not_tracking",
        source="api",
    )


def build_scheduled_db(
    time,
    trip_id,
    st: StopTime,
    st_map: dict[int, StopTime],
    r,
    include_started=True,
    get_prev=True,
):
    with SessionLocal() as db:
        stop_time = st_map.get(st.id)  # use preloaded StopTime
        stop_time._dep_dt = st._dep_dt  # ensure departure datetime is set

        if not stop_time:
            log.warning(
                f"StopTime with ID {st.id} not found in DB."
            )  # shouldn't happen
            return None

        if not st._dep_dt:
            log.warning(f"StopTime with ID {st.id} has no _dep_dt.")  # shouldn't happen
            return None

        departure_time: datetime = st._dep_dt
        today = datetime.now(tz=LONDON).date()
        dayshift = time.get("dayshift", 0)
        if dayshift:
            today += timedelta(days=dayshift)  # adjust for dayshift if needed

        headsign = stop_time.headsign
        line_name = stop_time.journey.service.line_name

        if include_started and trip_id:
            started, finished = get_started_finished(trip_id, r)
        else:
            started = False

        scheduled = departure_time

        time_to = (
            scheduled - datetime.now(tz=LONDON)
        ).total_seconds()  # seconds to scheduled time

        if time_to > 2 * 3600:
            get_prev = False  # save processing time

        # if (scheduled - datetime.now(tz=LONDON)).total_seconds() > 11 * 3600:
        #     log.debug("Scheduled too far in future")
        #     return None

        # if not trip_id or trip_id == 0:
        #     trip_id = stop_time.journey.get_bt_trip_id(db)

        dest = headsign

        scheduled_bus = ScheduledBus(
            destination=dest,
            line=line_name,
            scheduled=scheduled,
            expected=scheduled,
            started=started,
            trip=trip_id,
            db_journey=stop_time.journey.id,
            status="not_tracking",
            source="db",
        )  # default scheduled bus

        if get_prev:
            with time_taken("getting previous journey", threshold=1):
                prev_journey = stop_time.journey.get_previous_journey(
                    db, today
                )  # get the journey before this one

            if not prev_journey:
                log.warning("No previous journey")
                return scheduled_bus  # no previous journey, return scheduled bus

            layover_time = (
                stop_time.journey.start_time
                - prev_journey.end_time
                - timedelta(minutes=1)  # load/unload time
                if prev_journey
                else timedelta(0)
            )  # calculate layover time

            prev_trip = prev_journey.get_bt_trip_id(db)  # get previous bustimes trip id

            prev_service_id = prev_journey.service.get_bt_service_id(
                db
            )  # get previous bustimes service id
            this_service_id = stop_time.journey.service.get_bt_service_id(
                db
            )  # get this bustimes service id

            if not prev_trip or not prev_service_id or not this_service_id:
                log.warning(
                    f"no previous trip or service: {prev_trip}, {prev_service_id}, {this_service_id}"
                )
                return scheduled_bus  # missing data, return scheduled bus

            with time_taken("getting service info", threshold=5):
                service_info = get_service_info(this_service_id, r)

            potential_bus = fetch_bus_trip(
                prev_service_id, prev_trip, r
            )  # check if any bus is on the previous trip

            if potential_bus:
                log.debug(
                    f"Found bus from previous trip: {service_info.line_name} {potential_bus['id']}"
                )

                bus = build_bus(potential_bus["id"], r, get_journey=False)
                if not bus:
                    log.warning("Failed to build bus")
                else:
                    delay = max(
                        bus.delay - int(layover_time.total_seconds()), 0
                    )  # account for layover

                    # replace with scheduled bus info
                    bus.destination = dest
                    bus.scheduled = scheduled
                    bus.expected = scheduled + timedelta(seconds=delay)
                    bus.delay = delay
                    bus.trip = trip_id if trip_id != 0 else None
                    bus.db_journey = stop_time.journey.id
                    bus.started = False
                    bus.status = "on_prev_trip"
                    service = service_info if service_info else bus.service
                    bus.service = service
                    bus.confidence.log_off_confidence = 0.0
                    bus.source = "db"

                    # Don't show if expected is more than 2 hours away
                    if (
                        bus.expected - datetime.now(tz=LONDON)
                    ).total_seconds() < 4 * 3600:
                        return bus
                    if (
                        layover_time.total_seconds() > 30 * 60
                    ):  # bus is not necessarily going straight on the next trip, might have to drive there which affects delay
                        log.debug("Layover too long")
                        bus.delay = 0

                    log.debug("Bus expected too far in future")
            else:
                log.debug(f"No potential bus found, {prev_trip}, {prev_service_id}")

        return scheduled_bus


def build_bus_candidates(
    buses: list[dict],
    r: Redis,
    stop_id: str,
    journey_id: int | None = None,
    source: str = "api",
    bus_seen_counts: dict[int, int] | None = None,
    st_map: dict[int, StopTime] | None = None,
) -> TrackedBus | None:
    """builds all buses on the same trip, returns the one that is furthest along the route.

    deals with cases like breakdowns where there is a replacement bus

    Args:
        buses (list[dict]): list of bus dicts
        r (Redis): redis instance
        stop_id (str):
        journey_id (int | None, optional): Defaults to None.
        source (str, optional): "api" or "db". Defaults to "api".
        bus_seen_counts (dict[int, int] | None, optional). Defaults to None.
        st_map (dict[int, StopTime] | None, optional): map of StopTime id to StopTime object. Defaults to None.

    Returns:
        TrackedBus | None: Can return None if no valid bus found
    """

    # build all buses
    results = [
        build_bus(
            bus["id"],
            r,
            stop_id,
            journey_id,
            get_journey=False,
            source=source,
            bus_seen_count=(
                bus_seen_counts.get(bus["id"], 1) if bus_seen_counts else 1
            ),
            pick_up_only=True,
            st_map=st_map,
        )
        for bus in buses
    ]

    valid = [
        bus
        for bus in results
        if bus is not None
        and hasattr(bus, "progress")
        and isinstance(bus.progress.sequence, int)
    ]  # filter out invalid buses

    if not valid:
        return None

    # Return the one with the highest progress.sequence
    return max(valid, key=lambda b: b.progress.sequence)


def build_bus(
    bus_id: int,
    r: Redis,
    stop_id: str = "",
    db_journey_id: int | None = None,
    get_journey: bool = True,
    source: str = "api",
    bus_seen_count: int = 1,
    pick_up_only: bool = False,
    st_map: dict[int, StopTime] | None = None,
    ignore_returns=False,
) -> TrackedBus | None:
    this_bus = fetch_active_bus(bus_id, r)  # fetch live bus data, e.g. delay, coords
    vehicle_data = fetch_vehicle(
        bus_id, r
    )  # fetch vehicle data, e.g. reg, type, livery

    if not this_bus or not vehicle_data:
        return None

    delay = this_bus.get("delay")  # delay (lateness) in seconds

    db_stoptime = None

    if db_journey_id:
        with SessionLocal() as db:
            st_id_row = (
                db.query(StopTime.id)
                .filter(
                    StopTime.journey_id == db_journey_id, StopTime.stop_id == stop_id
                )
                .first()
            )  # get stoptime id for the given journey and stop

            st_id: int | None = st_id_row[0] if st_id_row else None

            if st_id and st_map:
                db_stoptime = st_map.get(st_id)  # use preloaded StopTime

    tracking = True

    if not delay:
        # the bus is not reporting a delay, could be tracking incorrectly
        log.warning(f"No delay for bus id: {bus_id}")
        delay = 0
        tracking = False

    timestamp = this_bus.get("datetime")

    coords = this_bus.get("coordinates", [0, 0])
    journey_id = this_bus.get("journey_id")
    destination = this_bus.get("destination")
    progress = this_bus.get("progress", {})

    reg = vehicle_data.reg if vehicle_data else "Unknown"

    if not ignore_returns:  # special case for whatbus on journey

        # Ignore buses with a delay of over 2 hours, they are likely broken down or similar
        if delay > 2 * 60 * 60:
            log.warning(
                f"ignoring bus with delay of {round(delay / 60)} minutes. id: {bus_id}"
            )
            return None

        # Ignore buses more than 2 hours early, probably logged on to the wrong trip
        if delay < -2 * 60 * 60:
            log.warning(
                f"ignoring bus with delay of {round(delay / 60)} minutes. id: {bus_id}"
            )
            return None

        # Reset delay if earlier than 15 mins, it has probably logged on early
        if delay < -15 * 60:
            log.warning(f"resetting delay, too early. id: {bus_id}, reg: {reg}")
            delay = 0

    r.sadd("total_buses", bus_id)  # track total unique buses seen

    bus_type = vehicle_data.vehicle_type
    if not bus_type.double_decker:
        bus_type = "Single decker"
    else:
        bus_type = "Double decker"

    if vehicle_data.special_features:
        bus_type += f", {', '.join(vehicle_data.special_features)}"  # generate a string like "Double decker, USB-A, USB-C"

    delay += 10  # account for stopping and various other things that increase delay
    confidence = calculate_confidence(
        delay, coords, journey_id, this_bus.get("trip_id"), r
    )

    log.debug(
        f"final={round(confidence.final_confidence, 5)}, brokendown={round(confidence.broken_down_confidence, 5)}, logoff={round(confidence.log_off_confidence, 5)}, diversion={round(confidence.diversion_confidence, 5)}, brokentracking={round(confidence.broken_tracking_confidence, 5)} id={bus_id}, reg={reg}"
    )

    if confidence.broken_tracking_confidence > 0.65:
        log.warning(
            f"bus likely has broken tracking, ignoring delay. id: {bus_id}, reg: {reg}"
        )
        delay = 0

    if confidence.broken_down_confidence > 0.65:
        log.warning(
            f"bus likely has broken down, ignoring delay. id: {bus_id}, reg: {reg}"
        )
        delay = 0

    if confidence.log_off_confidence > 0.65:
        log.warning(
            f"bus likely has finished, ignoring delay. id: {bus_id}, reg: {reg}"
        )
        delay = 0

    target_seq, times, journey = calculate_expected(
        delay,
        progress.get("sequence", 0),
        stop_id,
        journey_id,
        r,
        bus_seen_count,
        pick_up_only,
    )  # get expected times and target sequence

    sequence = progress.get("sequence", None)
    prog = progress.get("progress", None)
    if (
        sequence
        and prog
        and target_seq
        and confidence.final_confidence < 0.75
        and sequence > 5
    ):  # bus may be logging on early
        if (sequence == target_seq and prog >= 0.1) or sequence > target_seq:
            log.info(f"bus has likely passed the stop. id: {bus_id}, reg: {reg}")
            return None  # bus has likely passed the stop

    service_info = get_service_info(journey.service_id, r)

    if not times:
        log.warning(f"no times object. id: {bus_id}, reg: {reg}")  # shouldn't happen
        return None
    if (times.scheduled is None or times.expected is None) and stop_id:
        log.info(
            f"no scheduled time. id: {bus_id}, reg: {reg}"
        )  # failed to generate times, shouldn't happen
        return None
    if not times.include and not ignore_returns:
        log.warning(
            f"not including id: {bus_id}, reg: {reg}"
        )  # bus should not be included, decided by calculate_expected
        return None

    # if times.finished and stop_id:
    #     return None
    if not times.started:
        log.debug(f"bus not started yet. id: {bus_id}, reg: {reg}")
        delay = 0

    if get_journey:
        predictions = predict_future(
            journey, delay, timestamp, times.started, 35, r
        )  # predict bus locations for the next 35 seconds
    else:
        predictions = []

    status = "tracking"

    if not tracking:
        status = "not_tracking"
    if not times.started:
        status = "waiting"

    if times.call_condition == "notStopping":
        log.info(f"bus cancelled. id: {bus_id}, reg: {reg}")
        status = "cancelled"
        if times.expected and times.scheduled:
            delay = 0

            times.expected = times.scheduled + timedelta(
                minutes=30
            )  # show as cancelled for 30 mins after departure time so that everyone sees it

    min_expected = None
    max_expected = None

    if times.started:
        min_expected, max_expected = calculate_expected_difference(
            timestamp, times.expected, times.scheduled
        )  # calculate expected time range based on location age

    if min_expected and times.scheduled and times.expected:
        delay = int((min_expected - times.scheduled).total_seconds())
        if (
            min_expected > times.expected and min_expected > times.scheduled
        ):  # only adjust if min_expected is later than both
            log.debug(
                f"Adjusting expected from {times.expected} to {min_expected}. new delay {delay}"
            )
            times.expected = min_expected

    if db_stoptime:
        # override destination and line name with database values
        destination = db_stoptime.headsign or destination
        service_info.line_name = db_stoptime.journey.service.line_name

    if stop_id:
        # never include journey if asked for a stop, as it is not needed
        journey = None

    return TrackedBus(
        type="tracked",
        id=bus_id,
        service=service_info,
        trip=this_bus.get("trip_id", 0),
        db_journey=db_journey_id,
        timestamp=timestamp,
        destination=destination,
        bus_type=bus_type,
        vehicle=vehicle_data,
        journey_id=journey_id,
        delay=delay,
        expected=times.expected,
        min_expected=min_expected,
        max_expected=max_expected,
        scheduled=times.scheduled,
        started=times.started,
        finished=times.finished,
        target_seq=target_seq,
        progress=(
            progress
            if progress
            else Progress(sequence=0, next_stop="", prev_stop="", progress=0)
        ),
        predictions=predictions,
        journey=journey,
        speed=None,
        confidence=confidence,
        coords=coords,
        heading=this_bus.get("heading", 0) or 0,
        status=status,
        source=source,
    )
