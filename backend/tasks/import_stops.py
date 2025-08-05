import math
import naptan  # keep for later
import pandas as pd
from shapely.geometry import Point
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session

from backend.core.db import SessionLocal
from backend.models import Stop


def chunked_query(session: Session, model, ids, chunk_size=1000):
    """Query the database in chunks to avoid exceeding parameter limits."""
    for i in range(0, len(ids), chunk_size):
        yield (
            session.query(model)
            .filter(model.id.in_(list(ids)[i : i + chunk_size]))
            .all()
        )


def import_stops(BATCH_SIZE=100):
    print("Starting import of stops...")

    # stops = naptan.get_area_stops([190, 180], status="active")
    # stops = naptan.get_all_stops(status="active")
    # print(f"Fetched {len(stops)} stops from NAPTAN.")

    # stops.to_csv("stops.csv", index=False)

    stops = pd.read_csv("stops.csv")

    stops = stops[stops["Latitude"].notnull() & stops["Longitude"].notnull()]
    stops = stops.where(pd.notnull(stops), None)

    all_stops = []
    stop_ids = set()

    for _, row in stops.iterrows():
        point = from_shape(
            Point(float(row["Longitude"]), float(row["Latitude"])), srid=4326
        )

        stop_type = (
            "train"
            if row["StopType"] == "RSE"
            else "bus"
            if row["StopType"] in ["BCT", "BCS", "BCQ", "BCE", "BCP", "BST"]
            else None
        )

        default_wait_time = row.get("DefaultWaitTime")
        if (
            default_wait_time is not None
            and isinstance(default_wait_time, float)
            and math.isnan(default_wait_time)
        ):
            default_wait_time = None

        # Ensure revision is an integer
        revision = row.get("RevisionNumber")
        if (
            revision is None
            or not isinstance(revision, (int, float))
            or math.isnan(revision)
        ):
            revision = 0
        else:
            revision = int(revision)

        stop = Stop(
            id=row["ATCOCode"],
            crs=None,
            atco_code=row["ATCOCode"],
            stop_type_name=stop_type,
            stop_type=row["StopType"],
            street=row.get("Street"),
            locality=row.get("LocalityName"),
            name=row.get("ShortCommonName"),
            long_name=row.get("CommonName"),
            lat=float(row["Latitude"]),
            lon=float(row["Longitude"]),
            timing_status=row.get("TimingStatus"),
            default_wait_time=default_wait_time,
            point=point,
            parent_station=row.get("ParentLocality"),
            zone_id=row.get("NaptanCode"),
            indicator=row.get("Indicator") or "",
            bearing=row.get("Bearing"),
            platform=row.get("PlatformCode"),
            revision=revision,
        )
        all_stops.append(stop)
        stop_ids.add(stop.id)

    print(f"Prepared {len(all_stops)} stops out of {len(stops)} to insert or update.")

    with SessionLocal() as db:
        try:
            # Query existing stops in chunks
            existing = []
            for chunk in chunked_query(db, Stop, stop_ids, chunk_size=1000):
                existing.extend(chunk)
            existing_map = {s.id: s for s in existing}

            to_insert = []
            to_update = []

            for stop in all_stops:
                if stop.id in existing_map:
                    existing_stop = existing_map[stop.id]
                    existing_stop.crs = stop.crs
                    existing_stop.atco_code = stop.atco_code
                    existing_stop.stop_type = stop.stop_type
                    existing_stop.street = stop.street
                    existing_stop.locality = stop.locality
                    existing_stop.name = stop.name
                    existing_stop.long_name = stop.long_name
                    existing_stop.lat = stop.lat
                    existing_stop.lon = stop.lon
                    existing_stop.timing_status = stop.timing_status
                    existing_stop.default_wait_time = stop.default_wait_time
                    existing_stop.point = stop.point
                    existing_stop.parent_station = stop.parent_station
                    existing_stop.zone_id = stop.zone_id
                    existing_stop.indicator = stop.indicator
                    existing_stop.bearing = stop.bearing
                    existing_stop.platform = stop.platform
                    existing_stop.revision = stop.revision
                    to_update.append(existing_stop)
                else:
                    to_insert.append(stop)

            total_inserted = 0
            for i in range(0, len(to_insert), BATCH_SIZE):
                batch = to_insert[i : i + BATCH_SIZE]
                db.bulk_save_objects(batch)
                db.commit()
                total_inserted += len(batch)
                print(f"Inserted batch {i // BATCH_SIZE + 1}: {len(batch)} stops")

            total_updated = 0
            for i in range(0, len(to_update), BATCH_SIZE):
                batch = to_update[i : i + BATCH_SIZE]
                stop_columns = {col.name for col in Stop.__table__.columns}
                mappings = []
                for s in batch:
                    db_obj = existing_map[s.id]
                    # Only include if any field has changed
                    changed = any(
                        getattr(db_obj, k) != getattr(s, k)
                        for k in stop_columns
                        if hasattr(s, k)
                    )
                    if changed:
                        mappings.append(
                            {k: v for k, v in s.__dict__.items() if k in stop_columns}
                        )
                if mappings:
                    db.bulk_update_mappings(Stop.__mapper__, mappings)
                    db.commit()
                    total_updated += len(mappings)
                    print(f"Updated batch {i // BATCH_SIZE + 1}: {len(mappings)} stops")

            print(
                f"Inserted {total_inserted}, updated {total_updated} stops successfully."
            )
        except Exception as e:
            db.rollback()
            print(f"Error during batch processing: {e}")


if __name__ == "__main__":
    import_stops(1000)
