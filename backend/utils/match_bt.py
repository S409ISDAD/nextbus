from sqlalchemy import func, or_
from backend.models import Journey, Line, Service
from sqlalchemy.orm import Session
from backend.services.journeys import get_trip
from backend.services.services import get_service_info


def fuzzy_search_service(query, db, limit=10, threshold=0.2):
    return (
        db.query(Service)
        .filter(
            or_(
                func.similarity(Service.description, query) > threshold,
                func.similarity(Service.line_names, query) > threshold,
            )
        )
        .order_by(
            func.greatest(
                func.similarity(Service.description, query),
                func.similarity(Service.line_names, query),
            ).desc()
        )
        .limit(limit)
        .all()
    )


async def match_service_line(db: Session, service_id: int, r) -> Line | None:
    # try to find a matching Line in our DB for this service_id
    line = db.query(Line).filter(Line.bt_service_id == service_id).first()
    if line:
        return line

    # if no match by bt_service_id, try to match with other parameters
    service = await get_service_info(service_id, r)

    if service:
        db_service = fuzzy_search_service(
            f"{service.line_name} {service.description} {service.detail}", db, limit=10
        )

        if db_service:
            db_service = db_service[0]
            line_ids = db_service.line_names.split(", ")
            print(db_service.service_code)
            line = (
                db.query(Line)
                .filter(Line.service_code == db_service.service_code)
                .filter(Line.line_name.in_(line_ids))
                .first()
            )
        if line:
            print(
                f"Matched service {service_id} to line {line.line_name} via fuzzy search"
            )
            line.bt_service_id = service_id
            db.commit()
            return line
    return None


async def match_trip_journey(db: Session, trip_id: int, r) -> Journey | None:
    # try to find a matching Line in our DB for this service_id
    journey = db.query(Journey).filter(Journey.bt_trip_id == trip_id).first()
    if journey:
        return journey

    # if no match by bt_service_id, try to match with other parameters
    trip = await get_trip(trip_id, 0, r)

    if trip:
        query = (
            db.query(Journey)
            .filter(Journey.vehicle_journey_code == trip.vehicle_journey_code)
            .filter(Journey.ticket_machine_code == str(trip.ticket_machine_code))
        )
        if trip.block is not None:
            query = query.filter(Journey.block_id == trip.block)
        journey = query.first()
        if journey:
            print(f"Matched trip {trip_id} to journey {journey.id}")
            journey.bt_trip_id = trip_id
            db.commit()
            return journey
    return None
