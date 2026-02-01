from datetime import datetime
from sqlalchemy import func, or_
from backend.models import Journey, Service, journey_is_valid_filter
from sqlalchemy.orm import Session
from backend.services.journeys import get_trip
from backend.services.services import get_service_info

from backend.deps import LONDON, get_logger

log = get_logger(__name__)


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


def match_service(db: Session, service_id: int, r) -> Service | None:
    # try to find a matching Line in our DB for this service_id
    db_service = db.query(Service).filter(Service.bt_service_id == service_id).first()
    if db_service:
        return db_service

    # if no match by bt_service_id, try to match with other parameters
    service = get_service_info(service_id, r)

    if service:
        db_service = fuzzy_search_service(
            f"{service.line_name} {service.description} {service.detail}", db, limit=10
        )  # attempt a fuzzy search of the key attributes

        if db_service:
            # further refine the top result just to make sure
            db_service = db_service[0]
            line_ids = db_service.line_names.split(", ")
            log.debug(db_service.service_code)
            db_service = (
                db.query(Service)
                .filter(Service.service_code == db_service.service_code)
                .filter(Service.line_name.in_(line_ids))
                .first()
            )

        # save the ID for future lookups
        if db_service:
            log.debug(
                f"Matched service {service_id} to db {db_service.id} via fuzzy search"
            )
            db_service.bt_service_id = service_id
            db.commit()
            return db_service
    return None


def match_trip_journey(db: Session, trip_id: int, r) -> Journey | None:
    # try to find a matching journey in our DB for this trip_id
    if not trip_id:
        return None
    journey = db.query(Journey).filter(Journey.bt_trip_id == trip_id).first()
    if journey:
        return journey

    # if no match by bt_service_id, try to match with other parameters
    trip = get_trip(trip_id, 0, r)

    today = datetime.now(tz=LONDON).date()

    if trip:
        query = (
            db.query(Journey)
            .join(Journey.service)
            .join(Journey.calendar)
            .filter(Journey.vehicle_journey_code == trip.vehicle_journey_code)
            .filter(Journey.ticket_machine_code == str(trip.ticket_machine_code))
            .filter(Service.line_name == trip.route_name)
            .filter(journey_is_valid_filter(today))
        )  # find journey with matching attributes, as well as being valid today

        if trip.block is not None:
            # add block ID if present to narrow down search
            query = query.filter(Journey.block_id == trip.block)

        if len(query.all()) > 1:
            # this rarely happens, normally when there is an error in the data that produces 2 journeys
            log.warning(
                f"Multiple journeys found for trip {trip_id} and vjc {trip.vehicle_journey_code} and tmc {trip.ticket_machine_code}"
            )

        journey = query.first()
        if journey:
            # save ID for future lookups
            log.debug(f"Matched trip {trip_id} to journey {journey.id}")
            journey.bt_trip_id = trip_id
            db.commit()
            return journey
    return None
