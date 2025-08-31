from backend.models import Journey, JourneyTripMatch, Line, LineServiceMatch
from sqlalchemy.orm import Session
from backend.utils.fetch_json import fetch_json
from backend.config import API_BASE


async def match_journey_trip(db: Session, journey_id: str, r) -> int | None:
    """Match a db journey to a bustimes trip"""

    trip_id = (
        db.query(JourneyTripMatch.trip_id)
        .filter(JourneyTripMatch.journey_id == journey_id)
        .first()
    )
    if trip_id:
        return trip_id[0]

    db_journey: Journey = db.query(Journey).filter(Journey.id == journey_id).first()

    if not db_journey:
        return None

    vjc = db_journey.vehicle_journey_code
    tmc = db_journey.ticket_machine_code
    block = db_journey.block_id

    results = await fetch_json(
        f"{API_BASE}/trips/?vehicle_journey_code={vjc}&ticket_machine_code={tmc}&block={block or ''}"
    )

    if not results or "results" not in results:
        return None

    bt_trip = results["results"]

    if len(bt_trip) != 1:
        return None

    trip_id = bt_trip[0]["id"]

    match = JourneyTripMatch(journey_id=journey_id, trip_id=trip_id)
    db.add(match)
    db.commit()

    return trip_id


async def match_line_service(db: Session, line_id: str) -> int | None:
    """Match a db line to a bustimes service"""

    service_id = (
        db.query(LineServiceMatch.service_id)
        .filter(LineServiceMatch.line_id == line_id)
        .first()
    )
    if service_id:
        return service_id[0]

    db_line: Line = db.query(Line).filter(Line.id == line_id).first()

    if not db_line:
        return None

    noc = db_line.service.operator_noc or ""
    line_name = db_line.line_name
    origin = db_line.service.origin
    destination = db_line.service.destination

    results = await fetch_json(
        f"{API_BASE}/services/?operator={noc}&search={' '.join([str(line_name), str(origin), str(destination)])}"
    )

    if not results or "results" not in results:
        return None

    bt_service = results["results"]

    if len(bt_service) != 1:
        return None

    service_id = bt_service[0]["id"]

    match = LineServiceMatch(line_id=line_id, service_id=service_id)
    db.add(match)
    db.commit()

    return service_id
