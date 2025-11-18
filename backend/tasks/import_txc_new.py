import argparse
import asyncio
import gc
import hashlib
import re
import time
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

from geoalchemy2.shape import from_shape
from shapely import Point
from shapely.geometry import LineString
from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy_searchable import sync_trigger

from titlecase import titlecase

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal, engine
from backend.deps import LONDON
from backend.models import (
    BankHoliday,
    Calendar,
    CalendarException,
    CalendarToBankHoliday,
    DataSourceVersion,
    Journey,
    Service,
    Operator,
    Timetable,
    Stop,
    StopTime,
    RouteLink,
    FileImport,
    ServiceStopUsage,
    service_operator_table,
)
from backend.tasks.import_naptan import get_stop
from backend.transxchange import txc
from backend.utils.bulk_upsert import bulk_upsert

from backend.utils.time import to_datetime
from backend.utils.time_taken import time_taken

log = get_logger(__name__)

BAD_ORIGIN_DEST = {"Origin", "Destination", "Unknown"}


def import_txc_zip(zip_path, ds_id=None, dsv_id=None, skip_checks=False):
    start = time.time()
    zip_path = Path(zip_path).resolve()
    extract_dir = zip_path.parent / f"txc_extract_{dsv_id or ds_id or 'zip'}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    txc_importer = None
    stats = Statistics()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            xml_files = [f for f in zf.namelist() if f.endswith(".xml")]

            for filename in xml_files:
                extracted_path = extract_dir / Path(filename).name
                with zf.open(filename) as xml_file, open(extracted_path, "wb") as f_out:
                    f_out.write(xml_file.read())

            log.debug(f"Extracted {len(xml_files)} XML files to {extract_dir}")
            txc_importer = TXCImporter(
                extract_dir, ds_id=ds_id, dsv_id=dsv_id, skip_checks=skip_checks
            )
            txc_importer.import_folder()
    except Exception as e:
        import traceback

        traceback.print_exc()
        log.error(f"Error importing TXC zip {zip_path}: {e}")
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
        if txc_importer:
            stats = txc_importer.stats
            del txc_importer
            gc.collect()

            for item in stats.output():
                log.debug(item)

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
                    "vias",
                ],
            )
            sync_trigger(
                conn,
                "operator",
                "search_vector",
                ["name", "noc"],
            )
        return duration, stats


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
        return self.trading_name or self.operator_short_name or self.name_on_licence

    def get_noc(self):
        """
        override certain nocs to match the ones on bustimes.org, as some are incorrect
        """
        match self.noc or self.operator_code:
            case "BH":
                return "BHBC"
            case "MB":
                return "METR"
            case _:
                return self.noc or self.operator_code

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
    modified the via logic to improve descriptions
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

        if not description or len(description.split("-")) > 4:
            description = f"{origin} - {destination}"
            vias = txc_service.vias
            vias_list = []
            if vias:
                if all(via.isupper() for via in vias):
                    vias = [titlecase(via, callback=initialisms) for via in vias]
                if len(vias) == 1:
                    via = vias[0]
                    if "via " in via:
                        via = via.replace("via ", "").strip()
                    parts = re.split(r",| and |&", via)
                    vias_list.extend([part.strip() for part in parts])

                if len(vias_list) <= 2:
                    description = " - ".join([origin] + vias_list + [destination])

    return description


def get_service_data(path):
    txc_data = txc.TransXChange(path)
    operators = getOperators(txc_data.operators)

    revision_num = txc_data.attributes.get("RevisionNumber")

    services = []

    for service in txc_data.services.values():
        service_id = service.service_code
        operator = operators[service.operator].noc
        operating_period = service.operating_period

        for line in service.lines:
            line_name = line.line_name or "Unknown"
            services.append(
                [operator, service_id, line_name, revision_num, operating_period]
            )

    return txc_data, services


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


class Statistics:
    def __init__(self):
        self.services_created = 0
        self.services_updated: set[int] = set()
        self.services_deactivated = 0
        self.services_skipped = 0
        self.timetables_created = 0
        self.timetables_updated: set[int] = set()
        self.timetables_skipped: set[int] = set()
        self.timetables_deleted = 0
        self.journeys_created = 0
        self.stop_times_created = 0
        self.stops_created = 0
        self.stops_updated = 0

    def __add__(self, other):
        if not isinstance(other, Statistics):
            return NotImplemented
        result = Statistics()
        for attr in self.__dict__.keys():
            if type(getattr(self, attr)) is set:
                setattr(
                    result, attr, getattr(self, attr) | getattr(other, attr)
                )  # union of sets
            else:
                setattr(result, attr, getattr(self, attr) + getattr(other, attr))
        return result

    def output(self) -> list[str]:
        output = []
        for k, v in self.__dict__.items():
            if type(v) is set:
                output.append(f"{k}: {len(v)}")
            else:
                output.append(f"{k}: {v}")

        return output


class TXCImporter:
    def __init__(self, folder: Path, ds_id=None, dsv_id=None, skip_checks=False):
        self.txc_data = None
        self.folder = folder
        self.filename = None
        self.file_hash = None
        self.file_size_bytes = None
        self.skip_checks = skip_checks
        self.services: set[int] = set()
        self.timetables: set[int] = set()
        self.db = SessionLocal()
        self.today = datetime.now(tz=LONDON)
        self.operators: dict[int, Operator] = {}
        self.calendar_cache = {}
        self.ds_id = ds_id
        self.dsv_id = dsv_id
        self.map = {}
        self.files_in_revision = 0
        self.file_idx_in_revision = 0
        self.stops: dict[str, Stop] = {}
        self.file_count = 0
        self.operator_updated = False
        self.stats = Statistics()
        self.end_date = None
        self.processed_cache: dict[str, txc.TransXChange] = {}
        self.service_line_key: tuple[str, str] | None = None
        self.dsv = self.get_dsv()

    def get_dsv(self):
        if self.dsv_id:
            result = (
                self.db.query(DataSourceVersion)
                .filter(DataSourceVersion.id == self.dsv_id)
                .first()
            )
            return result

    @property
    def is_repeat_revision(self):
        return self.files_in_revision > 1 and self.file_idx_in_revision != 0

    def import_folder(self):
        with time_taken("Generating TXC map"):
            self.generate_txc_map()
        self.import_from_map()

    def generate_txc_map(self):
        try:
            txc_map = {}

            files = list(self.folder.glob("*.xml"))
            self.file_count = len(list(files))
            for file in files:
                log.debug(file)

                txc_data, services = get_service_data(file)
                self.processed_cache[file.as_posix()] = txc_data
                for service in services:
                    operator, service_id, line_name, revision_num, operating_period = (
                        service
                    )
                    line_key = (service_id, line_name)
                    start = operating_period.start
                    end = operating_period.end or date(9999, 12, 31)

                    entry = {"files": [file.as_posix()], "start": start, "end": end}

                    if line_key not in txc_map:
                        txc_map[line_key] = {}

                    revision_key = (revision_num, start)

                    if revision_key in txc_map[line_key]:
                        # append file(s) if multiple files exist for same service/(revision_num, start)
                        txc_map[line_key][revision_key]["files"].append(file.as_posix())
                        existing = txc_map[line_key][revision_key]
                        existing["start"] = min(existing["start"], start)
                        existing["end"] = max(existing["end"], end)
                        txc_map[line_key][revision_key]["start"] = min(
                            txc_map[line_key][revision_key]["start"], start
                        )
                    else:
                        txc_map[line_key][revision_key] = entry

            self.map = txc_map
        except Exception as e:
            import traceback

            traceback.print_exc()
            log.debug(f"Error generating TXC map: {e}")

    def import_from_map(self):
        log.debug(f"Importing {len(self.map.keys())} services...")
        idx = 0
        total_passes = sum(
            len(rev_data["files"])
            for revisions in self.map.values()
            for rev_data in revisions.values()
        )
        log.debug(f"Total file appearances to process: {total_passes}")
        for line_key in self.map.keys():
            service_id, line_name = line_key

            self.service_line_key = line_key

            sorted_revisions = sorted(
                self.map[line_key].items(),
                key=lambda x: x[0],  # sort by (revision_num, start_date)
            )

            for i, ((revision, start_date), rev_data) in enumerate(sorted_revisions):
                log.debug(
                    f"Processing service {service_id} - {line_name}, revision {revision} starting {start_date}"
                )
                # determine end date based on next revision's start date
                if i < len(sorted_revisions) - 1:
                    next_start = sorted_revisions[i + 1][1]["start"]
                    log.debug(
                        f"Revision {revision} for {line_name} ends {rev_data['end']} "
                        f"(next revision {sorted_revisions[i+1][0]} starts {next_start})"
                    )
                    if next_start > start_date:
                        rev_data["end"] = next_start - timedelta(days=1)
                    else:
                        # same start date or earlier (patch or reissue)
                        log.warning(
                            "Next revision start date is not after current revision start date"
                        )
                        rev_data["end"] = start_date

                self.files_in_revision = len(rev_data["files"])
                self.file_idx_in_revision = 0
                self.services.clear()

                for file in rev_data["files"]:
                    log.debug(
                        f"Importing {file} ({idx + 1}/{total_passes}, {round(((idx + 1) / total_passes) * 100, 2)}%)"
                    )
                    self.end_date = rev_data["end"]
                    self.timetables.clear()
                    self.handle_txc_file(Path(file))
                    self.file_idx_in_revision += 1
                    self.end_date = None  # reset just in case
                    idx += 1

                log.debug("Finalising services...")
                self.finish_services()

            self.clear_old_timetables(service_id, line_name)
            self.clear_old_services(service_id, line_name)

    def clear_old_timetables(self, service_code, line_name):
        today = self.today.date()

        T1 = Timetable
        T2 = aliased(Timetable)

        higher_revision_started = exists().where(
            and_(
                T2.service_code == T1.service_code,
                T2.line_name == T1.line_name,
                T2.data_source_id == self.ds_id,
                T2.start_date <= today,
                or_(
                    # T2 has higher revision number
                    and_(
                        T2.revision_number > T1.revision_number,
                        T2.revision_number > 0,
                    ),
                    # fallback: revision 0 case
                    and_(
                        T1.revision_number == 0,
                        T2.revision_number == 0,
                        T2.start_date > T1.start_date,
                    ),
                ),
            )
        )

        timetables_to_go = (
            self.db.query(T1)
            .filter(
                T1.service_code == service_code,
                T1.line_name == line_name,
                T1.data_source_id == self.ds_id,
                or_(
                    and_(T1.end_date is not None, T1.end_date < today),
                    T1.id.notin_(self.timetables),  # not in the current dataset
                ),
                higher_revision_started,  # only delete if a higher revision has started
            )
            .all()
        )

        if timetables_to_go:
            log.info(f"Deleting {len(timetables_to_go)} stale timetables...")
            self.stats.timetables_deleted += len(timetables_to_go)
            for timetable in timetables_to_go:
                self.db.delete(timetable)
            self.db.commit()
        else:
            log.debug("No old timetables to clear.")

    def clear_old_services(self, service_id, line_name):
        # flag services that have no timetables, after importing timetables incase they have been replaced
        services_to_go = (
            self.db.query(Service)
            .filter_by(
                service_code=service_id, data_source_id=self.ds_id, line_name=line_name
            )
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
            self.stats.services_deactivated += services_to_go.count()
            for service in services_to_go:
                service.current = False
                self.db.add(service)
            self.db.commit()
        else:
            log.debug("No old services to clear.")

    def get_calendar(
        self, operating_profile: txc.OperatingProfile, operating_period: txc.DateRange
    ):
        calendar_hash = f"{operating_profile.hash}{operating_period}"

        if calendar_hash in self.calendar_cache:
            return self.calendar_cache[calendar_hash]

        regular_days = operating_profile.regular_days

        calendar = Calendar(
            start_date=operating_period.start,
            end_date=self.end_date or operating_period.end or None,
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
            self.get_calendar_exception(
                date_range=date_range, operation=True, special=True
            )
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
        special=False,
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
            special=special,
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
            timing_status=timing_status,
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

        if not self.is_repeat_revision:
            # only clear journeys if this is the first file in a revision with multiple files OR if there's only one file
            log.debug("Clearing existing journeys...")

            delete_stmt = Journey.__table__.delete().where(
                Journey.timetable_id == timetable.id,
            )
            self.db.execute(delete_stmt)

            subq = (
                select(Journey.calendar_id)
                .join(Calendar, Calendar.id == Journey.calendar_id)
                .distinct()
            )

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
                    txc_journey.journey_pattern.operating_profile,
                    txc_service.operating_period,
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
                inbound=txc_journey.journey_pattern.is_inbound(),
            )
            self.db.add(journey)
            self.db.flush()

            if txc_journey.block and txc_journey.block.code:
                journey.block_id = txc_journey.block.code
            elif (
                txc_journey.journey_pattern
                and txc_journey.journey_pattern.block
                and txc_journey.journey_pattern.block.code
            ):
                journey.block_id = txc_journey.journey_pattern.block.code

            for seq, cell in enumerate(txc_journey.get_times()):
                stop_time = self.get_stop_time(journey, cell)
                if stop_time.stop_sequence is None:
                    stop_time.stop_sequence = seq
                stop_times_to_add.append(stop_time)

            # last stop cant have a departure time
            if not stop_time.arrival_time:
                stop_time.arrival_time = stop_time.departure_time
                stop_time.departure_time = None

            journey.end_time = stop_time.arrival_time

            journeys_to_add.append(journey)

        if journeys_to_add:
            self.stats.journeys_created += len(journeys_to_add)
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

            self.stats.stop_times_created += len(stop_times_to_add)

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

        operator = self.operators.get(txc_service.operator)

        if operator and "first" in operator.name.lower():
            # use the artificial end date for first bus
            end_date = self.end_date or txc_service.operating_period.end or None
        else:
            end_date = txc_service.operating_period.end or None

        # end_date = self.end_date or txc_service.operating_period.end or None

        if end_date and end_date < self.today.date():
            log.debug(
                f"Skipping file for {txc_service.service_code} as it ended on {end_date}"
            )
            self.stats.services_skipped += 1
            return

        description = get_description(txc_service)

        if description == "Origin - Destination":
            description = ""

        unique_service_code = False

        # from bustimes.org's import_transxchange.py
        if re.match(r"^P[BCDFGHKM]\d+:\d+.*$", txc_service.service_code) or re.match(
            r"^UZ[a-zA-Z0-9]+:.*$", txc_service.service_code
        ):
            unique_service_code = True
        # end from

        service = None

        for txc_line in txc_service.lines:
            if self.service_line_key and self.service_line_key[1] != txc_line.line_name:
                log.debug(
                    f"Skipping {txc_line.line_name} for {txc_service.service_code}, not the target line ({self.service_line_key[1]})"
                )
                continue
            if end_date and end_date < self.today.date():
                log.debug(
                    f"Skipping line {txc_line.line_name} for service {txc_service.service_code} as it ended on {end_date}"
                )
                continue

            txc_line.line_name = txc_line.line_name.replace("_", " ").strip()

            # find existing service
            # from bustimes.org's import_transxchange.py - modified
            services = (
                self.db.query(Service)
                .order_by(Service.current.desc(), Service.id.asc())
                .filter(
                    or_(
                        Service.line_name.ilike(txc_line.line_name),
                        exists().where(
                            and_(
                                Timetable.line_name.ilike(txc_line.line_name),
                                Timetable.service_id == Service.id,
                            )
                        ),
                    )
                )
            )
            existing_query = None

            if self.operators:
                op_ids = [operator.id for operator in self.operators.values()]

                matches_operator = exists().where(
                    and_(
                        service_operator_table.c.service_id == Service.id,
                        service_operator_table.c.operator_id.in_(op_ids),
                    )
                )

                # services with no operators linked yet
                no_operator_link = not_(
                    exists().where(service_operator_table.c.service_id == Service.id)
                )

                op_filter = or_(matches_operator, no_operator_link)

                if self.dsv and self.dsv.name.startswith("Stagecoach"):
                    line_name = txc_line.line_name
                    dsv_name = str(self.dsv.name)

                    if description and (
                        (line_name == "1" and "Chester" in description)
                        or (
                            line_name == "59" and dsv_name == "Stagecoach East Scotland"
                        )
                        or (line_name == "700" and "Stagecoach" in dsv_name)
                    ):
                        op_filter = and_(
                            or_(Service.data_source_id == self.ds_id, op_filter),
                            Service.description == description,
                        )

                existing_query = services.join(Service.operators).filter(op_filter)
            else:
                existing_query = services

            if len(self.txc_data.services) == 1:
                log.debug(
                    "matching by stop usage/stop times as only one service in file"
                )
                stop_ids = [s for s in self.stops.keys()]
                has_stop_time = exists().where(
                    and_(
                        StopTime.stop_id.in_(stop_ids),
                        StopTime.journey_id == Journey.id,
                        Journey.timetable_id == Timetable.id,
                        Timetable.service_id == Service.id,
                    )
                )

                has_stop_usage = exists().where(
                    and_(
                        ServiceStopUsage.stop_id.in_(stop_ids),
                        ServiceStopUsage.service_id == Service.id,
                    )
                )
                has_no_route = not_(
                    exists().where(
                        Journey.service_id == Service.id,
                    )
                )
                existing_query = existing_query.filter(
                    or_(has_stop_time, and_(has_stop_usage, has_no_route))
                )

            else:
                log.debug("matching by service code and description")
                condition = exists().where(
                    and_(
                        Timetable.service_code == txc_service.service_code,
                        Timetable.service_id == Service.id,
                    )
                )
                if description:
                    condition = or_(condition, Service.description == description)
                existing_query = existing_query.filter(condition)

            existing_service = existing_query.first()

            if unique_service_code and not existing_service:
                log.debug(f"Looking for unique service code {txc_service.service_code}")
                existing_service = services.filter(
                    Service.service_code == txc_service.service_code,
                ).first()

            # end from

            if existing_service:
                log.debug(f"Found existing service {existing_service.id}")
                service = existing_service

            else:
                log.debug("Creating new service")
                service = Service(
                    line_name=txc_line.line_name,
                    service_code=txc_service.service_code,
                    current=True,
                    data_source_id=self.ds_id,
                )
                self.stats.services_created += 1

            # from bustimes.org's import_transxchange.py

            if description and (
                not service.description
                or "Origin - " not in description
                and " - Destination" not in description
            ):
                service.description = description

            # end from

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

            log.debug(
                f"{txc_line.line_name} {f'({line_brand}) ' if line_brand else ''}| {description}"
            )

            # from bustimes.org's import_transxchange.py (modified)
            if line_brand:
                if service.description:
                    service.description = service.description.removesuffix(
                        f" [{txc_line.line_brand}]"
                    )
            # end from

            if line_brand:
                service.line_brand = line_brand

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
                    if (not service.description or len(txc_service.lines) > 1) and len(
                        out_desc.split("-")
                    ) <= 4:
                        service.description = out_desc
                if in_desc:
                    if not service.description and len(in_desc.split("-")) <= 4:
                        service.description = in_desc

            # end from

            if service.description is not None:
                # add spaces around hyphens that don't already have spaces
                service.description = re.sub(
                    r"(?<! )-(?! )", " - ", str(service.description)
                )

                # remove "via"  from description
                service.description = service.description.split("via")[0].strip()

            if txc_service.mode:
                service.mode = txc_service.mode

            self.db.add(service)
            self.db.flush()

            if operator:
                stmt = (
                    pg_insert(service_operator_table)
                    .values(
                        service_id=service.id,
                        operator_id=operator.id,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["service_id", "operator_id"]
                    )
                )
                self.db.execute(stmt)
                self.db.flush()
            else:
                log.warning(
                    f"Operator not found for service {txc_service.service_code}"
                )

            if end_date and end_date < txc_service.operating_period.start:
                log.warning(
                    f"Service {txc_service.service_code} has an end date before its start date"
                )
                end_date = None

            existing_timetable = (
                self.db.query(Timetable)
                .filter(
                    Timetable.service_id == service.id,
                    Timetable.data_source_id == self.ds_id,
                    Timetable.line_name == txc_line.line_name,
                    Timetable.start_date == txc_service.operating_period.start,
                    # make sure we dont overwrite an existing timetable if we find a new one with a different start date
                )
                .first()
            )

            if existing_timetable:
                existing_timetable.end_date = end_date or date(
                    9999, 12, 31
                )  # ensure end date is updated if changed
                self.db.add(existing_timetable)
                self.db.flush()
                self.timetables.add(existing_timetable.id)
                try:
                    new_revision = int(
                        self.txc_data.attributes.get("RevisionNumber", 0)
                    )
                except ValueError:
                    new_revision = 0
                log.debug(f"Existing timetable: {existing_timetable.revision_number}")
                log.debug(f"New timetable: {new_revision}")
                if (
                    existing_timetable.revision_number == new_revision
                    and not new_revision == 0
                    # dont skip if revision number is 0, operator might not be setting it
                    and not self.skip_checks
                    and not self.is_repeat_revision
                ):
                    log.info(
                        f"No changes to timetable for service {service.service_code} on line {txc_line.line_name}, skipping"
                    )
                    self.stats.timetables_skipped.add(int(existing_timetable.id))
                    continue
                else:
                    self.stats.timetables_updated.add(int(existing_timetable.id))
            else:
                self.stats.timetables_created += 1

            timetable = Timetable(
                service_id=service.id,
                line_id=txc_line.id,
                data_source_id=self.ds_id,
                data_source_version_id=self.dsv_id,
                line_name=txc_line.line_name,
                line_brand=line_brand,
                outbound_description=txc_line.outbound_description or "",
                inbound_description=txc_line.inbound_description or "",
                start_date=txc_service.operating_period.start,
                end_date=end_date or date(9999, 12, 31),
                revision_number=self.txc_data.attributes["RevisionNumber"],
                created_at=to_datetime(self.txc_data.attributes["CreationDateTime"]),
                modified_at=to_datetime(
                    self.txc_data.attributes["ModificationDateTime"]
                ),
                public_use=service.public_use,
                service_code=txc_service.service_code,
            )

            if existing_service:
                self.stats.services_updated.add(int(existing_service.id))

            if line_brand:
                timetable.line_brand = line_brand

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

            service.vias = timetable.vias or None

            self.db.merge(service)
            self.db.flush()

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
                    "service_code",
                ]:
                    setattr(existing_timetable, attr, getattr(timetable, attr))
                timetable = existing_timetable
            else:
                self.db.add(timetable)

            self.db.flush()

            log.debug(f"Timetable ID: {timetable.id}")

            self.timetables.add(timetable.id)

            if self.txc_data.route_sections:
                self.handle_route_links(journeys, timetable.id)

            if not skip_journeys:
                log.debug(
                    f"Handling {len(journeys)} journeys for service {txc_service.service_code} on line {txc_line.id}"
                )

                self.handle_journeys(journeys, txc_service, service, timetable)

            self.services.add(int(service.id))

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
                    start = Point([link.track[0].longitude, link.track[0].latitude])
                    end = Point([link.track[-1].longitude, link.track[-1].latitude])
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

                    null_point = from_shape(Point([0, 0]), 4326)

                    bad_points = (null_point, None)

                    from_stop_bad = bool(
                        from_stop.point in bad_points
                        or from_stop.lat == 0
                        or from_stop.lon == 0
                    )

                    to_stop_bad = bool(
                        to_stop.point in bad_points
                        or to_stop.lat == 0
                        or to_stop.lon == 0
                    )

                    if from_stop_bad or to_stop_bad:
                        self.stats.stops_updated += 1

                    if from_stop_bad:
                        from_stop.point = from_shape(start, srid=srid)
                        self.db.merge(from_stop)
                    if to_stop_bad:
                        to_stop.point = from_shape(end, srid=srid)
                        self.db.merge(to_stop)

                    self.db.flush()

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

        self.stops = {stop.atco_code: stop for stop in stops}

        stops_to_add = {}

        for atco_code, stop in txc_stops.items():
            atco_code_upper = atco_code.upper()
            if atco_code_upper not in self.stops.keys():
                stoppoint = get_stop(stop.element, atco_code_upper)
                stoppoint["common_name"] = str(stop)
                stoppoint["point"] = from_shape(
                    Point([0, 0]), 4326
                )  # default to a valid point
                stops_to_add[atco_code_upper] = stoppoint

        if stops_to_add:
            log.debug(f"Adding {len(stops_to_add)} new stops")
            self.stats.stops_created += len(stops_to_add)
            bulk_upsert(
                self.db,
                Stop,
                list(stops_to_add.values()),
                ["atco_code"],
                [
                    "common_name",
                ],
            )

            self.db.flush()

            new_stops = (
                self.db.query(Stop)
                .filter(
                    func.upper(Stop.atco_code).in_(
                        [s.upper() for s in stops_to_add.keys()]
                    )
                )
                .all()
            )

            for stop in new_stops:
                self.stops[stop.atco_code] = stop

    def finish_services(self):
        for id in self.services:
            service = self.db.query(Service).filter_by(id=id).first()
            if not service:
                continue
            service.do_stopusages(db=self.db)
            service.do_geometry(db=self.db)
            self.db.add(service)
        self.db.commit()

    def handle_txc_file(self, file: Path):
        start = time.time()
        try:
            self.dsv = self.get_dsv()
            self.filename = file.name
            self.file_size_bytes = file.stat().st_size
            with open(file, "rb") as f:
                self.file_hash = hashlib.file_digest(f, "sha256").hexdigest()

            file_import_log = (
                self.db.query(FileImport)
                .filter_by(file_hash=self.file_hash, data_source_id=self.ds_id)
                .first()
            )

            self.hash_different = True

            if not file_import_log:
                file_import_log = FileImport(
                    filename=self.filename,
                    file_hash=self.file_hash,
                    size_bytes=self.file_size_bytes,
                    data_source_id=self.ds_id,
                    data_source_version_id=self.dsv_id,
                    processed_at=datetime.now(tz=LONDON),
                )
                self.db.add(file_import_log)
                self.db.flush()

            self.txc_data = self.processed_cache.get(
                file.as_posix(), None
            ) or txc.TransXChange(
                file
            )  # use cached as we already processed when making the map

            if not self.txc_data:
                log.warning("No TXC data loaded.")
                return
            # self.filename = self.txc_data.attributes.get("FileName", None)

            self.calendar_cache = {}

            # if not self.filename:
            #     log.warning(
            #         "No FileName attribute found in TXC data. using actual file name"
            #     )
            #     self.filename = file.name

            for op in self.txc_data.operators:
                txc_operator = TXCOperator(op)
                noc = txc_operator.get_noc()
                db_operator = self.db.query(Operator).filter_by(noc=noc).first()
                if not db_operator:
                    operator = Operator(noc=noc, name=txc_operator.name)
                    log.debug(f"Adding operator {txc_operator.name}")
                    db_operator = operator

                    self.db.add(operator)
                else:
                    if not self.operator_updated:
                        db_operator.name = txc_operator.name

                self.operator_updated = True

                self.operators[txc_operator.id] = db_operator

            self.db.flush()

            self.get_stops(self.txc_data.stops)

            for service_code, txc_service in self.txc_data.services.items():
                if self.service_line_key and self.service_line_key[0] != service_code:
                    log.debug(
                        f"Skipping {txc_service.service_code}, not the target service ({self.service_line_key[0]})"
                    )
                    continue
                self.handle_service(txc_service)

            self.db.commit()
            # update_dashboard()

        except Exception as e:
            log.error("An error occurred during txc import:")
            error_str = e.__str__()
            log.error(error_str[:1000])
            # log.debug(error_str)
            self.db.rollback()
        finally:
            self.db.close()
            end = time.time()
            log.debug(f"TXC Import completed in {end - start:.2f} seconds")


if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser(description="Import TXC data.")
    parser.add_argument("file", nargs="?", help="Path to TXC XML file or ZIP archive")
    parser.add_argument(
        "--ds-id",
        type=int,
        default=1,
        help="Datasource ID to reference (default: 1)",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Do not exit on conflict, e.g. same file hash",
    )
    args = parser.parse_args()
    input_path = args.file
    skip_checks = args.skip_checks
    ds_id = int(args.ds_id) if args.ds_id else None
    if input_path.lower().endswith(".zip"):
        import_txc_zip(input_path, ds_id=ds_id, skip_checks=skip_checks)
    elif input_path.lower().endswith(".xml"):
        txc_importer = TXCImporter(
            Path(input_path), ds_id=ds_id, skip_checks=skip_checks
        )
        txc_importer.handle_txc_file(Path(input_path))
        txc_importer.finish_services()
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
