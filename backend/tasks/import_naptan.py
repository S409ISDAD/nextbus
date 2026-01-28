import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from ciso8601 import parse_datetime
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal, sync_stop_sv
from backend.db.db import engine
from backend.deps import LONDON
from backend.models import (
    Stop,
    StopArea,
    StopAreaTypeEnum,
    AdminArea,
    Locality,
)
from backend.utils.bulk_upsert import bulk_upsert
from backend.utils.download_to_static import download_to_static

log = get_logger(__name__)

new_stops = []
new_stop_areas = []
admin_areas = set()
localities = set()


def get_datetime(string):
    if string:
        datetime = parse_datetime(string)
        if not datetime.tzinfo:
            return datetime.replace(tzinfo=LONDON)
        return datetime


def get_point(element):
    if element is None:
        return

    easting = element.findtext("Easting")
    northing = element.findtext("Northing")
    grid_type = element.findtext("GridType")

    if not easting:
        easting = element.findtext("Translation/Easting")
        northing = element.findtext("Translation/Northing")
        grid_type = element.findtext("Translation/GridType")
    if easting:
        match grid_type:
            case "ITM":
                srid = 2157
            case "IrishOS":
                srid = 29902
            case "UKOS" | "" | None:
                srid = 27700
            case _:
                srid = 27700
        return from_shape(Point(float(easting), float(northing)), srid=srid)

    lon = element.findtext("Translation/Longitude") or element.findtext("Longitude")
    lat = element.findtext("Translation/Latitude") or element.findtext("Latitude")
    if lat is not None and lon is not None:
        return from_shape(Point(float(lon), float(lat)), srid=4326)


stop_mapping = (
    ("Descriptor/CommonName", "common_name"),
    ("Descriptor/Landmark", "landmark"),
    ("Descriptor/Street", "street"),
    ("Descriptor/Indicator", "indicator"),
    ("Descriptor/Crossing", "crossing"),
    ("Place/Suburb", "suburb"),
    ("Place/Town", "town"),
    ("StopClassification/StopType", "stop_type"),
    ("StopClassification/OnStreet/Bus/BusStopType", "bus_stop_type"),
    ("StopClassification/OnStreet/Bus/TimingStatus", "timing_status"),
)


def get_stop(element, atco_code):
    point = get_point(element.find("Place/Location"))

    naptan_code = element.findtext("NaptanCode")

    bearing = element.findtext(
        "StopClassification/OnStreet/Bus/MarkedPoint/Bearing/CompassPoint"
    )
    if bearing is None:
        bearing = element.findtext(
            "StopClassification/OnStreet/Bus/UnmarkedPoint/Bearing/CompassPoint"
        )
    if bearing is None:
        bearing = ""

    stop = {
        "atco_code": atco_code,
        "naptan_code": naptan_code,
        "bearing": bearing,
        "point": point,
        "search_name": "",
    }

    for xml_path, attr in stop_mapping:
        value = element.findtext(xml_path)
        if value:
            stop[attr] = value

    stop["active"] = element.attrib.get("Status", "active") == "active"

    if not stop["active"]:
        return None

    return stop


def get_stop_area(element: ET.Element):
    code = element.findtext("StopAreaCode")

    if element.attrib.get("Status") != "active":
        return None

    if code:
        point = get_point(element.find("Location"))

        try:
            stop_area_type = StopAreaTypeEnum(element.findtext("StopAreaType"))
        except Exception as e:
            log.warning(f"an error occurred parsing stop area type: {e}")
            stop_area_type = None

        return {
            "id": code,
            "name": element.findtext("Name"),
            "point": point,
            "active": element.attrib.get("Status", "active") == "active",
            "admin_area_id": element.findtext("AdministrativeAreaRef"),
            "type": stop_area_type,
            "revision_number": element.attrib.get("RevisionNumber"),
        }
    return None


def handle_stop_area(element: ET.Element):
    stop_area = get_stop_area(element)

    if stop_area:
        new_stop_areas.append(stop_area)


def handle_stop_point(element: ET.Element):
    atco_code = element.findtext("AtcoCode")

    if element.attrib.get("Status") != "active":
        return

    modified_at = get_datetime(element.attrib.get("ModificationDateTime"))
    created_at = get_datetime(element.attrib.get("CreationDateTime"))
    revision_number = element.attrib.get("RevisionNumber")

    stop = get_stop(element, atco_code)
    if not stop:
        return

    locality_id = element.findtext("Place/NptgLocalityRef")
    if locality_id not in localities:
        if locality_id not in localities_not_exist:
            log.debug(f"locality {locality_id} does not exist")
            localities_not_exist.add(locality_id)
        locality_id = None

    stop["locality_id"] = locality_id

    admin_area_id = int(element.findtext("AdministrativeAreaRef"))
    if admin_area_id not in admin_areas:
        log.debug(f"admin area {admin_area_id} does not exist")
        admin_area_id = None

    stop["admin_area_id"] = admin_area_id

    stop["modified_at"] = modified_at
    stop["created_at"] = created_at
    stop["revision_number"] = revision_number

    stop["search_name"] = ""

    for stop_area_ref in element.findall("StopAreas/StopAreaRef"):
        if stop_area_ref.attrib.get("Status") == "active":
            stop["stop_area_id"] = stop_area_ref.text

    new_stops.append(stop)


def create_or_update(db: Session, no_update: bool):
    if new_stop_areas:
        log.debug(f"Importing {len(new_stop_areas)} Stop Areas.")
        if no_update:
            db.bulk_insert_mappings(StopArea, new_stop_areas)
            db.commit()
        else:
            bulk_upsert(
                db,
                StopArea,
                new_stop_areas,
                ["id"],
                ["name", "point", "active", "type", "revision_number"],
            )

    stop_areas = {code[0] for code in db.query(StopArea.id).all()}

    unknown_stop_areas = {
        stop.get("stop_area_id")
        for stop in new_stops
        if stop.get("stop_area_id") not in stop_areas
        and stop.get("stop_area_id") is not None
    }

    new_stop_areas_2 = []

    for stop_area_code in unknown_stop_areas:
        stop_area = StopArea(
            id=stop_area_code,
            active=True,
        )
        new_stop_areas_2.append(stop_area)

    if new_stop_areas_2:
        log.debug(f"Importing {len(new_stop_areas_2)} Stop Areas that didnt exist")
        db.bulk_save_objects(new_stop_areas_2)
        db.commit()

    if new_stops:
        log.debug(f"Importing {len(new_stops)} Stops.")
        if no_update:
            db.bulk_insert_mappings(Stop, new_stops)
            db.commit()
        else:
            bulk_upsert(
                db,
                Stop,
                new_stops,
                ["atco_code"],
                [
                    "naptan_code",
                    "point",
                    "common_name",
                    "landmark",
                    "street",
                    "indicator",
                    "crossing",
                    "suburb",
                    "town",
                    "stop_type",
                    "bus_stop_type",
                    "timing_status",
                    "stop_area_id",
                    "modified_at",
                    "created_at",
                    "revision_number",
                    "search_name",
                ],
            )


def import_naptan_data(file_path: Path, no_update=False):
    log.debug("Importing NAPTAN data...")

    global new_stops, existing_stop_ids, stop_area_ids, new_stop_areas, admin_areas, localities, localities_not_exist

    iterator = ET.iterparse(file_path, events=("start", "end"))
    with SessionLocal() as db:
        try:
            # collect existing data
            existing_stop_ids = {
                atco_code[0] for atco_code in db.query(Stop.atco_code).all()
            }
            stop_area_ids = {code[0] for code in db.query(StopArea.id).all()}
            admin_areas = {adm[0] for adm in db.query(AdminArea.id).all()}
            localities = {loc[0] for loc in db.query(Locality.id).all()}
            localities_not_exist = set()
            log.debug("Loaded existing data")

            for event, element in iterator:  # loop over the streamed XML file
                element.tag = element.tag.removeprefix(
                    "{http://www.naptan.org.uk/}"
                )  # remove the tag prefix
                if event == "end":
                    if element.tag == "StopPoint":
                        # a StopPoint is a single bus stop.
                        handle_stop_point(element)
                    if element.tag == "StopArea":
                        # a StopArea is a collection of stops, e.g. a bus station.
                        handle_stop_area(element)

            create_or_update(db, no_update)

            log.debug("Updating search vectors...")
            with engine.begin() as conn:
                sync_stop_sv(conn)
            log.debug("Import complete.")
        except Exception as e:
            log.error("An error occurred during NaPTAN import:")
            error_str = e.__str__()
            log.error(error_str[:1000])
            # log.debug(error_str)
            db.rollback()


def main():
    parser = argparse.ArgumentParser(description="Import NaPTAN data.")
    parser.add_argument("file", nargs="?", help="Path to NaPTAN XML file")
    parser.add_argument(
        "--no_update", action="store_true", help="Do not update search vectors"
    )
    args = parser.parse_args()

    from_internet = False
    if not args.file:
        from_internet = True
        url = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml"

        log.debug(f"Downloading NAPTAN data from {url}...")
        naptan_path = download_to_static(url, "NaPTAN.xml")
        if not naptan_path:
            log.debug("Failed to download NAPTAN data.")
            sys.exit(1)
    else:
        naptan_path = Path(args.file)

    try:
        import_naptan_data(naptan_path, args.no_update)
    except KeyboardInterrupt:
        log.debug("Stopped by user.")
    finally:
        if from_internet:
            naptan_path.unlink()
        log.debug("done.")


if __name__ == "__main__":
    setup_logging()
    main()
