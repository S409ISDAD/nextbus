from pathlib import Path
import zipfile
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
    ContinuousPickupDropOff,
    ExceptionType,
    WheelchairAccessible,
    BikesAllowed,
    PickupDropOffType,
)
from sqlalchemy.orm import Session
import sys
from datetime import timedelta


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
    db: Session, model, rows: list[dict], conflict_columns: list, batch_size: int = 5000
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
        if not rows:
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

        filtered_rows = []
        for row in rows:
            instance = model(**row)
            needs = needs_update(db, model, instance)
            if needs:  # Only upsert if new or changed
                filtered_rows.append(row)

        for i in range(0, len(filtered_rows), batch_size):
            batch = filtered_rows[i : i + batch_size]
            if not batch:
                continue
            stmt = pg_insert(model).values(batch)
            if (
                update_columns
            ):  # Only add on_conflict_do_update if there are columns to update
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


def import_feed_info(db: Session, file_path: str):
    print("Importing feed info...")
    for feed_info_df in pd.read_csv(file_path, chunksize=1000):
        feed_info_df = feed_info_df.where(pd.notnull(feed_info_df), None)

        if "feed_start_date" in feed_info_df.columns:
            feed_info_df["feed_start_date"] = pd.to_datetime(
                feed_info_df["feed_start_date"], format="%Y%m%d", errors="coerce"
            )
        if "feed_end_date" in feed_info_df.columns:
            feed_info_df["feed_end_date"] = pd.to_datetime(
                feed_info_df["feed_end_date"], format="%Y%m%d", errors="coerce"
            )

        # Ensure column names match the FeedInfo model
        rows = [
            {
                "publisher_name": row.get("feed_publisher_name"),
                "publisher_url": row.get("feed_publisher_url"),
                "lang": row.get("feed_lang"),
                "default_lang": row.get("default_lang"),
                "start_date": row.get("feed_start_date"),
                "end_date": row.get("feed_end_date"),
                "version": row.get("feed_version"),
                "contact_email": row.get("feed_contact_email"),
                "contact_url": row.get("feed_contact_url"),
            }
            for _, row in feed_info_df.iterrows()
        ]

        # Ensure primary key is not null
        rows = [row for row in rows if row["publisher_name"] is not None]

        upsert(db, FeedInfo, rows, ["publisher_name"])
        print(f"Imported {len(rows)} feed info entries.")


def import_agencies(db: Session, file_path: str):
    print("Importing agencies...")
    for agencies_df in pd.read_csv(file_path, chunksize=1000):
        agencies_df = agencies_df.where(pd.notnull(agencies_df), None)

        rows = [
            {
                "id": row.get("agency_id"),
                "name": row.get("agency_name"),
                "url": row.get("agency_url"),
                "timezone": row.get("agency_timezone"),
                "lang": row.get("agency_lang"),
                "phone": row.get("agency_phone"),
                "fare_url": row.get("agency_fare_url"),
                "email": row.get("agency_email"),
            }
            for _, row in agencies_df.iterrows()
        ]

        rows = [row for row in rows if row["id"] is not None]

        upsert(db, Agency, rows, ["id"])
        print(f"Imported {len(rows)} agencies.")


def import_routes(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_route_entries = 0
    print(f"Importing {total_rows} route entries...")

    for routes_df in pd.read_csv(file_path, chunksize=10000):
        routes_df = routes_df.where(pd.notnull(routes_df), None)

        rows = []
        for _, row in routes_df.iterrows():
            try:
                route_type = row.get("route_type")
                if pd.isnull(route_type):
                    continue
                if route_type == "200":
                    route_type = 2
                route_type_enum = RouteType(route_type)
            except (ValueError, TypeError):
                print(
                    f"Invalid route type {row.get('route_type')} for {row.get('route_id')} skipping."
                )
                continue

            rows.append(
                {
                    "id": row.get("route_id"),
                    "agency_id": row.get("agency_id"),
                    "short_name": row.get("route_short_name"),
                    "long_name": row.get("route_long_name")
                    if not pd.isnull(row.get("route_long_name"))
                    else "",
                    "desc": row.get("route_desc"),
                    "type": route_type_enum,
                    "url": row.get("route_url"),
                    "color": row.get("route_color"),
                    "text_color": row.get("route_text_color"),
                    "sort_order": safe_int(row.get("route_sort_order")),
                    "continuous_pickup": ContinuousPickupDropOff(
                        row.get("route_continuous_pickup")
                    )
                    if not pd.isnull(row.get("route_continuous_pickup"))
                    else None,
                    "continuous_drop_off": ContinuousPickupDropOff(
                        row.get("route_continuous_drop_off")
                    )
                    if not pd.isnull(row.get("route_continuous_drop_off"))
                    else None,
                }
            )

        rows = [row for row in rows if row["id"] is not None]

        total_route_entries += len(rows)

        upsert(db, Route, rows, ["id"])
        percent = (total_route_entries / total_rows) * 100 if total_rows > 0 else 100
        print(f"Imported {total_route_entries} routes. ({percent:.2f}%)")


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


def import_shapes(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_shapes = 0
    total_shape_points = 0
    print(f"Importing {total_rows} shape points...")

    shape_ids = set()

    for shapes_df in pd.read_csv(file_path, chunksize=10000):
        shapes_df = shapes_df.where(pd.notnull(shapes_df), None)

        chunk_shape_ids = set(shapes_df["shape_id"].dropna().unique())
        new_shape_ids = chunk_shape_ids - shape_ids
        shape_ids.update(new_shape_ids)

        shape_rows = [{"id": shape_id} for shape_id in new_shape_ids]
        if shape_rows:
            upsert(db, Shape, shape_rows, ["id"])
            total_shapes += len(shape_rows)

        rows = [
            {
                "shape_id": row.get("shape_id"),
                "point": generate_point(
                    float(row["shape_pt_lat"]), float(row["shape_pt_lon"])
                ),
                "sequence": safe_int(row.get("shape_pt_sequence")),
                "distance_traveled": safe_float(row.get("shape_dist_traveled")),
            }
            for _, row in shapes_df.iterrows()
        ]
        rows = [row for row in rows if row["shape_id"] is not None]

        upsert(db, ShapePoint, rows, ["shape_id", "sequence"])
        total_shape_points += len(rows)
        percent = (total_shape_points / total_rows) * 100 if total_rows > 0 else 100
        print(
            f"Imported {total_shapes} shapes and {total_shape_points} shape points. ({percent:.2f}%)"
        )


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


def import_trips(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_trips = 0
    print(f"Importing {total_rows} trips...")

    for trips_df in pd.read_csv(file_path, chunksize=10000):
        trips_df = trips_df.where(pd.notnull(trips_df), None)

        all_service_ids = {service.id for service in db.query(Service).all()}
        service_ids = set(trips_df["service_id"].dropna().unique())
        new_service_ids = service_ids - all_service_ids

        service_rows = [{"id": service_id} for service_id in new_service_ids]
        if service_rows:
            print(f"Upserting {len(service_rows)} new services.")
            upsert(db, Service, service_rows, ["id"])

        rows = [
            {
                "id": row.get("trip_id"),
                "route_id": row.get("route_id"),
                "service_id": row.get("service_id"),
                "headsign": row.get("trip_headsign"),
                "direction": row.get("direction_id"),
                "block_id": row.get("block_id"),
                "shape_id": None
                if pd.isna(row.get("shape_id"))
                else row.get("shape_id"),
                "wheelchair_accessible": WheelchairAccessible(
                    row.get("wheelchair_accessible")
                )
                if not pd.isna(row.get("wheelchair_accessible"))
                else None,
                "bikes_allowed": BikesAllowed(row.get("bikes_allowed"))
                if not pd.isna(row.get("bikes_allowed"))
                else None,
                "vehicle_journey_code": row.get("vehicle_journey_code"),
            }
            for _, row in trips_df.iterrows()
        ]

        rows = [row for row in rows if row["id"] is not None]

        upsert(db, Trip, rows, ["id"])
        total_trips += len(rows)
        percent = (total_trips / total_rows) * 100 if total_rows > 0 else 100
        print(f"Total: {total_trips} trips. ({percent:.2f}%)")


def import_stop_times(db: Session, file_path: str):
    total_rows = sum(1 for _ in open(file_path)) - 1  # subtract header
    total_stop_times = 0
    print(f"Importing {total_rows} stop times...")

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

    for stop_times_df in pd.read_csv(file_path, chunksize=10000):
        stop_times_df = stop_times_df.where(pd.notnull(stop_times_df), None)
        stop_times_df["arrival_time"] = stop_times_df["arrival_time"].apply(
            parse_gtfs_time
        )
        stop_times_df["departure_time"] = stop_times_df["departure_time"].apply(
            parse_gtfs_time
        )

        rows = [
            {
                "trip_id": row.get("trip_id"),
                "stop_id": row.get("stop_id"),
                "arrival_time": row.get("arrival_time"),
                "departure_time": row.get("departure_time"),
                "stop_sequence": row.get("stop_sequence"),
                "stop_headsign": row.get("stop_headsign"),
                "pickup_type": PickupDropOffType(row.get("pickup_type"))
                if not pd.isnull(row.get("pickup_type"))
                else None,
                "drop_off_type": PickupDropOffType(row.get("drop_off_type"))
                if not pd.isnull(row.get("drop_off_type"))
                else None,
                "continuous_pickup": ContinuousPickupDropOff(
                    row.get("continuous_pickup")
                )
                if not pd.isnull(row.get("continuous_pickup"))
                else None,
                "continuous_drop_off": ContinuousPickupDropOff(
                    row.get("continuous_drop_off")
                )
                if not pd.isnull(row.get("continuous_drop_off"))
                else None,
                "shape_dist_traveled": row.get("shape_dist_traveled"),
                "timepoint": row.get("timepoint"),
            }
            for _, row in stop_times_df.iterrows()
        ]

        rows = [
            row
            for row in rows
            if row["trip_id"] is not None and row["stop_id"] is not None
        ]

        # Remove duplicates within the batch based on (trip_id, stop_id)
        seen = set()
        unique_rows = []
        for row in rows:
            key = (row["trip_id"], row["stop_id"])
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)

        upsert(db, StopTime, unique_rows, ["trip_id", "stop_id"])

        total_stop_times += len(rows)
        percent = (total_stop_times / total_rows) * 100 if total_rows > 0 else 100
        print(f"Total: {total_stop_times} stop times. ({percent:.2f}%)")


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


def import_gtfs(zip_file_path: str, test=False):
    print("Starting GTFS import...")

    if test:
        print("Running in test mode.")

    else:
        file_path = Path(zip_file_path).resolve()

        if not file_path.exists():
            print(f"File {zip_file_path} does not exist.")
            return
        print(f"Extracting GTFS data from {file_path}...")
        with zipfile.ZipFile(zip_file_path, "r") as zf:
            zf.extractall(path="gtfs_data")
            print("Extracted GTFS files to gtfs_data directory.")

    with SessionLocal() as db:
        try:
            feed_ver = db.query(FeedInfo.version).first()
            feed_info_df = pd.read_csv("gtfs_data/feed_info.txt")
            if feed_ver == feed_info_df.get("feed_version", [None])[0]:
                print("Feed info version matches, skipping import.")
            else:
                print("Feed info version differs, importing GTFS data...")
                import_feed_info(db, "gtfs_data/feed_info.txt")

                import_agencies(db, "gtfs_data/agency.txt")

                import_routes(db, "gtfs_data/routes.txt")

                import_shapes(db, "gtfs_data/shapes.txt")

                import_line_strings(db)

                import_trips(db, "gtfs_data/trips.txt")

                import_frequencies(db, "gtfs_data/frequencies.txt")

                import_calendar(db, "gtfs_data/calendar.txt")

                import_calendar_dates(db, "gtfs_data/calendar_dates.txt")

                import_stops(db, "gtfs_data/stops.txt")

                import_stop_times(db, "gtfs_data/stop_times.txt")

                db.commit()
                print("GTFS import completed successfully.")

        except Exception as e:
            import traceback

            print("An error occurred during GTFS import:")
            error_str = e.__str__()
            print(error_str[:1000])
            db.rollback()

        finally:
            if not test:
                import shutil

                gtfs_data_path = Path("gtfs_data")
                try:
                    if gtfs_data_path.exists() and gtfs_data_path.is_dir():
                        shutil.rmtree(gtfs_data_path)
                        print("Attempted to clean up extracted GTFS files.")
                    else:
                        print("gtfs_data directory does not exist, skipping cleanup.")
                except Exception as e:
                    print(
                        f"Error cleaning up gtfs_data: {e}. Some files or directories may not have been deleted."
                    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_gtfs.py <path_to_gtfs_zip> [--test]")
        sys.exit(1)
    test_mode = "--test" in sys.argv[2:]
    gtfs_path = ""
    if not test_mode:
        gtfs_path = sys.argv[1]
    import_gtfs(gtfs_path, test=test_mode)
    print("done.")
