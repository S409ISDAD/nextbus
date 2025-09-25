import asyncio
import gc
from hashlib import sha256
import hashlib
import json
import re
import sys
import time
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

from geoalchemy2.shape import from_shape, to_shape
from shapely import MultiLineString, Point
from shapely.geometry import LineString
from sqlalchemy import and_, func, select, update
from sqlalchemy_searchable import sync_trigger

from titlecase import titlecase

from backend.config import get_logger, setup_logging
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

from backend.utils.time import to_datetime
from backend.utils.time_taken import time_taken

log = get_logger()

BAD_ORIGIN_DEST = {"Origin", "Destination", "Unknown"}


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
    zip_path = Path(zip_path).resolve()
    extract_dir = zip_path.parent / f"txc_extract_{ds_id or 'zip'}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            xml_files = [f for f in zf.namelist() if f.endswith(".xml")]

            for filename in xml_files:
                extracted_path = extract_dir / Path(filename).name
                with zf.open(filename) as xml_file, open(extracted_path, "wb") as f_out:
                    f_out.write(xml_file.read())

            log.debug(f"Extracted {len(xml_files)} XML files to {extract_dir}")
            txc_importer = TXCImporter(extract_dir, ds_id=ds_id)
            await txc_importer.import_folder()
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
        if extract_dir.exists():
            try:
                for file in extract_dir.iterdir():
                    file.unlink()
                extract_dir.rmdir()
            except Exception as e:
                log.debug(f"Error removing directory {extract_dir}: {e}")
        if ds_id:
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
                    "line_name",
                    "line_brand",
                    "description",
                ],
            )
            sync_trigger(
                conn,
                "operator",
                "search_vector",
                ["name", "noc"],
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
        self.name_on_licence = element.findtext("OperatorNameOnLicence")
        self.licence_number = element.findtext("LicenceNumber")
        self.element = element

    @property
    def name(self):
        return self.trading_name or self.name_on_licence or self.operator_short_name

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

    revision_num = txc_data.attributes.get("RevisionNumber")

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
        self.folder = folder
        self.filename = None
        self.file_hash = None
        self.file_size_bytes = None
        self.db = SessionLocal()
        self.today = datetime.now(tz=LONDON)
        self.operators: dict[int, Operator] = {}
        self.calendar_cache = {}
        self.ds_id = ds_id
        self.tds_id = None
        self.map = {}
        self.stops: dict[str, Stop] = {}
        self.file_count = 0

    async def import_folder(self):
        with time_taken("Generating TXC map"):
            self.generate_txc_map()
        await self.import_from_map()

    def generate_txc_map(self):
        txc_map = {}

        files = self.folder.glob("*.xml")
        self.file_count = len(list(files))
        for file in self.folder.glob("*.xml"):
            log.debug(file)

            services = get_service_data(file)
            for service in services:
                operator, service_id, revision_num = service

                if service_id in txc_map:
                    if revision_num in txc_map[service_id]:
                        txc_map[service_id][revision_num].append(file.as_posix())
                    else:
                        txc_map[service_id][revision_num] = [file.as_posix()]
                else:
                    txc_map[service_id] = {revision_num: [file.as_posix()]}
        self.map = txc_map

    async def import_from_map(self):
        idx = 0
        for service_id in self.map.keys():
            self.clear_old_data(service_id)

            for revision in self.map[service_id]:
                for file in self.map[service_id][revision]:
                    log.debug(
                        f"Importing {file} ({idx + 1}/{self.file_count}, {round(((idx + 1) / self.file_count) * 100, 2)}%)"
                    )
                    await self.handle_txc_file(Path(file))
                    idx += 1

    def clear_old_data(self, service_code):
        routes_to_go = (
            self.db.query(Timetable)
            .filter(
                Timetable.service_code == service_code,
                Timetable.data_source_id == self.ds_id,
                Timetable.end_date is not None,
                Timetable.end_date
                < self.today.date(),  # route is inactive if end_date is in the past (inclusive)
            )
            .all()
        )
        if routes_to_go:
            log.info(f"Deleting {len(routes_to_go)} stale routes...")
            for route in routes_to_go:
                self.db.delete(route)
            self.db.commit()
        else:
            log.debug("No old timetables to clear.")

        # flag services that have no timetables
        services_to_go = (
            self.db.query(Service)
            .filter_by(service_code=service_code, data_source_id=self.ds_id)
            .filter(
                ~self.db.query(Timetable)  # ~ = not
                .filter(
                    Timetable.service_id == Service.id,
                )
                .exists()
            )
        )
        if services_to_go.count() > 0:
            log.info(f"deactivating {services_to_go.count()} services...")
            for service in services_to_go:
                service.current = False
                self.db.add(service)
            self.db.commit()
        else:
            log.debug("No old services to clear.")

        timetable_ds_to_go = (
            self.db.query(TimetableDataSource)
            .filter_by(data_source_id=self.ds_id)
            .filter(
                ~self.db.query(Timetable)  # ~ = not
                .filter(
                    Timetable.timetable_data_source_id == TimetableDataSource.id,
                )
                .exists()
            )
        )
        if timetable_ds_to_go.count() > 0:
            log.info(f"deleting {timetable_ds_to_go.count()} tds...")
            for tds in timetable_ds_to_go:
                self.db.delete(tds)
            self.db.commit()
        else:
            log.debug("No old timetable data sources to clear.")

    def get_calendar(
        self, operating_profile: txc.OperatingProfile, operating_period: txc.DateRange
    ):
        calendar_hash = f"{operating_profile.hash}{operating_period}"

        if calendar_hash in self.calendar_cache:
            return self.calendar_cache[calendar_hash]

        regular_days = operating_profile.regular_days

        calendar = Calendar(
            start_date=operating_period.start,
            end_date=operating_period.end or None,
            monday=0 in regular_days,
            tuesday=1 in regular_days,
            wednesday=2 in regular_days,
            thursday=3 in regular_days,
            friday=4 in regular_days,
            saturday=5 in regular_days,
            sunday=6 in regular_days,
        )
        self.db.add(calendar)
        self.db.flush()

        calendar_exceptions = [
            self.get_calendar_exception(date_range=date_range, operation=False)
            for date_range in operating_profile.nonoperation_days
        ]

        calendar_exceptions += [
            self.get_calendar_exception(date_range=date_range, operation=True)
            for date_range in operating_profile.operation_days
        ]

        bank_holidays_to_add = {}

        bank_holidays_operation = operating_profile.operation_bank_holidays
        bank_holidays_non_operation = operating_profile.nonoperation_bank_holidays

        for bank_holidays, operating in [
            (bank_holidays_operation, True),
            (bank_holidays_non_operation, False),
        ]:
            if bank_holidays is None:
                continue
            for bank_holiday in bank_holidays:
                name = bank_holiday.tag

                if name == "OtherPublicHoliday":
                    date = bank_holiday.findtext("Date")
                    calendar_exceptions.append(
                        self.get_calendar_exception(
                            date=to_datetime(date),
                            operation=operating,
                            description=bank_holiday.findtext("Description") or "",
                        )
                    )
                else:
                    if name == "HolidaysOnly":
                        name = "AllBankHolidays"

                    bh = self.db.query(BankHoliday).filter_by(name=name).first()
                    if not bh:
                        bh = BankHoliday(name=name)
                        self.db.add(bh)
                        self.db.flush()
                    bank_holidays_to_add[name] = CalendarToBankHoliday(
                        operating=operating,
                        calendar_id=calendar.id,
                        bank_holiday=name,
                    )

        for serviced_org in operating_profile.serviced_organisations:
            working = serviced_org.working
            operation = serviced_org.operation

            working_days = serviced_org.serviced_organisation.working_days
            holidays = serviced_org.serviced_organisation.holidays

            if working:
                if working_days:
                    dates = working_days
                else:
                    operation = not operation
                    dates = holidays
            else:
                if holidays:
                    dates = holidays
                else:
                    operation = not operation
                    dates = working_days

            calendar_exceptions += [
                self.get_calendar_exception(date_range=date_range, operation=operation)
                for date_range in dates
            ]

        seen = set()
        deduped_exceptions = []
        for ce in calendar_exceptions:
            key = (ce.calendar_id, ce.start_date, ce.end_date, ce.operating)
            if key not in seen:
                seen.add(key)
                deduped_exceptions.append(ce)

        calendar_exceptions = deduped_exceptions

        for ce in calendar_exceptions:
            ce.calendar_id = calendar.id

        calendar_exceptions = [ce.__dict__ for ce in calendar_exceptions]

        bulk_upsert(
            self.db,
            CalendarException,
            calendar_exceptions,
            ["calendar_id", "start_date", "end_date", "operating"],
            ["description"],
        )

        for bh in bank_holidays_to_add.values():
            bh.calendar_id = calendar.id

        bank_holidays_to_add = [bh.__dict__ for bh in bank_holidays_to_add.values()]

        bulk_upsert(
            self.db,
            CalendarToBankHoliday,
            bank_holidays_to_add,
            ["calendar_id", "bank_holiday"],
            ["operating"],
        )

        self.calendar_cache[calendar_hash] = calendar

        return calendar

    def get_calendar_exception(
        self,
        date_range: txc.DateRange | None = None,
        date=None,
        operation=True,
        description="",
    ):
        """

        Create a CalendarException from a TransXChange DateRange or single date.

        From bustimes.org's import_transxchange.py
        modified to use our CalendarException model

        """
        if date_range:
            start_date = date_range.start
            end_date = date_range.end
            description = date_range.note or date_range.description
        else:
            start_date = date
            end_date = date

        return CalendarException(
            start_date=start_date,
            end_date=end_date,
            description=description,
            operating=operation,
        )

    def get_stop_time(self, journey: Journey, cell: txc.Cell):
        """
        Generates a stop time object from a txc.Cell
        from bustimes.org's import_transxchange.py
        modified to use our StopTime model
        """

        timing_status = cell.stopusage.timing_status or ""
        if len(timing_status) > 3:
            match timing_status:
                case "otherPoint":
                    timing_status = "OTH"
                case "timeInfoPoint":
                    timing_status = "TIP"
                case "principleTimingPoint" | "principalTimingPoint":
                    timing_status = "PTP"
                case _:
                    log.warning(f"Unknown timing status: {timing_status}")

        stop_time = StopTime(
            journey_id=journey.id,
            stop_sequence=cell.stopusage.sequence_number,
            dest_display=cell.stopusage.dynamic_destination_display,
            drop_off=True,
            pick_up=True,
        )

        match cell.activity:
            case "pickUp":
                stop_time.drop_off = False
            case "setDown":
                stop_time.pick_up = False
            case "pass":
                stop_time.pick_up = False
                stop_time.drop_off = False

        stop_time.departure_time = cell.departure_time
        if cell.arrival_time != cell.departure_time:
            stop_time.arrival_time = cell.arrival_time

        atco_code = cell.stopusage.stop.atco_code.upper()

        if journey.start_time is None:
            journey.start_time = stop_time.departure_time or stop_time.arrival_time
            if atco_code in self.stops:
                journey.origin_stop_id = atco_code
            else:
                log.warning(f"Stop with ATCO code {atco_code} not found in database")

        if journey.headsign is None:
            journey.headsign = cell.stopusage.dynamic_destination_display

        if atco_code in self.stops:
            stop_time.stop_id = atco_code
            journey.destination_stop_id = atco_code
        else:
            log.warning(f"Stop with ATCO code {atco_code} not found in database")

        return stop_time

    def handle_journeys(
        self,
        journeys: list[txc.VehicleJourney],
        txc_service: txc.Service,
        service: Service,
        timetable: Timetable,
    ):
        default_calendar = None  # in case calendars are not defined anywhere

        stop_times_to_add = []
        journeys_to_add = []

        log.debug("Clearing existing journeys...")

        delete_stmt = Journey.__table__.delete().where(
            Journey.timetable_id == timetable.id,
        )
        self.db.execute(delete_stmt)

        subq = select(Journey.calendar_id).distinct()

        delete_stmt = Calendar.__table__.delete().where(~Calendar.id.in_(subq))
        self.db.execute(delete_stmt)
        self.db.flush()

        for i, txc_journey in enumerate(journeys):
            if txc_journey.operating_profile:
                calendar = self.get_calendar(
                    txc_journey.operating_profile, txc_service.operating_period
                )

            elif txc_journey.journey_pattern.operating_profile:
                calendar = self.get_calendar(
                    txc_journey.journey_pattern.operating_profile, operating_period
                )
            elif txc_service.operating_profile:
                if not default_calendar:
                    default_calendar = self.get_calendar(
                        txc_service.operating_profile, txc_service.operating_period
                    )
                calendar = default_calendar  # use the service's calendar as a fallback
            else:
                calendar = None
                log.warning("could not get any calendar")

            journey = Journey(
                service_id=service.id,
                timetable_id=timetable.id,
                calendar_id=calendar.id if calendar else None,
                vehicle_journey_code=txc_journey.code or "",
                ticket_machine_code=txc_journey.ticket_machine_journey_code or "",
                sequence=txc_journey.sequencenumber,
                inbound=txc_journey.journey_pattern.direction == "inbound",
            )
            self.db.add(journey)
            self.db.flush()

            if txc_journey.block and txc_journey.block.code:
                journey.block_id = txc_journey.block.code

            for cell in txc_journey.get_times():
                stop_time = self.get_stop_time(journey, cell)
                stop_times_to_add.append(stop_time)

            # last stop cant have a departure time
            if not stop_time.arrival_time:
                stop_time.arrival_time = stop_time.departure_time
                stop_time.departure_time = None

            journey.end_time = stop_time.arrival_time

            journeys_to_add.append(journey)

        if journeys_to_add:
            self.db.bulk_save_objects(journeys_to_add)

            # journeys_to_add = [
            #     {c.name: getattr(j, c.name) for c in Journey.__table__.columns}
            #     for j in journeys_to_add
            # ]

            # bulk_upsert(
            #     session=self.db,
            #     model=Journey,
            #     rows=journeys_to_add,
            #     conflict_cols=[
            #         "id",
            #     ],
            #     update_cols=[
            #         "vehicle_journey_code",
            #         "ticket_machine_code",
            #         "sequence",
            #         "block_id",
            #         "inbound",
            #         "headsign",
            #         "start_time",
            #         "end_time",
            #         "origin_stop_id",
            #         "destination_stop_id",
            #         "calendar_id",
            #     ],
            # )
            log.debug(f"Added {len(journeys_to_add)} journeys")
            journeys_to_add.clear()
            self.db.flush()

        if stop_times_to_add:
            # stop_times_to_add = [
            #     {
            #         c.name: getattr(s, c.name)
            #         for c in StopTime.__table__.columns
            #         if c.name != "id"
            #     }
            #     for s in stop_times_to_add
            # ]

            self.db.bulk_save_objects(stop_times_to_add)
            # bulk_upsert(
            #     session=self.db,
            #     model=StopTime,
            #     rows=stop_times_to_add,
            #     conflict_cols=["journey_id", "stop_sequence"],
            #     update_cols=[
            #         "stop_sequence",
            #         "arrival_time",
            #         "departure_time",
            #         "dest_display",
            #         "timing_status",
            #         "pick_up",
            #         "drop_off",
            #     ],
            # )
            log.debug(f"Added {len(stop_times_to_add)} stop times")
            stop_times_to_add.clear()
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
        log.debug(f"{txc_service.lines[0].line_name} | {description}")

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

        operator = self.operators.get(txc_service.operator)

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
                processed_at=datetime.now(tz=LONDON),
            )
            self.db.add(timetable_datasource)
            self.db.flush()
        else:
            log.info(f"No changes to timetable data source {self.filename}, skipping")
            return

        routes = set()

        for txc_line in txc_service.lines:
            if (
                txc_service.operating_period.end
                and txc_service.operating_period.end < self.today.date()
            ):
                log.debug(
                    f"Skipping line {txc_line.line_name} for service {txc_service.service_code} as it ended on {txc_service.operating_period.end}"
                )
                continue

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

            service.description = description

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

            service.operator_id = operator.id if operator else None

            # from bustimes.org's import_transxchange.py (modified)
            if (
                txc_line.outbound_description != txc_line.inbound_description
                or txc_service.origin in BAD_ORIGIN_DEST
            ):
                out_desc = txc_line.outbound_description
                in_desc = txc_line.inbound_description

                if out_desc and in_desc and out_desc.isupper() and in_desc.isupper():
                    out_desc = titlecase(out_desc, callback=initialisms)
                    in_desc = titlecase(in_desc, callback=initialisms)

                if out_desc:
                    if not service.description or len(txc_service.lines) > 1:
                        service.description = out_desc
                if in_desc:
                    if not service.description:
                        service.description = in_desc

            # end from

            self.db.add(service)
            self.db.flush()

            existing_timetable = (
                self.db.query(Timetable)
                .filter(
                    Timetable.service_id == service.id,
                    Timetable.data_source_id == self.ds_id,
                    Timetable.line_name == txc_line.line_name,
                )
                .first()
            )

            if existing_timetable:
                log.debug(f"Existing timetable: {existing_timetable.revision_number}")
                log.debug(
                    f"New timetable: {self.txc_data.attributes['RevisionNumber']}"
                )
                if existing_timetable.revision_number == int(
                    self.txc_data.attributes["RevisionNumber"]
                ):
                    log.info(
                        f"No changes to timetable for service {service.service_code} on line {txc_line.line_name}, skipping"
                    )
                    continue

            timetable = Timetable(
                service_id=service.id,
                line_id=txc_line.id,
                operator_id=operator.id if operator else None,
                data_source_id=self.ds_id,
                timetable_data_source_id=timetable_datasource.id,
                line_name=txc_line.line_name,
                line_brand=line_brand,
                outbound_description=txc_line.outbound_description or "",
                inbound_description=txc_line.inbound_description or "",
                start_date=txc_service.operating_period.start,
                end_date=txc_service.operating_period.end or date(9999, 12, 31),
                revision_number=self.txc_data.attributes["RevisionNumber"],
                created_at=to_datetime(self.txc_data.attributes["CreationDateTime"]),
                modified_at=to_datetime(
                    self.txc_data.attributes["ModificationDateTime"]
                ),
                public_use=service.public_use,
                service_code=txc_service.service_code,
            )

            for desc in (timetable.outbound_description, timetable.inbound_description):
                if len(desc) > 255:
                    log.warning(
                        f"{desc} is too long ({len(desc)} characters) in {self.filename}"
                    )
                    desc = desc[:255]

            # from bustimes.org's import_transxchange.py (modified)
            if txc_service.origin and txc_service.origin not in BAD_ORIGIN_DEST:
                timetable.origin = txc_service.origin
            else:
                timetable.origin = ""

            if (
                txc_service.destination
                and txc_service.destination not in BAD_ORIGIN_DEST
            ):
                if " via " in txc_service.destination:
                    (
                        timetable.destination,
                        timetable.vias,
                    ) = txc_service.destination.split(" via ", 1)
                else:
                    timetable.destination = txc_service.destination
            else:
                timetable.destination = ""

            # end from

            if description:
                timetable.description = description

            if txc_service.vias:
                timetable.vias = ", ".join(txc_service.vias)

            if existing_timetable:
                timetable.id = existing_timetable.id
                for attr in [
                    "end_date",
                    "description",
                    "origin",
                    "destination",
                    "vias",
                    "line_brand",
                    "outbound_description",
                    "inbound_description",
                    "public_use",
                    "revision_number",
                    "created_at",
                    "modified_at",
                    "timetable_data_source_id",
                    "operator_id",
                    "service_code",
                ]:
                    setattr(existing_timetable, attr, getattr(timetable, attr))
                timetable = existing_timetable
            else:
                self.db.add(timetable)

            # bulk_upsert(
            #     self.db,
            #     Timetable,
            #     [
            #         {
            #             c.name: getattr(timetable, c.name)
            #             for c in Timetable.__table__.columns
            #             if c.name != "id"
            #         }
            #     ],
            #     [
            #         "service_id",
            #         "revision_number",
            #         "start_date",
            #         "end_date",
            #         "data_source_id",
            #     ],
            #     [
            #         "end_date",
            #         "description",
            #         "origin",
            #         "destination",
            #         "vias",
            #         "line_brand",
            #         "outbound_description",
            #         "inbound_description",
            #         "public_use",
            #         "revision_number",
            #         "created_at",
            #         "modified_at",
            #         "timetable_data_source_id",
            #         "operator_id",
            #         "service_code",
            #     ],
            # )

            self.db.flush()

            log.debug(f"Timetable ID: {timetable.id}")

            if self.txc_data.route_sections:
                self.handle_route_links(journeys, timetable.id)

            if not skip_journeys:
                log.debug(
                    f"Handling {len(journeys)} journeys for service {txc_service.service_code} on line {txc_line.id}"
                )

                self.handle_journeys(journeys, txc_service, service, timetable)

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
            links_to_add = {}

            for link in route_links:
                from_stop = self.stops.get(link.from_stop)
                to_stop = self.stops.get(link.to_stop)

                if type(from_stop) is Stop and type(to_stop) is Stop:
                    track = [
                        Point([coord.longitude, coord.latitude]) for coord in link.track
                    ]

                    srid = (
                        link.track[0].srid
                        if link.track and link.track[0].srid
                        else 4326
                    )
                    key = (from_stop.atco_code, to_stop.atco_code)

                    links_to_add[key] = {
                        "from_stop": from_stop.atco_code,
                        "to_stop": to_stop.atco_code,
                        "geometry": from_shape(LineString(track), srid=srid),
                        "distance": link.distance,
                        "timetable_id": timetable_id,
                    }

                else:
                    log.warning(
                        f"stop from {link.from_stop} or to {link.to_stop} is {type(from_stop)} / {type(to_stop)}"
                    )
            log.debug(f"Adding {len(links_to_add)} route links")

            bulk_upsert(
                self.db,
                RouteLink,
                list(links_to_add.values()),
                ["from_stop", "to_stop", "timetable_id"],
                ["geometry", "distance"],
            )

    def get_stops(self, txc_stops: dict):
        stops = (
            self.db.query(Stop)
            .filter(
                func.upper(Stop.atco_code).in_([s.upper() for s in txc_stops.keys()])
            )
            .all()
        )

        # TODO: Handle missing stops

        self.stops = {stop.atco_code: stop for stop in stops}

    async def handle_txc_file(self, file: Path):
        start = time.time()
        try:
            self.txc_data = txc.TransXChange(file)
            if not self.txc_data:
                log.warning("No TXC data loaded.")
                return
            self.filename = self.txc_data.attributes.get("FileName", None)
            self.file_size_bytes = file.stat().st_size

            self.calendar_cache = {}

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
                    operator = Operator(noc=noc, name=txc_operator.name)
                    log.debug(f"Adding operator {txc_operator.name}")
                    db_operator = operator

                    self.db.add(operator)

                self.operators[txc_operator.id] = db_operator

            self.db.commit()

            self.get_stops(self.txc_data.stops)

            for service_code, txc_service in self.txc_data.services.items():
                self.clear_old_data(service_code)
                self.handle_service(txc_service)

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


if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) != 2:
        log.debug("Usage: python import_txc_new.py <path_to_zip_or_xml>")
        exit(1)
    input_path = sys.argv[1]
    if input_path.lower().endswith(".zip"):
        asyncio.run(import_txc_zip(input_path))
    elif input_path.lower().endswith(".xml"):
        txc_importer = TXCImporter(Path(input_path), ds_id=1)
        asyncio.run(txc_importer.handle_txc_file(Path(input_path)))
    else:
        log.debug("Error: Input must be a .zip or .xml file")
        exit(1)

# if __name__ == "__main__":
#     setup_logging()
#     if len(sys.argv) != 2:
#         log.debug("Usage: python import_txc_new.py <path_to_zip_or_xml>")
#         exit(1)
#     input_path = sys.argv[1]
#     path = STATIC_DATA_DIR / input_path
#     txc_importer = TXCImporter(path, ds_id=1)
#     txc_importer.import_folder()
