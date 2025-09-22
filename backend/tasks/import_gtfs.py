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
    Calendar,
    CalendarDate,
    Service,
    Shape,
    Trip,
    StopTime,
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
    batch_size: int = 10000,
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
                    log.debug(f"Upserting batch {counter // batch_size} ({percent:.2f}%)")
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
            log.debug(f"Upserting final batch ({percent:.2f}%)")
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
    log.debug("Importing feed info...")
    if feed_info is None or feed_info.empty:
        log.debug("No feed info available in GTFS feed.")
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
    log.debug(f"Imported {len(feed_info)} feed info entries.")


def import_agencies(db: Session, agencies: pd.DataFrame):
    log.debug("Importing agencies...")
    if agencies is None or agencies.empty:
        log.debug("No agencies available in GTFS feed.")
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
    log.debug(f"Imported {len(agencies)} agencies.")


def import_routes(db: Session, routes: pd.DataFrame):
    log.debug("Importing routes...")
    if routes is None or routes.empty:
        log.debug("No routes available in GTFS feed.")
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
    log.debug(f"Imported {len(routes)} routes.")


def import_calendar(db: Session, calendar_df: pd.DataFrame):
    log.debug(f"Importing {len(calendar_df)} calendar entries...")

    calendar_df = calendar_df.where(pd.notnull(calendar_df), None)
    calendar_df["start_date"] = pd.to_datetime(
        calendar_df["start_date"], format="%Y%m%d"
    )
    calendar_df["end_date"] = pd.to_datetime(calendar_df["end_date"], format="%Y%m%d")

    mapping = {
        "service_id": "service_id",
        "monday": "monday",
        "tuesday": "tuesday",
        "wednesday": "wednesday",
        "thursday": "thursday",
        "friday": "friday",
        "saturday": "saturday",
        "sunday": "sunday",
        "start_date": "start_date",
        "end_date": "end_date",
    }

    upsert(db, Calendar, calendar_df, ["service_id"], mapping)
    log.debug(f"Imported {len(calendar_df)} calendar entries.")


def import_calendar_dates(db: Session, calendar_dates_df: pd.DataFrame):
    log.debug(f"Importing {len(calendar_dates_df)} calendar dates...")

    calendar_dates_df = calendar_dates_df.where(pd.notnull(calendar_dates_df), None)
    calendar_dates_df["date"] = pd.to_datetime(
        calendar_dates_df["date"], format="%Y%m%d"
    )
    calendar_dates_df["exception_type"] = calendar_dates_df["exception_type"].map(
        ExceptionType
    )

    mapping = {
        "service_id": "service_id",
        "date": "date",
        "exception_type": "exception_type",
    }

    upsert(db, CalendarDate, calendar_dates_df, ["service_id", "date"], mapping)
    log.debug(f"Imported {len(calendar_dates_df)} calendar date entries.")


def import_shapes(db: Session, shapes: pd.DataFrame):
    log.debug(f"Importing {len(shapes)} shapes...")

    shapes = shapes.where(pd.notnull(shapes), None)

    mapping = {
        "id": "shape_id",
        "geometry": "geometry",
    }

    upsert(db, Shape, shapes, ["shape_id"], mapping)
    log.debug(f"Imported {len(shapes)} shapes.")


def import_trips(db: Session, trips: pd.DataFrame, shapes: pd.DataFrame):
    log.debug(f"Importing {len(trips)} trips...")

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
    log.debug(f"Imported {len(trips)} trips.")


def import_stop_times(db: Session, stop_times: pd.DataFrame):
    log.debug(f"Importing {len(stop_times)} stop times...")

    stop_times = stop_times.where(pd.notnull(stop_times), None)

    stop_times["pickup_type"] = stop_times["pickup_type"].map(
        lambda x: PickupDropOffType(int(x)) if not pd.isnull(x) else None
    )
    stop_times["drop_off_type"] = stop_times["drop_off_type"].map(
        lambda x: PickupDropOffType(int(x)) if not pd.isnull(x) else None
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

    log.debug("Removing duplicates...")
    # Remove duplicates within the batch based on (trip_id, stop_id) using DataFrame
    unique_stop_times = stop_times.drop_duplicates(subset=["trip_id", "stop_id"])
    log.debug(f"Total stop times to import: {len(stop_times)}")

    upsert(db, StopTime, unique_stop_times, ["trip_id", "stop_id"], mapping)
    log.debug(f"Imported {len(unique_stop_times)} stop times.")


def import_frequencies(db: Session, frequencies_df: pd.DataFrame):
    log.debug(f"Importing {len(frequencies_df)} frequencies...")

    frequencies_df = frequencies_df.where(pd.notnull(frequencies_df), None)

    mapping = {
        "trip_id": "trip_id",
        "start_time": "start_time",
        "end_time": "end_time",
        "headway_secs": "headway_secs",
        "exact_times": "exact_times",
    }

    upsert(db, Frequency, frequencies_df, ["trip_id"], mapping)
    log.debug(f"Imported {len(frequencies_df)} frequencies.")


def import_gtfs(zip_file_path: str):
    log.debug("Starting GTFS import...")

    config = ptg.config.geo_config()
    config.remove_edges_from(list(config.out_edges("stops.txt")))

    feed = ptg.load_feed(zip_file_path, config=config)

    # feed = ptg.load_geo_feed(zip_file_path)

    if not feed:
        log.debug("No GTFS feed found or feed is empty.")
        return

    log.debug(f"GTFS feed loaded from {zip_file_path}")

    # log.debug(
    #     f"GTFS feed contains {len(feed.agency)} agencies, {len(feed.routes)} routes, and {len(feed.trips)} trips."
    # )

    with SessionLocal() as db:
        try:
            import_feed_info(db, feed.feed_info)

            import_agencies(db, feed.agency)

            import_routes(db, feed.routes)

            existing_service_ids = {service.id for service in db.query(Service).all()}
            service_ids = set(feed.trips.service_id)
            new_services = service_ids - existing_service_ids
            log.debug(f"Inserting {len(new_services)} new services...")
            new_services_models = []
            for service_id in new_services:
                new_services_models.append(Service(id=service_id))

            if new_services_models:
                db.bulk_save_objects(new_services_models)
                db.commit()

            services_check = db.query(Service).all()
            log.debug(f"Total services in DB: {len(services_check)}")

            import_trips(db, feed.trips, feed.shapes)

            import_frequencies(db, feed.frequencies)

            import_calendar(db, feed.calendar)

            import_calendar_dates(db, feed.calendar_dates)

            import_stop_times(db, feed.stop_times)

            db.commit()
            log.debug("GTFS import completed successfully.")

        except Exception as e:
            log.debug("An error occurred during GTFS import:")
            error_str = e.__str__()
            log.debug(error_str[:1000])
            # log.debug(error_str)
            db.rollback()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        log.debug("Usage: python import_gtfs.py <path_to_gtfs_zip> [--test]")
        sys.exit(1)
    test_mode = "--test" in sys.argv[2:]
    gtfs_path = ""
    if not test_mode:
        gtfs_path = sys.argv[1]

    import_gtfs(gtfs_path)
    log.debug("done.")
