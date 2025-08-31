from pathlib import Path
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from backend.db.db import SessionLocal
from backend.models import (
    Stop,
    StopArea,
    StopAreaTypeEnum,
)
from sqlalchemy.orm import Session
import sys
import xml.etree.ElementTree as ET
from datetime import timedelta, timezone


from ciso8601 import parse_datetime

new_stops = []
updated_stops = []
new_stop_areas = []
updated_stop_areas = []


def generate_point(lat, lon):
    """Generate a Point object from latitude and longitude."""
    return from_shape(Point(lon, lat), srid=4326)


def get_datetime(string):
    if string:
        datetime = parse_datetime(string)
        if not datetime.tzinfo:
            uk_timezone = timezone(timedelta(hours=1))
            return datetime.replace(tzinfo=uk_timezone)
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

    stop = Stop(
        atco_code=atco_code,
        naptan_code=naptan_code,
        point=point,
    )

    for xml_path, attr in stop_mapping:
        value = element.findtext(xml_path)
        if value:
            setattr(stop, attr, value)

    return stop


def get_stop_area(element: ET.Element):
    code = element.findtext("StopAreaCode")

    if element.attrib.get("Status") != "active":
        return None

    if code:
        point = get_point(element.find("Location"))

        try:
            type = StopAreaTypeEnum(element.findtext("StopAreaType"))
        except:
            return None

        return StopArea(
            id=code,
            name=element.findtext("Name"),
            point=point,
            active=element.attrib.get("Status", "active") == "active",
            type=type,
            revision_number=element.attrib.get("RevisionNumber"),
        )
    return None


def handle_stop_area(element: ET.Element):
    stop_area = get_stop_area(element)

    if stop_area:
        if getattr(stop_area, "id") in stop_area_ids:
            updated_stop_areas.append(stop_area)
        else:
            new_stop_areas.append(stop_area)


def handle_stop_point(element: ET.Element):
    atco_code = element.findtext("AtcoCode")

    if element.attrib.get("Status") != "active":
        return

    modified_at = get_datetime(element.attrib.get("ModificationDateTime"))
    created_at = get_datetime(element.attrib.get("CreationDateTime"))
    revision_number = element.attrib.get("RevisionNumber")

    stop = get_stop(element, atco_code)

    setattr(stop, "modified_at", modified_at)
    setattr(stop, "created_at", created_at)
    setattr(stop, "revision_number", revision_number)

    for stop_area_ref in element.findall("StopAreas/StopAreaRef"):
        if stop_area_ref.attrib.get("Status") == "active":
            setattr(stop, "stop_area_id", stop_area_ref.text)

    if atco_code in existing_stop_ids:
        updated_stops.append(stop)
    else:
        new_stops.append(stop)


def create_or_update(db: Session):
    if new_stop_areas:
        print(f"Importing {len(new_stop_areas)} Stop Areas.")
        db.bulk_save_objects(new_stop_areas)
        db.commit()

    if updated_stop_areas:
        print(f"Updating {len(updated_stop_areas)} Stop Areas.")
        for stop_area in updated_stop_areas:
            db.merge(stop_area)
        db.commit()

    stop_areas = {code[0] for code in db.query(StopArea.id).all()}

    unknown_stop_areas = {
        stop.stop_area_id
        for stop in new_stops
        if stop.stop_area_id not in stop_areas and stop.stop_area_id is not None
    }

    new_stop_areas_2 = []

    for stop_area_code in unknown_stop_areas:
        stop_area = StopArea(
            id=stop_area_code,
            active=True,
        )
        new_stop_areas_2.append(stop_area)

    if new_stop_areas_2:
        print(f"Importing {len(new_stop_areas_2)} Stop Areas that didnt exist")
        db.bulk_save_objects(new_stop_areas_2)
        db.commit()

    if new_stops:
        print(f"Importing {len(new_stops)} Stops.")
        db.bulk_save_objects(new_stops)
        db.commit()

    if updated_stops:
        print(f"Updating {len(updated_stops)} Stops.")
        for stop in updated_stops:
            db.merge(stop)
        db.commit()


def import_naptan_data(file_path: Path):
    print("Importing NAPTAN data...")

    global \
        new_stops, \
        updated_stops, \
        existing_stop_ids, \
        stop_area_ids, \
        updated_stop_areas, \
        new_stop_areas

    iterator = ET.iterparse(file_path, events=("start", "end"))
    with SessionLocal() as db:
        try:
            existing_stop_ids = {
                atco_code[0] for atco_code in db.query(Stop.atco_code).all()
            }
            stop_area_ids = {code[0] for code in db.query(StopArea.id).all()}
            print("Loaded existing data")
            for event, element in iterator:
                element.tag = element.tag.removeprefix("{http://www.naptan.org.uk/}")
                if event == "end":
                    if element.tag == "StopPoint":
                        handle_stop_point(element)
                    if element.tag == "StopArea":
                        handle_stop_area(element)

            create_or_update(db)
            print("Import complete.")
        except Exception as e:
            print("An error occurred during NaPTAN import:")
            error_str = e.__str__()
            print(error_str[:1000])
            # print(error_str)
            db.rollback()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: <path_to_naptan_xml>")
        sys.exit(1)
    naptan_path = Path(sys.argv[1])
    import_naptan_data(naptan_path)
    print("done.")
