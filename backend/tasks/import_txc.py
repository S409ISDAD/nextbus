import logging
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta, timezone
import isodate

from geoalchemy2.shape import from_shape
from shapely import Point
from shapely.geometry import LineString
from sqlalchemy.orm import Session

from backend.db.db import SessionLocal
from backend.models import (
    Calendar,
    Journey,
    Line,
    Operator,
    Route,
    RouteSection,
    Service,
    Stop,
    StopTime,
    TrackSection,
)
from backend.txc import txc

logger = logging.getLogger(__name__)


service_id = ""


def import_txc_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        for filename in zf.namelist():
            if filename.endswith(".xml"):
                with zf.open(filename) as xml_file:
                    print(f"Processing file: {filename}")
                    handle_txc_file(xml_file)
                    # break  # only process one for testing


def get_id(id: str) -> str:
    """Generate a unique ID for the object based on the service code, as e.g. RS3 is only unique within a service."""

    return f"{service_id}:{id}" if service_id else id


def get_description(txc_service: txc.Service):
    description = txc_service.description
    if not description:
        description = f"{txc_service.origin} - {txc_service.destination}"

    return description.strip() if description else "No description available"


def parse_runtime(runtime: str) -> timedelta:
    """Parse the runtime string in ISO 8601 format (e.g., PT1H30M15S) and return a timedelta."""
    if not runtime or not runtime.startswith("PT"):
        return timedelta(0)
    return isodate.parse_duration(runtime)


def handle_journey(
    txc: txc.TransXChange,
    txc_journey: txc.VehicleJourney,
    txc_service: txc.Service,
    service: Service,
    line: Line,
    today,
    db: Session,
):
    journey_code = get_id(txc_journey.journey_code)

    journey_pattern = txc_service.journey_patterns.get(txc_journey.journey_pattern_ref)
    journey_pattern_section = txc.journey_pattern_sections[
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
            db.query(TrackSection)
            .filter_by(
                route_link_ref=get_id(journey_pattern_timing_link.route_link_ref)
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
            "runtime": parse_runtime(timing_link.run_time),
            "distance": track_section.distance if track_section else 0.0,
        }

    cumulative_distance = 0.0
    cumulative_time = start_time

    sorted_stops = sorted(stops.items(), key=lambda item: stop_sequence.get(item[0], 0))

    for i, (stop_ref, stop_data) in enumerate(sorted_stops, start=1):
        seq = i
        stop_data = stops.get(stop_ref)

        cumulative_time += (
            stop_data["runtime"]
            if stop_data and "runtime" in stop_data
            else timedelta(0)
        )
        cumulative_distance += stop_data["distance"] if stop_data else 0.0

        stoptime = (
            db.query(StopTime)
            .filter_by(journey_id=journey_code, stop_sequence=seq)
            .first()
        )
        if not stoptime:
            activity = stop_data.get("activity") if stop_data else None
            pick_up = "pickup" in activity.lower() if activity else False
            drop_off = "setdown" in activity.lower() if activity else False
            stoptime = StopTime(
                journey_id=journey_code,
                stop_id=stop_ref,
                pick_up=pick_up,
                drop_off=drop_off,
                departure_time=cumulative_time,
                arrival_time=cumulative_time,
                stop_sequence=seq,
                distance_traveled=cumulative_distance,
                timing_status=stop_data["timing_status"]
                if stop_data and "timing_status" in stop_data
                else None,
                wait_time=timedelta(0),
            )
            db.add(stoptime)

    journey = db.query(Journey).filter_by(id=journey_code).first()

    if not journey:
        print(f"Adding journey {journey_code}")
        journey = Journey(
            id=journey_code,
            service_code=service.service_code,
            line_id=line.id,
            direction=journey_pattern.direction if journey_pattern else None,
            start_time=start_time,
            end_time=cumulative_time,
        )
        db.add(journey)
        db.commit()


def handle_service(txc: txc.TransXChange, txc_service: txc.Service, today, db: Session):
    skip_journeys = False

    end_date = (
        txc_service.operating_period.end_date if txc_service.operating_period else None
    )

    if end_date and end_date < today.date():
        print(f"Skipping service {txc_service.service_code} as it ended on {end_date}")
        skip_journeys = True

    description = get_description(txc_service)
    print(f"{txc_service.lines[0].line_name} {description}")

    service_id = txc_service.service_code

    service = db.query(Service).filter_by(service_code=txc_service.service_code).first()
    operator = (
        db.query(Operator).filter_by(ref=txc_service.registered_operator_ref).first()
    )
    if not service:
        print(f"Adding service {txc_service.service_code}")
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
        db.add(service)
        db.commit()

    for txc_line in txc_service.lines:
        line = db.query(Line).filter_by(id=txc_line.line_id).first()
        if not line:
            print(f"Adding line {txc_line.line_id}")
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
            db.add(line)
            db.commit()

        if skip_journeys:
            continue
        for txc_journey in txc.get_journeys(txc_line.line_id, txc_service.service_code):
            if not txc_journey.journey_code:
                print(
                    f"Skipping journey for service {txc_service.service_code} on line {txc_line.line_id} due to missing journey code"
                )
                continue
            handle_journey(txc, txc_journey, txc_service, service, line, today, db)


def handle_route_section(txc_route_section: txc.RouteSection, db: Session):
    track_points: list[Point] = []
    track_points_to_create = []
    route_links = txc_route_section.route_links
    rs_id = get_id(txc_route_section.section_id)
    for link in route_links:
        points = [location.point for location in link.locations if location.point]
        track_points.extend(points)
        trackpoint = TrackSection(
            from_stop=link.from_stop,
            to_stop=link.to_stop,
            distance=link.distance,
            geometry=from_shape(LineString([pt.coords[0] for pt in points])),
            route_link_ref=get_id(link.route_link_id),
            route_section_id=rs_id,
        )
        track_points_to_create.append(trackpoint)

    if track_points:
        coords = [pt.coords[0] for pt in track_points]
        geometry = from_shape(LineString(coords))
    else:
        geometry = None

    route_section = db.query(RouteSection).filter_by(id=rs_id).first()
    if not route_section:
        print(f"Adding route section {rs_id}")
        route_section = RouteSection(
            id=rs_id,
            geometry=geometry,
        )
        db.add(route_section)
        db.commit()

    db.bulk_save_objects(track_points_to_create)
    db.commit()


def handle_txc_file(xml_file):
    txc_data = txc.TransXChange(xml_file)
    today = datetime.now(timezone.utc).astimezone(timezone.utc)

    global service_id

    with SessionLocal() as db:
        for txc_operator in txc_data.operators:
            operator = (
                db.query(Operator)
                .filter_by(noc=txc_operator.national_operator_code)
                .first()
            )
            if not operator:
                print(f"Adding operator {txc_operator.operator_name_on_licence}")
                operator = Operator(
                    noc=txc_operator.national_operator_code,
                    ref=txc_operator.operator_id,
                    name=txc_operator.operator_name_on_licence
                    or txc_operator.trading_name,
                )
                db.add(operator)
        db.commit()

        for txc_service in txc_data.services:
            service_id = txc_service.service_code

        for txc_route in txc_data.routes:
            route_id = get_id(txc_route.route_id)
            route = db.query(Route).filter_by(id=route_id).first()
            if not route:
                print(f"Adding route {route_id}")
                route_section_ref = txc_route.route_section_ref

                if route_section_ref:
                    route_section = txc_data.route_sections.get(route_section_ref)
                    if route_section:
                        handle_route_section(route_section, db)

                route = Route(
                    id=route_id,
                    private_code=txc_route.private_code,
                    description=txc_route.description,
                    route_section_id=get_id(route_section_ref),
                )
                db.add(route)

        for txc_service in txc_data.services:
            handle_service(txc_data, txc_service, today, db)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_txc.py <path_to_zip_or_xml>")
        exit(1)
    input_path = sys.argv[1]
    if input_path.lower().endswith(".zip"):
        import_txc_zip(input_path)
    elif input_path.lower().endswith(".xml"):
        with open(input_path, "rb") as xml_file:
            handle_txc_file(xml_file)
    else:
        print("Error: Input must be a .zip or .xml file")
        exit(1)
