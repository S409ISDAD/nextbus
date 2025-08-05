from datetime import datetime, timezone
import zipfile
import os
import sys

import xml.etree.ElementTree as ET
from backend.core.db import SessionLocal
from backend.models import Service, Stop, Route
from backend.txc import txc
import logging

logger = logging.getLogger(__name__)


not_found = 0


def import_txc_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf, SessionLocal() as db:
        for filename in zf.namelist():
            if filename.endswith(".xml"):
                with zf.open(filename) as xml_file:
                    print(f"Processing file: {filename}")
                    handle_txc_file(xml_file, db)
                    # break  # only process one for testing


def process_stops(txc: txc.TransXChange, db):
    global not_found
    db_stops = db.query(Stop).filter(Stop.id.in_(txc.stops.keys())).all()
    found_stop_ids = {stop.id for stop in db_stops}
    missing_stops = [stop for stop in txc.stops.keys() if stop not in found_stop_ids]
    for stop in missing_stops:
        print(f"Stop {stop} not found in the database.")
        not_found += 1
        # stop_obj = Stop(
        #     id=stop, name=txc.stops[stop].common_name, atco_code=stop
        # )
        # db.add(stop_obj)
        # db.commit()
        # print(f"Added stop {stop} to the database.")
    print(f"Found {len(db_stops)} of {len(txc.stops)} stops in the database")
    if missing_stops:
        print(f"Stops not found in the database: {sorted(missing_stops)}")
    return db_stops


def process_service(today, 
    txc: txc.TransXChange, txc_service: txc.Service, stops: list[Stop], db
):
    if (
            txc_service.operating_period.end
            and txc_service.operating_period.end < today
        ):
            logger.warning(
                f"{txc_service.service_code} end {txc_service.operating_period.end} is in the past"
            )
            skip_journeys = True
    print(
        f"Processing service {txc_service.service_code} from {txc_service.origin} to {txc_service.destination}"
    )
    for line in txc_service.lines:
        print(f"Processing line {line.line_name}")

        journeys = txc.get_journeys(txc_service.service_code, line.id)

        print(f"Found {len(journeys)} journeys for service {txc_service.service_code}")

        for journey in journeys:
            times = journey.get_times()
            # for time in times:
            #     print(f"Processing time {time.activity} {time.departure_time}")

        route = Route(
            id=line.id,
            agency_id=None,
            service_code=txc_service.service_code,
            mode=txc_service.mode,
            name=txc_service.lines[0].line_name,
            origin=txc_service.origin,
            destination=txc_service.destination,
            colour=None,
            text_color=None,
        )
        print(f"Adding route {route.name} to the database")
        existing_route = db.query(Route).filter_by(id=route.id).first()
        if existing_route:
            needs_update = (
                existing_route.name != route.name
                or existing_route.origin != route.origin
                or existing_route.destination != route.destination
                or existing_route.colour != route.colour
                or existing_route.text_color != route.text_color
                or existing_route.mode != route.mode
                or existing_route.agency_id != route.agency_id
            )
            if needs_update:
                print(f"Route {route.name} already exists, updating.")
                existing_route.name = route.name
                existing_route.origin = route.origin
                existing_route.destination = route.destination
                existing_route.colour = route.colour
                existing_route.text_color = route.text_color
                existing_route.mode = route.mode
                existing_route.agency_id = route.agency_id
                db.merge(existing_route)
            else:
                print(f"Route {route.name} already exists, no update needed.")
        else:
            print(f"Route {route.name} does not exist, adding.")
            db.add(route)
            
    calendar = 
    service = Service(
        id=txc_service.service_code,
    )
    db.add(service)


def handle_txc_file(xml_file, db):
    txc_data = txc.TransXChange(xml_file)
    stops = process_stops(txc_data, db)

    today = datetime.now(timezone.utc).astimezone(timezone.utc)

    for txc_service in txc_data.services.values():
        process_service(today, txc_data, txc_service, stops, db)

    db.commit()  # Commit once after processing all services for this file

    print("Import completed successfully.")
    print(f"Total stops not found: {not_found}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_txc.py <path_to_zip>")
        exit(1)
    import_txc_zip(sys.argv[1])
    print(f"Total stops not found: {not_found}")
