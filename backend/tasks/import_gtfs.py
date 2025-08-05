import partridge as ptg
import pandas as pd
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString
from sqlalchemy.dialects.postgresql import insert as pg_insert
from backend.core.db import SessionLocal
from backend.models import (
    Agency,
    FeedInfo,
    Frequency,
    Route,
    Service,
    Calendar,
    CalendarDate,
    Shape,
    ShapePoint,
    Trip,
    Stop,
    StopTime,
    LocationType,
    RouteType,
    ExceptionType,
    WheelchairAccessible,
    PickupDropOffType,
)
from sqlalchemy.orm import Session
import sys

from shapely.wkb import loads as wkb_loads


def safe_int(value):
    try:
        if value == "" or pd.isnull(value):
            return 0
        return int(value)
    except (ValueError, TypeError):
        return 0


def safe_float(value):
    try:
        if value == "" or pd.isnull(value):
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def needs_update(db: Session, model, instance):
    """
    Check if the instance needs to be updated based on its attributes.
    Returns a dictionary of changed attributes if updates are needed, otherwise None.
    """
    pk_columns = [col.name for col in model.__table__.primary_key.columns]
    filter_kwargs = {col: getattr(instance, col) for col in pk_columns}
    existing_instance = db.query(model).filter_by(**filter_kwargs).first()
    if not existing_instance:
        return True  # New instance, needs to be inserted

    changes = {}
    for attr in instance.__table__.columns.keys():
        new_value = getattr(instance, attr)
        old_value = getattr(existing_instance, attr)
        if new_value != old_value:
            changes[attr] = new_value

    return changes if changes else None


def upsert(
    db: Session,
    model,
    rows: pd.DataFrame,
    conflict_columns: list,
    mapping: dict,
    batch_size: int = 5000,
):
    """
    Perform an upsert operation for a given SQLAlchemy model using a list of JSON-like dictionaries, in batches.

    Args:
        db (Session): SQLAlchemy database session.
        model (Base): SQLAlchemy model class.
        rows (list[dict]): List of dictionaries representing rows to upsert.
        conflict_columns (list): List of column names to check for conflicts (e.g., primary keys).
        batch_size (int): Number of records per batch.
    """
    try:
        if rows is None or (hasattr(rows, "empty") and rows.empty):
            return  # No rows to upsert

        # Exclude generated columns from the update set
        generated_columns = {
            col.name
            for col in model.__table__.columns
            if getattr(col, "computed", None) is not None
        }
        update_columns = {
            col.name: col
            for col in model.__table__.columns
            if col.name not in conflict_columns and col.name not in generated_columns
        }

        batch = []
        counter = 0
        for _, orig_row in rows.iterrows():
            row = {
                table_col: orig_row[df_col]
                for table_col, df_col in mapping.items()
                if df_col is not None and df_col in orig_row
            }
            # instance = model(**row)
            needs = True
            # needs = needs_update(db, model, instance)
            if needs:  # Only upsert if new or changed
                batch.append(row)
                counter += 1
                if len(batch) >= batch_size:
                    percent = (counter) / len(rows) * 100
                    print(f"Upserting batch {counter // batch_size} ({percent:.2f}%)")
                    stmt = pg_insert(model).values(batch)
                    if update_columns:
                        stmt = stmt.on_conflict_do_update(
                            index_elements=conflict_columns,
                            set_=update_columns,
                        )
                    db.execute(stmt)
                    db.commit()
                    batch = []
        # Upsert any remaining rows
        if batch:
            percent = 100
            print(f"Upserting final batch ({percent:.2f}%)")
            stmt = pg_insert(model).values(batch)
            if update_columns:
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_columns,
                    set_=update_columns,
                )
                db.execute(stmt)
                db.commit()
    except Exception as e:
        db.rollback()
        raise e


def build_line_string(points: list[Point]):
    """Build a LineString from a list of points."""
    if not points:
        return None
    coords = [(point.x, point.y) for point in points]
    return from_shape(LineString(coords), srid=4326)


def generate_point(lat, lon):
    """Generate a Point object from latitude and longitude."""
    return from_shape(Point(lon, lat), srid=4326)


def import_feed_info(db: Session, feed_info: pd.DataFrame):
    print("Importing feed info...")
    if feed_info is None or feed_info.empty:
        print("No feed info available in GTFS feed.")
        return

    feed_info = feed_info.where(pd.notnull(feed_info), None)

    mapping = {
        "publisher_name": "feed_publisher_name",
        "publisher_url": "feed_publisher_url",
        "lang": "feed_lang",
        "start_date": "feed_start_date",
        "end_date": "feed_end_date",
        "version": "feed_version",
    }

    upsert(db, FeedInfo, feed_info, ["publisher_name"], mapping)
    print(f"Imported {len(feed_info)} feed info entries.")


def import_agencies(db: Session, agencies: pd.DataFrame):
    print("Importing agencies...")
    if agencies is None or agencies.empty:
        print("No agencies available in GTFS feed.")
        return

    agencies = agencies.where(pd.notnull(agencies), None)

    mapping = {
        "id": "agency_id",
        "name": "agency_name",
        "url": "agency_url",
        "timezone": "agency_timezone",
        "lang": "agency_lang",
        "phone": "agency_phone",
        "noc": "agency_noc",
    }

    upsert(db, Agency, agencies, ["id"], mapping)
    print(f"Imported {len(agencies)} agencies.")


def import_routes(db: Session, routes: pd.DataFrame):
    print("Importing routes...")
    if routes is None or routes.empty:
        print("No routes available in GTFS feed.")
        return

    routes = routes.where(pd.notnull(routes), None)

    routes["route_type"] = routes["route_type"].map(
        lambda x: RouteType(x) if not pd.isnull(x) else None
    )
    routes["route_long_name"] = routes["route_long_name"].fillna("")

    mapping = {
        "id": "route_id",
        "agency_id": "route_agency_id",
        "short_name": "route_short_name",
        "long_name": "route_long_name",
        "type": "route_type",
    }

    upsert(db, Route, routes, ["id"], mapping)
    print(f"Imported {len(routes)} routes.")


def import_calendar(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_calendar_entries = 0
    print(f"Importing {total_rows} calendar entries...")

    for calendar_df in pd.read_csv(file_path, chunksize=10000):
        calendar_df = calendar_df.where(pd.notnull(calendar_df), None)
        calendar_df["start_date"] = pd.to_datetime(
            calendar_df["start_date"], format="%Y%m%d"
        )
        calendar_df["end_date"] = pd.to_datetime(
            calendar_df["end_date"], format="%Y%m%d"
        )

        all_service_ids = {service.id for service in db.query(Service).all()}
        service_ids = set(calendar_df["service_id"].dropna().unique())
        new_service_ids = service_ids - all_service_ids

        service_rows = [{"id": service_id} for service_id in new_service_ids]
        if service_rows:
            print(f"Upserting {len(service_rows)} new services.")
            upsert(db, Service, service_rows, ["id"])

        rows = calendar_df.to_dict(orient="records")
        total_calendar_entries += len(rows)

        upsert(db, Calendar, rows, ["service_id"])
        percent = (total_calendar_entries / total_rows) * 100 if total_rows > 0 else 100
        print(f"Imported {total_calendar_entries} calendar entries. ({percent:.2f}%)")


def import_calendar_dates(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_calendar_dates = 0
    print(f"Importing {total_rows} calendar dates...")

    for calendar_dates_df in pd.read_csv(file_path, chunksize=10000):
        calendar_dates_df = calendar_dates_df.where(pd.notnull(calendar_dates_df), None)
        calendar_dates_df["date"] = pd.to_datetime(
            calendar_dates_df["date"], format="%Y%m%d"
        )
        calendar_dates_df["exception_type"] = calendar_dates_df["exception_type"].apply(
            ExceptionType
        )

        all_service_ids = {service.id for service in db.query(Service).all()}
        service_ids = set(calendar_dates_df["service_id"].dropna().unique())
        new_service_ids = service_ids - all_service_ids

        service_rows = [{"id": service_id} for service_id in new_service_ids]
        if service_rows:
            print(f"Upserting {len(service_rows)} new services.")
            upsert(db, Service, service_rows, ["id"])

        rows = calendar_dates_df.to_dict(orient="records")
        total_calendar_dates += len(rows)
        percent = (total_calendar_dates / total_rows) * 100 if total_rows > 0 else 100
        upsert(db, CalendarDate, rows, ["service_id", "date"])
        print(
            f"Imported {total_calendar_dates} calendar date entries. ({percent:.2f}%)"
        )


def import_shapes(db: Session, shapes: pd.DataFrame):
    print(f"Importing {len(shapes)} shapes...")

    shapes = shapes.where(pd.notnull(shapes), None)

    mapping = {
        "id": "shape_id",
        "geometry": "geometry",
    }

    upsert(db, Shape, shapes, ["shape_id"], mapping)
    print(f"Imported {len(shapes)} shapes.")


def import_stops(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_stops = 0
    print(f"Importing {total_rows} stops...")

    stops_df = pd.read_csv(file_path, low_memory=False)

    stops_df = stops_df.where(pd.notnull(stops_df), None)
    parent_stops = stops_df[stops_df["parent_station"].notnull()]
    child_stops = stops_df[stops_df["parent_station"].isnull()]

    parent_rows = [
        {
            "id": row.get("stop_id"),
            "code": row.get("stop_code"),
            "name": row.get("stop_name"),
            "point": generate_point(float(row["stop_lat"]), float(row["stop_lon"])),
            "zone_id": row.get("zone_id"),
            "url": row.get("stop_url"),
            "location_type": LocationType(row.get("location_type"))
            if not pd.isnull(row.get("location_type"))
            else LocationType.STOP,
            "parent_station_id": None,
            "desc": row.get("stop_desc"),
            "timezone": row.get("stop_timezone"),
            "wheelchair_boarding": row.get("wheelchair_boarding"),
            "level_id": row.get("level_id"),
            "platform_code": row.get("platform_code"),
        }
        for _, row in parent_stops.iterrows()
    ]

    rows = [row for row in parent_rows if row["id"] is not None]

    upsert(db, Stop, rows, ["id"])
    total_stops += len(rows)
    percent = (total_stops / total_rows) * 100 if total_rows > 0 else 100
    print(f"Total: {total_stops} parent stops. ({percent:.2f}%)")

    child_rows = [
        {
            "id": row.get("stop_id"),
            "code": row.get("stop_code"),
            "name": row.get("stop_name"),
            "point": generate_point(float(row["stop_lat"]), float(row["stop_lon"])),
            "zone_id": row.get("zone_id"),
            "url": row.get("stop_url"),
            "location_type": LocationType(row.get("location_type"))
            if not pd.isnull(row.get("location_type"))
            else LocationType.STOP,
            "parent_station_id": row.get("parent_station"),
            "desc": row.get("stop_desc"),
            "timezone": row.get("stop_timezone"),
            "wheelchair_boarding": row.get("wheelchair_boarding"),
            "level_id": row.get("level_id"),
            "platform_code": row.get("platform_code"),
        }
        for _, row in child_stops.iterrows()
    ]

    rows = [row for row in child_rows if row["id"] is not None]

    upsert(db, Stop, rows, ["id"])
    total_stops += len(rows)
    percent = (total_stops / total_rows) * 100 if total_rows > 0 else 100
    print(f"Total: {total_stops} parent and child stops. ({percent:.2f}%)")


def import_trips(db: Session, trips: pd.DataFrame, shapes: pd.DataFrame):
    print(f"Importing {len(trips)} trips...")

    trips = trips.where(pd.notnull(trips), None)

    trips["wheelchair_accessible"] = trips["wheelchair_accessible"].map(
        lambda x: WheelchairAccessible(x) if not pd.isna(x) else None
    )

    # Only keep shape_ids present in trips to reduce memory usage
    relevant_shape_ids = set(trips["shape_id"].dropna().unique())
    filtered_shapes = shapes[shapes["shape_id"].isin(relevant_shape_ids)]
    shape_map = pd.Series(
        filtered_shapes["geometry"].values, index=filtered_shapes["shape_id"]
    )

    # Use .map with fillna(None) to avoid double mapping and keep dtype=object
    def to_shapely_line(geom):
        if geom is None or pd.isnull(geom):
            return None
        # If already a LineString, return as is
        if isinstance(geom, LineString):
            return from_shape(geom)
        # If WKB hex or bytes, convert to LineString
        try:
            if isinstance(geom, (bytes, memoryview)):
                return from_shape(wkb_loads(bytes(geom)))
            if isinstance(geom, str):
                return from_shape(wkb_loads(bytes.fromhex(geom)))
        except Exception:
            return None
        return None

    trips["shape"] = (
        trips["shape_id"].map(shape_map).where(pd.notnull(trips["shape_id"]), None)
    )
    trips["shape"] = trips["shape"].map(to_shapely_line)

    mapping = {
        "id": "trip_id",
        "route_id": "route_id",
        "service_id": "service_id",
        "headsign": "trip_headsign",
        "direction": "direction_id",
        "block_id": "block_id",
        "geometry": "shape",
        "wheelchair_accessible": "wheelchair_accessible",
        "vehicle_journey_code": "vehicle_journey_code",
    }

    upsert(db, Trip, trips, ["id"], mapping)
    print(f"Imported {len(trips)} trips.")


def import_stop_times(db: Session, stop_times: pd.DataFrame):
    print(f"Importing {len(stop_times)} stop times...")

    def parse_gtfs_time(time_str):
        """
        Parse a GTFS time string (which may be >24:00:00) into a string or timedelta.
        Returns None if invalid.
        """
        if pd.isnull(time_str) or time_str == "":
            return None
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                return None
            hours, minutes, seconds = map(int, parts)
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        except Exception:
            return None

    stop_times = stop_times.where(pd.notnull(stop_times), None)
    stop_times["arrival_time"] = stop_times["arrival_time"].apply(parse_gtfs_time)
    stop_times["departure_time"] = stop_times["departure_time"].apply(parse_gtfs_time)

    stop_times["pickup_type"] = stop_times["pickup_type"].map(
        lambda x: PickupDropOffType(x) if not pd.isnull(x) else None
    )
    stop_times["drop_off_type"] = stop_times["drop_off_type"].map(
        lambda x: PickupDropOffType(x) if not pd.isnull(x) else None
    )

    mapping = {
        "trip_id": "trip_id",
        "stop_id": "stop_id",
        "arrival_time": "arrival_time",
        "departure_time": "departure_time",
        "stop_sequence": "stop_sequence",
        "stop_headsign": "stop_headsign",
        "pickup_type": "pickup_type",
        "drop_off_type": "drop_off_type",
        "shape_dist_traveled": "shape_dist_traveled",
        "timepoint": "timepoint",
    }

    rows = stop_times.to_dict(orient="records")
    print(f"Total stop times to import: {len(rows)}")
    print("Removing duplicates...")
    # Remove duplicates within the batch based on (trip_id, stop_id) using DataFrame
    unique_stop_times = stop_times.drop_duplicates(subset=["trip_id", "stop_id"])

    upsert(db, StopTime, unique_stop_times, ["trip_id", "stop_id"], mapping)
    print(f"Imported {len(unique_stop_times)} stop times.")


def import_frequencies(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_frequencies = 0
    print(f"Importing {total_rows} frequencies...")

    for frequencies_df in pd.read_csv(file_path, chunksize=10000):
        frequencies_df = frequencies_df.where(pd.notnull(frequencies_df), None)

        rows = [
            {
                "trip_id": row.get("trip_id"),
                "start_time": row.get("start_time"),
                "end_time": row.get("end_time"),
                "headway_secs": safe_int(row.get("headway_secs")),
                "exact_times": row.get("exact_times"),
            }
            for _, row in frequencies_df.iterrows()
        ]

        rows = [row for row in rows if row["trip_id"] is not None]

        upsert(db, Frequency, rows, ["trip_id"])
        total_frequencies += len(rows)
        percent = (total_frequencies / total_rows) * 100 if total_rows > 0 else 100
        print(f"Total: {total_frequencies} frequencies. ({percent:.2f}%)")


def import_line_strings(db: Session):
    print("Importing line strings for shapes...")
    shape_ids = db.query(Shape.id).all()
    for shape_id_tuple in shape_ids:
        shape_id = shape_id_tuple[0]
        points = (
            db.query(ShapePoint)
            .filter(ShapePoint.shape_id == shape_id)
            .order_by(ShapePoint.sequence)
            .all()
        )
        coords = [
            getattr(point, "point", None)
            for point in points
            if getattr(point, "point", None) is not None
        ]
        shapely_points = []
        from geoalchemy2.shape import to_shape

        for geom in coords:
            if hasattr(geom, "geom_type"):
                shapely_points.append(geom)
            else:
                shapely_points.append(to_shape(geom))
        linestring = build_line_string(shapely_points)
        if linestring:
            db.query(Shape).filter(Shape.id == shape_id).update({"line": linestring})
    db.commit()


def import_gtfs(zip_file_path: str):
    print("Starting GTFS import...")

    feed = ptg.load_geo_feed("itm_all_gtfs.zip")

    if not feed:
        print("No GTFS feed found or feed is empty.")
        return

    print(
        f"GTFS feed contains {len(feed.agency)} agencies, {len(feed.routes)} routes, and {len(feed.trips)} trips."
    )

    routes = {}

    with SessionLocal() as db:
        try:
            import_feed_info(db, feed.feed_info)

            import_agencies(db, feed.agency)

            import_routes(db, feed.routes)

            existing_service_ids = {service.id for service in db.query(Service).all()}
            service_ids = set(feed.trips.service_id)
            new_services = service_ids - existing_service_ids
            print(f"Inserting {len(new_services)} new services...")
            new_services_models = []
            for service_id in new_services:
                new_services_models.append(Service(id=service_id))

            if new_services_models:
                db.bulk_save_objects(new_services_models)
                db.commit()

            services_check = db.query(Service).all()
            print(f"Total services in DB: {len(services_check)}")

            import_trips(db, feed.trips, feed.shapes)

            import_frequencies(db, "gtfs_data/frequencies.txt")

            import_calendar(db, "gtfs_data/calendar.txt")

            import_calendar_dates(db, "gtfs_data/calendar_dates.txt")

            import_stops(db, feed)

            import_stop_times(db, feed)

            db.commit()
            print("GTFS import completed successfully.")

        except Exception as e:
            print("An error occurred during GTFS import:")
            error_str = e.__str__()
            print(error_str[:1000])
            db.rollback()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_gtfs.py <path_to_gtfs_zip> [--test]")
        sys.exit(1)
    test_mode = "--test" in sys.argv[2:]
    gtfs_path = ""
    if not test_mode:
        gtfs_path = sys.argv[1]

    import_gtfs(gtfs_path)
    print("done.")
