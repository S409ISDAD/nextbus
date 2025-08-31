import asyncio
import logging
import sys
import zipfile
from datetime import datetime, timedelta, timezone
import isodate

from geoalchemy2.shape import from_shape, to_shape
from shapely import MultiLineString, Point
from shapely.geometry import LineString
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from backend.bot.bot import update_dashboard
from backend.db.db import SessionLocal
from backend.models import (
    BankHoliday,
    Calendar,
    CalendarException,
    CalendarToBankHoliday,
    Journey,
    Line,
    LineToRoute,
    Operator,
    Route,
    RouteSection,
    Service,
    Stop,
    StopTime,
    TrackSection,
    LineStopUsage,
)
from backend.txc import txc
from backend.utils.bulk_upsert import bulk_upsert
import concurrent.futures

logger = logging.getLogger(__name__)


def import_txc_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        xml_files = [
            filename for filename in zf.namelist() if filename.endswith(".xml")
        ]

        def process_xml(filename):
            with zf.open(filename) as xml_file:
                print(f"Processing file: {filename}")
                txc_importer = TXCImporter(xml_file)
                txc_importer.handle_txc_file()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(process_xml, xml_files)


# def import_txc_zip(zip_path):
#     with zipfile.ZipFile(zip_path, "r") as zf:
#         for filename in zf.namelist():
#             if filename.endswith(".xml"):
#                 with zf.open(filename) as xml_file:
#                     print(f"Processing file: {filename}")
#                     txc_importer = TXCImporter(xml_file)
#                     txc_importer.handle_txc_file()


class TXCImporter:
    def __init__(self, xml_file):
        self.txc_data = txc.TransXChange(xml_file)
        self.today = datetime.now(timezone.utc).astimezone(timezone.utc)
        self.service_id = None
        self.calendar_cache = {}
        self.db = SessionLocal()
        self.journeys_to_add = []
        self.stop_times_to_add = []
        self.line_to_routes = {}  # Maps line_id to a list of route IDs
        self.line_to_stops = {}  # Maps line_id to a list of stop IDs

    def get_id(self, id: str) -> str:
        """Generate a unique ID for the object based on the service code, as e.g. RS3 is only unique within a service."""

        return f"{self.service_id}:{id}" if self.service_id else id

    def get_description(self, txc_service: txc.Service):
        description = txc_service.description
        if not description:
            description = f"{txc_service.origin} - {txc_service.destination}"

        return description.strip() if description else "No description available"

    def parse_runtime(self, runtime: str) -> timedelta:
        """Parse the runtime string in ISO 8601 format (e.g., PT1H30M15S) and return a timedelta."""
        if not runtime or not runtime.startswith("PT"):
            return timedelta(0)
        return isodate.parse_duration(runtime)

    def get_calendar_exception(
        self,
        date_range: txc.DateRange | None = None,
        date=None,
        operation=True,
        description="",
    ):
        if date_range:
            start_date = date_range.start_date
            end_date = date_range.end_date
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
        line: Line,
    ):
        journey_code = self.get_id(line.line_name + ":" + txc_journey.journey_code)

        operating_profile = txc_journey.operating_profile
        regular_days_of_week = (
            operating_profile.regular_day_type.days_of_week if operating_profile else []
        )

        calendar_hash = f"{operating_profile.hash}{txc_service.operating_period}"

        if calendar_hash in self.calendar_cache:
            calendar = self.calendar_cache[calendar_hash]
        else:
            calendar = Calendar(
                start_date=txc_service.operating_period.start_date,
                end_date=txc_service.operating_period.end_date or None,
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

            for non_operation in operating_profile.non_operation_days:
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

            for serviced_organisation in self.txc_data.serviced_organisations:
                for working_day in serviced_organisation.working_days:
                    cal_exep = self.get_calendar_exception(
                        date_range=working_day,
                        operation=True,
                    )
                    cal_exep.calendar_id = calendar.id
                    self.db.add(cal_exep)

            bank_holidays_operation = (
                operating_profile.bank_holiday_operation.days_of_operation
            )
            bank_holidays_non_operation = (
                operating_profile.bank_holiday_operation.days_of_non_operation
            )

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

        journey_pattern = txc_service.journey_patterns.get(
            txc_journey.journey_pattern_ref
        )
        journey_pattern_section = self.txc_data.journey_pattern_sections[
            journey_pattern.journey_pattern_section_refs[0]
        ]

        start_time = txc_journey.departure_time

        stop_sequence = {}

        stops: dict[str, dict] = {}

        for timing_link in txc_journey.timing_links:
            journey_pattern_timing_link = journey_pattern_section.timing_links.get(
                timing_link.journey_pattern_timing_link_ref
            )
            if not journey_pattern_timing_link:
                continue
            track_section = (
                self.db.query(TrackSection)
                .filter_by(
                    route_link_ref=self.get_id(
                        journey_pattern_timing_link.route_link_ref
                    )
                )
                .first()
            )

            from_stop = journey_pattern_timing_link.from_stop
            from_seq = journey_pattern_timing_link.from_stop.sequence_number
            to_stop = journey_pattern_timing_link.to_stop
            to_seq = journey_pattern_timing_link.to_stop.sequence_number

            if from_stop and to_stop:
                stop_sequence[from_stop] = int(from_seq)
                stop_sequence[to_stop] = int(to_seq)

            stops[from_stop.stop_point_ref] = {
                "activity": from_stop.activity,
                "timing_status": from_stop.timing_status,
                "runtime": self.parse_runtime(timing_link.run_time),
                "distance": track_section.distance if track_section else 0.0,
            }

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

            cumulative_distance += stop_data["distance"] if stop_data else 0.0

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

        journey = {
            "id": journey_code,
            "service_code": service.service_code,
            "vehicle_journey_code": txc_journey.journey_code,
            "ticket_machine_code": txc_journey.ticket_machine_code,
            "line_id": line.id,
            "block_id": txc_journey.block,
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
            txc_service.operating_period.end_date
            if txc_service.operating_period
            else None
        )

        if end_date and end_date < self.today.date():
            print(
                f"Skipping journeys for {txc_service.service_code} as it ended on {end_date}"
            )
            skip_journeys = True

        description = self.get_description(txc_service)
        print(f"{txc_service.lines[0].line_name} {description}")

        self.service_id = txc_service.service_code

        db_service = (
            self.db.query(Service)
            .filter_by(service_code=txc_service.service_code)
            .first()
        )
        operator = (
            self.db.query(Operator)
            .filter_by(ref=txc_service.registered_operator_ref)
            .first()
        )
        service = Service(
            service_code=txc_service.service_code,
            description=description,
            origin=txc_service.origin,
            destination=txc_service.destination,
            vias=txc_service.vias,
            line_names=", ".join(
                line.line_name for line in txc_service.lines if line.line_name
            ),
            operator_noc=operator.noc if operator else None,
        )
        if not db_service:
            print(f"Adding service {txc_service.service_code}")
            self.db.add(service)
        else:
            print(f"Updating service {txc_service.service_code}")
            self.db.merge(service)
        self.db.flush()

        routes = set()

        for jp in txc_service.journey_patterns.values():
            route_ref = jp.route_ref
            if route_ref:
                routes.add(self.get_id(route_ref))

        for txc_line in txc_service.lines:
            db_line = self.db.query(Line).filter_by(id=txc_line.line_id).first()
            line = Line(
                id=txc_line.line_id,
                line_name=txc_line.line_name,
                inbound_description=txc_line.inbound_description.description
                if txc_line.inbound_description
                else None,
                outbound_description=txc_line.outbound_description.description
                if txc_line.outbound_description
                else None,
                service_code=txc_service.service_code,
            )
            if not db_line:
                print(f"Adding line {txc_line.line_id}")
                self.db.add(line)
            else:
                print(f"Updating line {txc_line.line_id}")
                self.db.merge(line)
            self.db.flush()
            self.line_to_routes.setdefault(txc_line.line_id, []).extend(routes)

            if skip_journeys:
                continue
            for txc_journey in self.txc_data.get_journeys(
                txc_line.line_id, txc_service.service_code
            ):
                if not txc_journey.journey_code:
                    print(
                        f"Skipping journey for service {txc_service.service_code} on line {txc_line.line_id} due to missing journey code"
                    )
                    continue
                self.handle_journey(txc_journey, txc_service, service, line)

    def handle_route_section(self, txc_route_section: txc.RouteSection):
        track_points: list[Point] = []
        track_points_to_create = []
        route_links = txc_route_section.route_links
        rs_id = self.get_id(txc_route_section.section_id)
        for link in route_links:
            points = [location.point for location in link.locations if location.point]
            track_points.extend(points)
            trackpoint = TrackSection(
                from_stop=link.from_stop,
                to_stop=link.to_stop,
                distance=link.distance,
                geometry=from_shape(LineString([pt.coords[0] for pt in points])),
                route_link_ref=self.get_id(link.route_link_id),
                route_section_id=rs_id,
            )
            track_points_to_create.append(trackpoint)

        if track_points:
            coords = [pt.coords[0] for pt in track_points]
            geometry = from_shape(LineString(coords))
        else:
            geometry = None

        db_route_section = self.db.query(RouteSection).filter_by(id=rs_id).first()
        route_section = RouteSection(
            id=rs_id,
            geometry=geometry,
        )
        if not db_route_section:
            self.db.add(route_section)
        else:
            self.db.merge(route_section)
        self.db.flush()

        self.db.bulk_save_objects(track_points_to_create)

    def update_geometry(self, line_id):
        print(f"Updating route overview geometry for line {line_id}")

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
            print(f"No line with id {line_id} found or no geometry to update.")
        else:
            print(f"Geometry updated for line {line_id}")

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
            .join(Route, Route.route_section_id == RouteSection.id)
            .join(LineToRoute, LineToRoute.route_id == Route.id)
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
            print(
                f"Merged geometry for line {line_id} is not a LineString or MultiLineString."
            )
            return None

    async def handle_txc_file(self):
        try:
            for txc_operator in self.txc_data.operators:
                db_operator = (
                    self.db.query(Operator)
                    .filter_by(noc=txc_operator.national_operator_code)
                    .first()
                )
                operator = Operator(
                    noc=txc_operator.national_operator_code,
                    ref=txc_operator.operator_id,
                    name=txc_operator.operator_name_on_licence
                    or txc_operator.trading_name,
                )
                if not db_operator:
                    print(f"Adding operator {txc_operator.operator_name_on_licence}")
                    self.db.add(operator)
                else:
                    print(f"Updating operator {txc_operator.operator_name_on_licence}")
                    self.db.merge(operator)

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
            print(f"Added {len(self.journeys_to_add)} journeys")
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
            print(f"Added {len(self.stop_times_to_add)} stop times")
            self.stop_times_to_add.clear()
            self.db.flush()

            for txc_route in self.txc_data.routes:
                route_id = self.get_id(txc_route.route_id)
                db_route = self.db.query(Route).filter_by(id=route_id).first()
                route_section_ref = txc_route.route_section_ref

                if route_section_ref:
                    route_section = self.txc_data.route_sections.get(route_section_ref)
                    if route_section:
                        self.handle_route_section(route_section)

                route = Route(
                    id=route_id,
                    private_code=txc_route.private_code,
                    description=txc_route.description,
                    route_section_id=self.get_id(route_section_ref),
                )
                if not db_route:
                    print(f"Adding route {route_id}")
                    self.db.add(route)
                else:
                    print(f"Updating route {route_id}")
                    self.db.merge(route)
            self.db.commit()

            for line_id, stop_codes in self.line_to_stops.items():
                for stop_code in stop_codes:
                    db_stop = (
                        self.db.query(LineStopUsage)
                        .filter_by(line_id=line_id, stop_id=stop_code)
                        .first()
                    )
                    if not db_stop:
                        ltr = LineStopUsage(
                            line_id=line_id,
                            stop_id=stop_code,
                        )
                        self.db.add(ltr)
                # self.update_geometry(line_id)
                self.db.flush()

            for line_id, route_ids in self.line_to_routes.items():
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
            await update_dashboard()
        except Exception as e:
            print("An error occurred during txc import:")
            error_str = e.__str__()
            print(error_str[:1000])
            # print(error_str)
            self.db.rollback()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_txc.py <path_to_zip_or_xml>")
        exit(1)
    input_path = sys.argv[1]
    if input_path.lower().endswith(".zip"):
        import_txc_zip(input_path)
    elif input_path.lower().endswith(".xml"):
        with open(input_path, "rb") as xml_file:
            txc_importer = TXCImporter(xml_file)
            asyncio.run(txc_importer.handle_txc_file())
    else:
        print("Error: Input must be a .zip or .xml file")
        exit(1)
