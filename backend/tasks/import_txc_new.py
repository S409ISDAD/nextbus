import gc
from hashlib import sha256
import hashlib
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from geoalchemy2.shape import from_shape, to_shape
from shapely import MultiLineString, Point
from shapely.geometry import LineString
from sqlalchemy import and_, func, select, update
from sqlalchemy_searchable import sync_trigger

from titlecase import titlecase

from backend.config import setup_logging
from backend.db.db import SessionLocal, engine
from backend.deps import LONDON, STATIC_DATA_DIR
from backend.models import (
    BankHoliday,
    Calendar,
    CalendarException,
    CalendarToBankHoliday,
    DataSource,
    Journey,
    Service,
    Operator,
    Timetable,
    Stop,
    StopTime,
    RouteLink,
    ServiceStopUsage,
    TimetableDataSource,
)
from backend.transxchange import txc
from backend.utils.bulk_upsert import bulk_upsert
from backend.utils.download_if_modified import download_if_modified
import logging

from backend.utils.time import to_datetime
from backend.utils.time_taken import time_taken
from sqlalchemy import or_, exists
from sqlalchemy.orm import aliased

log = logging.getLogger(__name__)


async def import_datasource(id, folder: Path):
    logs: dict[datetime, str] = {}
    with SessionLocal() as db:
        datasource = db.query(DataSource).filter(DataSource.id == id).first()
        name = datasource.name if datasource else "Unknown"

        if not datasource:
            log.debug(f"No DataSource with id {id} found.")
            logs[datetime.now(tz=LONDON)] = f"No DataSource with id {id} found."
            return

        logs[datetime.now(tz=LONDON)] = (
            f"Trying to import data source {name} from {datasource.url}"
        )

        path = download_if_modified(datasource, folder / f"txc_source_{id}.zip")

    if path:
        logs[datetime.now(tz=LONDON)] = f"Importing data from {path}..."
        log.debug(f"Importing data from {path}")

        await import_txc_zip(folder / f"txc_source_{id}.zip", id)

        logs[datetime.now(tz=LONDON)] = f"Import completed for data source {name}"
        log.debug(f"Import completed for data source {name}")

    else:
        logs[datetime.now(tz=LONDON)] = f"No updates for data source {name}"
        log.debug(f"No updates for data source {name}")

    log_dir = folder / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"import_log_{id}.log"

    log_file.touch()

    with log_file.open("w") as f:
        for ts, txc_log in logs.items():
            f.write(f"{ts.strftime('%d/%m/%Y, %H:%M:%S')} - {txc_log}\n")


async def import_txc_zip(zip_path, ds_id=None):
    start = time.time()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            xml_files = [
                filename for filename in zf.namelist() if filename.endswith(".xml")
            ]

            total = len(xml_files)

            for filename in xml_files:
                with zf.open(filename) as xml_file:
                    log.debug(
                        f"Processing file: {filename} ({xml_files.index(filename) + 1}/{total})"
                    )
                    txc_importer = TXCImporter(xml_file, ds_id=ds_id)
                    await txc_importer.handle_txc_file()
                    del txc_importer
                    gc.collect()
    finally:
        end = time.time()
        time_taken = end - start
        duration = ""
        if time_taken >= 3600:
            hours = int(time_taken // 3600)
            minutes = int((time_taken % 3600) // 60)
            duration = f"{hours}h {minutes}m"
        elif time_taken >= 60:
            minutes = int(time_taken // 60)
            seconds = int(time_taken % 60)
            duration = f"{minutes}m {seconds}s"
        else:
            duration = f"{int(time_taken)}s"
        log.debug(f"Total TXC Import completed in {duration}")
        log.debug(f"Removing data source file {zip_path}")
        try:
            zip_path.unlink()
        except Exception as e:
            log.debug(f"Error removing file: {e}")
        log.debug("Updating search vectors...")
        with engine.begin() as conn:
            sync_trigger(
                conn,
                "service",
                "search_vector",
                [
                    "description",
                    "origin",
                    "destination",
                    "vias",
                    "line_names",
                ],
            )
            sync_trigger(
                conn,
                "operator",
                "search_vector",
                ["name", "noc"],
            )
            sync_trigger(
                conn,
                "line",
                "search_vector",
                [
                    "line_name",
                    "inbound_description",
                    "outbound_description",
                ],
            )


# def import_txc_zip(zip_path):
#     with zipfile.ZipFile(zip_path, "r") as zf:
#         for filename in zf.namelist():
#             if filename.endswith(".xml"):
#                 with zf.open(filename) as xml_file:
#                     log.debug(f"Processing file: {filename}")
#                     txc_importer = TXCImporter(xml_file)
#                     txc_importer.handle_txc_file()


class TXCOperator:
    """A TransXChange Operator."""

    def __init__(self, element):
        self.id = element.get("id")
        self.noc = element.findtext("NationalOperatorCode")
        self.operator_code = element.findtext("OperatorCode")
        self.operator_short_name = element.findtext("OperatorShortName")
        self.trading_name = element.findtext("TradingName")
        self.licence_number = element.findtext("LicenceNumber")
        self.element = element

    @property
    def name(self):
        return self.operator_short_name or self.trading_name

    def __str__(self):
        return self.noc if self.noc else self.operator_code


def getOperators(operatorsElement):
    operators = {}
    for operatorElement in operatorsElement:
        operator = TXCOperator(operatorElement)
        operators[operator.id] = operator
    return operators


# a callback for titlecase
def initialisms(word, **kwargs):
    if word in ("YMCA", "PH"):
        return word


def get_description(txc_service: txc.Service):
    """
    Generate a valid description for a service.
    from bustimes.org's import_transxchange.py
    """
    description = txc_service.description

    if description and description.isupper():
        description = titlecase(description, callback=initialisms)

    origin = txc_service.origin
    destination = txc_service.destination

    if origin and destination:
        if origin[:4].isdigit() and destination[:4].isdigit():
            print(origin, destination)

        if origin.isupper() and destination.isupper():
            txc_service.origin = origin = titlecase(origin, callback=initialisms)
            txc_service.destination = destination = titlecase(
                destination, callback=initialisms
            )

        if not description:
            description = f"{origin} - {destination}"
            vias = txc_service.vias
            if vias:
                if all(via.isupper() for via in vias):
                    vias = [titlecase(via, callback=initialisms) for via in vias]
                if len(vias) == 1:
                    via = vias[0]
                    if "via " in via:
                        return f"{description} {via}"
                    elif "," in via or " and " in via or "&" in via:
                        return f"{description} via {via}"
                description = " - ".join([origin] + vias + [destination])
    return description


def get_service_data(path):
    txc_data = TransXChangeMeta(path)
    operators = getOperators(txc_data.operators)

    log.debug(operators)

    revision_num = txc_data.attributes.get("RevisionNumber")
    filename = txc_data.attributes.get("FileName")

    services = []

    for service in txc_data.services.values():
        service_id = service.service_code
        operator = operators[service.operator].noc

        services.append([operator, service_id, revision_num])

    return services


def generate_txc_map(dataset: Path):
    txc_map = {}

    files = dataset.glob("*.xml")
    for file in files:
        log.debug(file)

        services = get_service_data(file)
        for service in services:
            operator, service_id, revision_num = service

            log.debug(service)
            if service_id in txc_map:
                if revision_num in txc_map[service_id]:
                    txc_map[service_id][revision_num].append(file.as_posix())
                else:
                    txc_map[service_id][revision_num] = [file.as_posix()]
            else:
                txc_map[service_id] = {revision_num: [file.as_posix()]}
    return txc_map


class ServiceMeta:
    def __init__(self, element):
        self.operator = element.findtext("RegisteredOperatorRef")
        self.service_code = element.find("ServiceCode").text.strip()


class TransXChangeMeta:
    def __init__(self, open_file):
        iterator = txc.ET.iterparse(open_file)

        self.services = {}

        last_elem = None

        for _, element in iterator:
            if element.tag[:33] == "{http://www.transxchange.org.uk/}":
                element.tag = element.tag[33:]
            tag = element.tag

            if tag == "Operators":
                self.operators = element
            elif tag == "Services":
                for service_element in element:
                    service = ServiceMeta(
                        service_element,
                    )
                    self.services[service.service_code] = service
                # break
            last_elem = element
        if last_elem is not None:
            self.attributes = last_elem.attrib


class TXCImporter:
    def __init__(self, folder: Path, ds_id=None):
        self.txc_data = None
        self.dataset = folder
        self.filename = None
        self.file_hash = None
        self.file_size_bytes = None
        self.today = datetime.now(tz=LONDON)
        self.calendar_cache = {}
        self.db = SessionLocal()
        self.journeys_to_add = []
        self.stop_times_to_add = []
        self.service_to_routes = {}  # Maps line_id to a list of route IDs
        self.line_to_stops = {}  # Maps line_id to a list of stop IDs
        self.ds_id = ds_id
        self.tds_id = None
        self.map = {}
        self.stops: dict[str, Stop] = {}

    def generate_txc_map(self):
        txc_map = {}

        for file in self.dataset.glob("*.xml"):
            log.debug(file)

            services = get_service_data(file)
            for service in services:
                operator, service_id, revision_num = service

                log.debug(service)
                if service_id in txc_map:
                    if revision_num in txc_map[service_id]:
                        txc_map[service_id][revision_num].append(file.as_posix())
                    else:
                        txc_map[service_id][revision_num] = [file.as_posix()]
                else:
                    txc_map[service_id] = {revision_num: [file.as_posix()]}
        self.map = txc_map

    def clear_old_routes(self, service_code):
        log.debug("Clearing old routes...")

        routes_to_go = (
            self.db.query(Timetable)
            .filter(
                Timetable.service_id == service_code,
                Timetable.data_source_id == self.ds_id,
                Timetable.end_date is not None,
                Timetable.end_date
                > self.today.date(),  # route is inactive if end_date is in the past (inclusive)
            )
            .all()
        )
        if routes_to_go:
            log.info(f"Deleting {len(routes_to_go)} stale routes...")
            for route in routes_to_go:
                self.db.delete(route)
            self.db.commit()
        else:
            log.debug("No old routes to clear.")

    def get_calendar_exception(
        self,
        date_range: txc.DateRange | None = None,
        date=None,
        operation=True,
        description="",
    ):
        if date_range:
            start_date = date_range.start
            end_date = date_range.end
            description = date_range.description
        else:
            start_date = date
            end_date = date

        return CalendarException(
            start_date=start_date,
            end_date=end_date,
            description=description,
            operating=operation,
        )

    def handle_journey(
        self,
        txc_journey: txc.VehicleJourney,
        txc_service: txc.Service,
        service: Service,
        route: Timetable,
    ):
        operating_profile = txc_journey.operating_profile
        regular_days_of_week = (
            operating_profile.regular_days if operating_profile else []
        )

        calendar_hash = f"{operating_profile.hash}{txc_service.operating_period}"

        if calendar_hash in self.calendar_cache:
            calendar = self.calendar_cache[calendar_hash]
        else:
            calendar = Calendar(
                start_date=txc_service.operating_period.start,
                end_date=txc_service.operating_period.end or None,
                monday="monday" in regular_days_of_week,
                tuesday="tuesday" in regular_days_of_week,
                wednesday="wednesday" in regular_days_of_week,
                thursday="thursday" in regular_days_of_week,
                friday="friday" in regular_days_of_week,
                saturday="saturday" in regular_days_of_week,
                sunday="sunday" in regular_days_of_week,
            )
            self.db.add(calendar)
            self.db.flush()

            for non_operation in operating_profile.nonoperation_days:
                cal_exep = self.get_calendar_exception(
                    date_range=non_operation,
                    operation=False,
                )
                cal_exep.calendar_id = calendar.id
                self.db.add(cal_exep)

            for operation in operating_profile.operation_days:
                cal_exep = self.get_calendar_exception(
                    date_range=operation,
                    operation=True,
                )
                cal_exep.calendar_id = calendar.id
                self.db.add(cal_exep)

            for working_day in txc_journey.operating_profile.serviced_organisations:
                cal_exep = self.get_calendar_exception(
                    date_range=working_day,
                    operation=True,
                )
                cal_exep.calendar_id = calendar.id
                self.db.add(cal_exep)

            bank_holidays_operation = operating_profile.operation_bank_holidays
            bank_holidays_non_operation = operating_profile.nonoperation_bank_holidays

            for days, operating in [
                (bank_holidays_operation, True),
                (bank_holidays_non_operation, False),
            ]:
                for day in days:
                    bh = self.db.query(BankHoliday).filter_by(name=day).first()
                    if not bh:
                        bh = BankHoliday(name=day)
                        self.db.add(bh)
                        self.db.flush()
                    ctbh = CalendarToBankHoliday(
                        operating=operating,
                        calendar_id=calendar.id,
                        bank_holiday_id=bh.id if bh else None,
                    )
                    self.db.add(ctbh)

            self.calendar_cache[calendar_hash] = calendar

        journey_pattern = txc_service.journey_patterns.get(txc_journey.journey_pattern)
        journey_pattern_section = self.txc_data.journey_pattern_sections[
            journey_pattern.journey_pattern_section_refs[0]
        ]

        start_time = txc_journey.departure_time

        stop_sequence = {}

        stops: dict[str, dict] = {}

        route_link_refs = [
            self.get_id(journey_pattern_section.timing_links[tl_ref].route_link_ref)
            for tl_ref in journey_pattern_section.timing_links
            if journey_pattern_section.timing_links[tl_ref].route_link_ref
        ]
        track_sections = (
            self.db.query(TrackSection)
            .filter(TrackSection.route_link_ref.in_(route_link_refs))
            .all()
        )
        track_section_map = {str(ts.route_link_ref): ts for ts in track_sections}

        last_to_stop = None
        last_to_seq = None

        for timing_link in txc_journey.timing_links:
            journey_pattern_timing_link = journey_pattern_section.timing_links.get(
                timing_link.journey_pattern_timing_link_ref
            )
            if not journey_pattern_timing_link:
                continue
            track_section = track_section_map.get(
                self.get_id(journey_pattern_timing_link.route_link_ref)
            )

            from_stop = journey_pattern_timing_link.from_stop
            from_seq = journey_pattern_timing_link.from_stop.sequence_number
            to_stop = journey_pattern_timing_link.to_stop
            to_seq = journey_pattern_timing_link.to_stop.sequence_number

            headsign = to_stop.dynamic_destination_display

            if from_stop and to_stop:
                stop_sequence[from_stop.stop_point_ref] = int(from_seq)
                stop_sequence[to_stop.stop_point_ref] = int(to_seq)

            stops[from_stop.stop_point_ref] = {
                "activity": from_stop.activity,
                "timing_status": from_stop.timing_status,
                "runtime": self.parse_runtime(timing_link.run_time),
                "headsign": headsign,
                "distance": track_section.distance if track_section else 0.0,
            }

            last_to_stop = to_stop
            last_to_seq = to_seq

        if last_to_stop:
            stop_ref = last_to_stop.stop_point_ref
            if stop_ref not in stops:
                stops[stop_ref] = {
                    "activity": last_to_stop.activity,
                    "timing_status": last_to_stop.timing_status,
                    "headsign": last_to_stop.dynamic_destination_display,
                    "runtime": timedelta(0),
                    "distance": 0.0,
                }

            if stop_ref not in stop_sequence and last_to_seq is not None:
                stop_sequence[stop_ref] = int(last_to_seq)

        cumulative_distance = 0.0
        cumulative_time = start_time

        for stop_code in stops.keys():
            self.line_to_stops.setdefault(line.id, set()).add(stop_code)

        sorted_stops = sorted(
            stops.items(), key=lambda item: stop_sequence.get(item[0], 0)
        )

        for i, (stop_ref, stop_data) in enumerate(sorted_stops, start=1):
            seq = i
            stop_data = stops.get(stop_ref)

            activity = stop_data.get("activity") if stop_data else None
            pick_up = "pickup" in activity.lower() if activity else False
            drop_off = "setdown" in activity.lower() if activity else False
            stoptime = {
                "journey_id": journey_code,
                "stop_id": stop_ref,
                "pick_up": pick_up,
                "drop_off": drop_off,
                "departure_time": cumulative_time,
                "arrival_time": cumulative_time,
                "stop_sequence": seq,
                "dest_display": stop_data["headsign"],
                "distance_traveled": cumulative_distance,
                "timing_status": stop_data["timing_status"]
                if stop_data and "timing_status" in stop_data
                else None,
                "wait_time": timedelta(0),
            }
            self.stop_times_to_add.append(stoptime)
            cumulative_time += (
                stop_data["runtime"]
                if stop_data and "runtime" in stop_data
                else timedelta(0)
            )
            cumulative_distance += stop_data["distance"] if stop_data else 0.0

        first_stop = sorted_stops[0][0]
        final_stop = sorted_stops[-1][0]
        headsign = next(
            (stop[1]["headsign"] for stop in sorted_stops if stop[1]["headsign"]), ""
        )

        journey = {
            "id": journey_code,
            "service_code": service.service_code,
            "vehicle_journey_code": txc_journey.journey_code,
            "ticket_machine_code": txc_journey.ticket_machine_code,
            "line_id": line.id,
            "block_id": txc_journey.block,
            "headsign": headsign,
            "origin_stop_id": first_stop,
            "destination_stop_id": final_stop,
            "direction": journey_pattern.direction if journey_pattern else None,
            "start_time": start_time,
            "end_time": cumulative_time,
            "calendar_id": calendar.id,
        }
        self.journeys_to_add.append(journey)

        self.db.flush()

    def handle_service(self, txc_service: txc.Service):
        skip_journeys = False

        end_date = (
            txc_service.operating_period.end if txc_service.operating_period else None
        )

        if end_date and end_date < self.today.date():
            log.debug(
                f"Skipping journeys for {txc_service.service_code} as it ended on {end_date}"
            )
            skip_journeys = True

        description = get_description(txc_service)
        log.debug(f"{txc_service.lines[0].line_name} {description}")

        if description == "Origin - Destination":
            description = ""

        # from bustimes.org's import_transxchange.py
        if re.match(r"^P[BCDFGHKM]\d+:\d+.*$", txc_service.service_code) or re.match(
            r"^UZ[a-zA-Z0-9]+:.*$", txc_service.service_code
        ):
            unique_service_code = txc_service.service_code
        else:
            unique_service_code = None
        # end from

        service = None

        operator = self.db.query(Operator).filter_by(ref=txc_service.operator).first()

        timetable_datasource = (
            self.db.query(TimetableDataSource)
            .filter_by(file_hash=self.file_hash, data_source_id=self.ds_id)
            .first()
        )

        if not timetable_datasource:
            timetable_datasource = TimetableDataSource(
                filename=self.filename,
                file_hash=self.file_hash,
                size_bytes=self.file_size_bytes,
                data_source_id=self.ds_id,
                processed_at=self.today,
            )
            self.db.add(timetable_datasource)
            self.db.flush()
        else:
            log.info(f"No changes to timetable data source {self.filename}, skipping")
            return

        routes = set()

        for txc_line in txc_service.lines:
            txc_line.line_name = txc_line.line_name.replace("_", " ").strip()

            existing_service = (
                self.db.query(Service)
                .filter(
                    Service.line_name.ilike(txc_line.line_name),
                    Service.service_code == txc_service.service_code,
                )
                .order_by(
                    Service.current.desc(), Service.id.asc()
                )  # speed up lookup by preferring current services
                .first()
            )

            if existing_service:
                service = existing_service
            else:
                service = Service(
                    line_name=txc_line.line_name,
                    service_code=txc_service.service_code,
                    current=True,
                    data_source_id=self.ds_id,
                )

            journeys = self.txc_data.get_journeys(
                txc_service.service_code, line_id=txc_line.id
            )

            if not journeys:
                log.warning(
                    f"No journeys found for service {txc_service.service_code} on line {txc_line.id}"
                )
                continue

            # from bustimes.org's import_transxchange.py
            match txc_service.public_use:
                case "0" | "false":
                    service.public_use = False
                case "1" | "true":
                    service.public_use = True
                case _:
                    service.public_use = None
            # end from

            line_brand = txc_line.line_brand or txc_line.marketing_name

            # from bustimes.org's import_transxchange.py (modified)
            if line_brand:
                if service.description:
                    service.description = service.description.removesuffix(
                        f" [{txc_line.line_brand}]"
                    )
            # end from

            if line_brand:
                service.line_brand = line_brand

            service.operator_noc = operator.noc if operator else None

            self.db.add(service)
            self.db.flush()

            timetable_defaults = {
                "service_id": service.id,
                "line_id": txc_line.id,
                "data_source_id": self.ds_id,
                "timetable_data_source_id": timetable_datasource.id,
                "line_name": txc_line.line_name,
                "line_brand": line_brand,
                "outbound_description": txc_line.outbound_description or "",
                "inbound_description": txc_line.inbound_description or "",
                "start_date": txc_service.operating_period.start,
                "end_date": txc_service.operating_period.end,
                "revision_number": self.txc_data.attributes["RevisionNumber"],
                "created_at": to_datetime(self.txc_data.attributes["CreationDateTime"]),
                "modified_at": to_datetime(
                    self.txc_data.attributes["ModificationDateTime"]
                ),
                "public_use": service.public_use,
                "service_code": txc_service.service_code,
            }

            if description:
                timetable_defaults["description"] = description

            if txc_service.vias:
                timetable_defaults["vias"] = ", ".join(txc_service.vias)

            # TODO: finish this

            timetable_id = 1  # replace with actual timetable id

            if self.txc_data.route_sections:
                self.handle_route_links(journeys, timetable_id)

    def get_route_links(self, journeys: list[txc.VehicleJourney]):
        """
        Gets all route links associated with the given journeys.
        From bustimes.org's import_transxchange.py, modified.
        """
        patterns = {
            journey.journey_pattern.id: journey.journey_pattern for journey in journeys
        }
        route_refs = [
            pattern.route_ref for pattern in patterns.values() if pattern.route_ref
        ]
        if route_refs:
            routes = [
                self.txc_data.routes[route_id]
                for route_id in self.txc_data.routes
                if route_id in route_refs
            ]
            for route in routes:
                for section_ref in route.route_section_refs:
                    route_section = self.txc_data.route_sections[section_ref]
                    for route_link in route_section.links:
                        if route_link.track:
                            yield route_link
        else:
            route_links = {}
            for route_section in self.txc_data.route_sections.values():
                for route_section_link in route_section.links:
                    route_links[route_section_link.id] = route_section_link
            for journey in journeys:
                if journey.journey_pattern:
                    for section in journey.journey_pattern.sections:
                        for timing_link in section.timinglinks:
                            try:
                                route_link = route_links[timing_link.route_link_ref]
                            except KeyError:
                                continue
                            if route_link.track:
                                yield route_link

    def handle_route_links(self, journeys, timetable_id: int):
        route_links = list(self.get_route_links(journeys))

        if any(
            len(link.track) > 2 for link in route_links
        ):  # from bustimes.org's import_transxchange.py - ignore straight lines
            links_to_add = []

            for link in route_links:
                from_stop = self.stops.get(link.from_stop)
                to_stop = self.stops.get(link.to_stop)

                if type(from_stop) is Stop and type(to_stop) is Stop:
                    track = [
                        Point([coord.latitude, coord.longitude]) for coord in link.track
                    ]

                    links_to_add.append(
                        {
                            "from_stop_id": from_stop.atco_code,
                            "to_stop_id": to_stop.atco_code,
                            "geometry": from_shape(LineString(track), srid=27700),
                            "distance": link.distance,
                            "timetable_id": timetable_id,
                        }
                    )

            bulk_upsert(
                self.db,
                RouteLink,
                links_to_add,
                ["from_stop_id", "to_stop_id", "timetable_id"],
                ["geometry", "distance"],
            )

    def update_geometry(self, line_id):
        log.debug(f"Updating route overview geometry for line {line_id}")

        # Query to get the ordered stops for the line
        ordered_stops_query = (
            select(Stop.point)
            .join(LineStopUsage, LineStopUsage.stop_id == Stop.atco_code)
            .where(LineStopUsage.line_id == line_id)
            .order_by(LineStopUsage.stop_id)
        ).subquery()

        # Create a LINESTRING from the ordered stops
        geom_subquery = select(
            func.ST_MakeLine(ordered_stops_query.c.point)
        ).scalar_subquery()

        # Convert geometry from EPSG:27700 to EPSG:4326 (WGS84)
        geom_subquery = func.ST_Transform(geom_subquery, 4326)

        # Build and execute the update statement
        stmt = update(Line).where(Line.id == line_id).values(geometry=geom_subquery)

        result = self.db.execute(stmt)
        self.db.commit()

        if result.rowcount == 0:
            log.debug(f"No line with id {line_id} found or no geometry to update.")
        else:
            log.debug(f"Geometry updated for line {line_id}")

    def merge_line_routes(
        self, line_id: str, simplify_tolerance=0.0001, snap_tolerance=0.0001
    ):
        """
        Given a line_id, merge the geometries of all its related routes into one LineString overview,
        snapping close points to reduce redundant vertices and create smoother merged lines.

        Args:
            line_id: ID of the Line to fetch routes for
            simplify_tolerance: tolerance for ST_Simplify (optional)
            snap_tolerance: tolerance distance for snapping points together (in degrees for SRID 4326)

        Returns:
            Merged Shapely LineString or MultiLineString of all route sections, or None if no geometry found.
        """

        # Subquery to get all route_section geometries for routes linked to this line
        route_sections_subq = (
            select(RouteSection.geometry)
            .join(Timetable, Timetable.route_section_id == RouteSection.id)
            .join(LineToRoute, LineToRoute.route_id == Timetable.id)
            .where(LineToRoute.line_id == line_id)
        ).subquery()

        # 1. Aggregate with ST_Union to merge all geometries
        # 2. Snap vertices to a grid to merge very close points
        # 3. Simplify geometry to reduce vertex count further
        # 4. Merge connected line segments into single lines

        merged_geom_sql = func.ST_LineMerge(
            func.ST_Simplify(
                func.ST_SnapToGrid(
                    func.ST_Union(route_sections_subq.c.geometry), snap_tolerance
                ),
                simplify_tolerance,
            )
        )

        # Execute query and get merged geometry as WKB
        merged_geom_wkb = self.db.execute(select(merged_geom_sql)).scalar()

        if merged_geom_wkb is None:
            return None

        merged_geom = to_shape(merged_geom_wkb)

        # Update the Line.geometry column in DB if we got a geometry
        if isinstance(merged_geom, (MultiLineString, LineString)):
            stmt = (
                update(Line)
                .where(Line.id == line_id)
                .values(geometry=from_shape(merged_geom, srid=4326))
            )
            self.db.execute(stmt)
            self.db.commit()
            return merged_geom
        else:
            log.debug(
                f"Merged geometry for line {line_id} is not a LineString or MultiLineString."
            )
            return None

    async def import_from_map(self):
        for service_id in self.map.keys():
            self.clear_old_routes(service_id)

            for revision in self.map[service_id]:
                for file in self.map[service_id][revision]:
                    await self.handle_txc_file(Path(file))

    def get_stops(self, txc_stops: dict):
        stops = list(txc_stops.keys())

        stops = (
            self.db.query(Stop)
            .filter(func.upper(Stop.atco_code).in_([s.upper() for s in stops]))
            .with_entities(Stop.atco_code, Stop.latlong)
            .all()
        )

        # TODO: Handle missing stops

        self.stops = {stop.atco_code: stop for stop in stops}

    async def handle_txc_file(self, file: Path):
        if not self.txc_data:
            log.warning("No TXC data loaded.")
            return
        start = time.time()
        try:
            self.txc_data = txc.TransXChange(file)
            self.filename = self.txc_data.attributes.get("FileName", None)
            self.file_size_bytes = file.stat().st_size

            if not self.filename:
                log.warning(
                    "No FileName attribute found in TXC data. using actual file name"
                )
                self.filename = file.name

            with open(file, "rb") as f:
                self.file_hash = hashlib.file_digest(f, "sha256").hexdigest()

            for op in self.txc_data.operators:
                txc_operator = TXCOperator(op)
                noc = txc_operator.noc or txc_operator.operator_code
                db_operator = self.db.query(Operator).filter_by(noc=noc).first()
                if not db_operator:
                    operator = Operator(
                        noc=noc, ref=txc_operator.id, name=txc_operator.name
                    )
                    log.debug(f"Adding operator {txc_operator.name}")
                    self.db.add(operator)
            self.db.commit()

            self.get_stops(self.txc_data.stops)

            for txc_service in self.txc_data.services:
                self.handle_service(txc_service)
            bulk_upsert(
                session=self.db,
                model=Journey,
                rows=self.journeys_to_add,
                conflict_cols=["id"],
                update_cols=[
                    "service_code",
                    "ticket_machine_code",
                    "line_id",
                    "block_id",
                    "direction",
                    "start_time",
                    "end_time",
                    "calendar_id",
                ],
            )
            log.debug(f"Added {len(self.journeys_to_add)} journeys")
            self.journeys_to_add.clear()
            self.db.flush()

            bulk_upsert(
                session=self.db,
                model=StopTime,
                rows=self.stop_times_to_add,
                conflict_cols=["journey_id", "stop_sequence"],
                update_cols=[
                    "pick_up",
                    "drop_off",
                    "departure_time",
                    "arrival_time",
                    "stop_sequence",
                    "distance_traveled",
                    "timing_status",
                    "wait_time",
                ],
            )
            log.debug(f"Added {len(self.stop_times_to_add)} stop times")
            self.stop_times_to_add.clear()
            self.db.flush()

            for txc_route in self.txc_data.routes:
                route_id = self.get_id(txc_route.route_id)
                db_route = self.db.query(Timetable).filter_by(id=route_id).first()
                route_section_ref = txc_route.route_section_ref

                if route_section_ref:
                    route_section = self.txc_data.route_sections.get(route_section_ref)
                    if route_section:
                        self.handle_route_section(route_section)

                route = Timetable(
                    id=route_id,
                    private_code=txc_route.private_code,
                    description=txc_route.description,
                    route_section_id=self.get_id(route_section_ref),
                )
                if not db_route:
                    log.debug(f"Adding route {route_id}")
                    self.db.add(route)
                else:
                    log.debug(f"Updating route {route_id}")
                    self.db.merge(route)
            self.db.commit()

            # Batch fetch all existing usages for relevant line_ids and stop_codes
            all_line_ids = list(self.line_to_stops.keys())
            all_stop_codes = set()
            for stop_codes in self.line_to_stops.values():
                all_stop_codes.update(stop_codes)
            existing_usages = set(
                (r.line_id, r.stop_id)
                for r in self.db.query(LineStopUsage.line_id, LineStopUsage.stop_id)
                .filter(LineStopUsage.line_id.in_(all_line_ids))
                .filter(LineStopUsage.stop_id.in_(all_stop_codes))
                .all()
            )
            to_insert = []
            for line_id, stop_codes in self.line_to_stops.items():
                for stop_code in stop_codes:
                    if (line_id, stop_code) not in existing_usages:
                        to_insert.append({"line_id": line_id, "stop_id": stop_code})
            if to_insert:
                objects = [LineStopUsage(**data) for data in to_insert]
                self.db.bulk_save_objects(objects)
            self.db.flush()

            for line_id, route_ids in self.service_to_routes.items():
                for route_id in route_ids:
                    db_ltr = (
                        self.db.query(LineToRoute)
                        .filter_by(line_id=line_id, route_id=route_id)
                        .first()
                    )
                    if not db_ltr:
                        ltr = LineToRoute(
                            line_id=line_id,
                            route_id=route_id,
                        )
                        self.db.add(ltr)
                self.merge_line_routes(line_id)
                self.db.flush()

            self.db.commit()
            # await update_dashboard()
        except Exception as e:
            log.debug("An error occurred during txc import:")
            error_str = e.__str__()
            log.debug(error_str[:1000])
            # log.debug(error_str)
            self.db.rollback()
        finally:
            self.db.close()
            end = time.time()
            log.debug(f"TXC Import completed in {end - start:.2f} seconds")


# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         log.debug("Usage: python import_txc_new.py <path_to_zip_or_xml>")
#         exit(1)
#     input_path = sys.argv[1]
#     if input_path.lower().endswith(".zip"):
#         asyncio.run(import_txc_zip(input_path))
#     elif input_path.lower().endswith(".xml"):
#         with open(input_path, "rb") as xml_file:
#             txc_importer = TXCImporter(xml_file)
#             asyncio.run(txc_importer.handle_txc_file())
#     else:
#         log.debug("Error: Input must be a .zip or .xml file")
#         exit(1)

if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) != 2:
        log.debug("Usage: python import_txc_new.py <path_to_zip_or_xml>")
        exit(1)
    input_path = sys.argv[1]
    path = STATIC_DATA_DIR / input_path
    with time_taken("Generating TXC map"):
        map = generate_txc_map(Path(path))
    with open("txc_map.json", "w") as f:
        json.dump(map, f, indent=4)
