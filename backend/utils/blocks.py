import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.config import get_logger, setup_logging
from backend.deps import LONDON
from backend.models import Journey, journey_is_valid_filter
from backend.services.bus import fetch_bus_trip
from backend.deps import get_redis
from sqlalchemy.orm import aliased

log = get_logger(__name__)


def find_bus_on_block(
    db: Session,
    block_id: Optional[str] = None,
    journey_id: Optional[int] = None,
    today: Optional[datetime] = None,
):
    ThisJourney = aliased(Journey)

    if today is None:
        today = datetime.now(tz=LONDON)

    journeys_on_block = (
        db.query(Journey)
        .filter(
            journey_is_valid_filter(today.date()),
        )
        .join(Journey.calendar)
        .order_by(Journey.start_time)
    )

    if journey_id is not None:
        journeys_on_block = journeys_on_block.filter(
            Journey.start_time <= ThisJourney.start_time,
            Journey.block_id == ThisJourney.block_id,
        ).join(ThisJourney, ThisJourney.id == journey_id)

    elif block_id is not None:
        journeys_on_block = journeys_on_block.filter(Journey.block_id == block_id)

    else:
        raise ValueError("Either block_id or journey_id must be provided")

    journeys_on_block = journeys_on_block.all()

    for journey in journeys_on_block:
        print(
            f"Journey ID: {journey.id}, {journey.start_time} -> {journey.end_time} | {journey.service.line_name} to {journey.headsign}"
        )

    reversed_journeys = list(reversed(journeys_on_block))

    r = get_redis()

    away = 0

    for journey in reversed_journeys:
        trip_id = journey.get_bt_trip_id(db)
        service_id = journey.service.get_bt_service_id(db)
        print(
            f"Fetching trip for Journey ID: {journey.id} (Trip ID: {trip_id}, Service ID: {service_id})"
        )
        bus = fetch_bus_trip(service_id, trip_id, r)
        if bus is not None:
            log.debug(
                f"Found bus for journey {journey.id}, block {block_id}: {bus.get('vehicle').get('name')}"
            )
            return bus, away
        away += 1

    return None, None


if __name__ == "__main__":
    setup_logging()
    from backend.db.db import SessionLocal

    with SessionLocal() as db:
        asyncio.run(find_bus_on_block(db, "WI30"))
