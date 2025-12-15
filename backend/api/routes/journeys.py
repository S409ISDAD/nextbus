from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from backend.db.db import get_db
from backend.schemas.journey import Trip
from backend.models import Journey, StopTime, Stop, Service
from backend.schemas.stop import StopTime as StopTimeSchema
from backend.services import journeys
from backend.services.bus import build_bus
from backend.deps import LONDON, get_redis
from sqlalchemy.orm import selectinload, load_only

from backend.deps import limiter
from backend.deps import get_logger
from backend.utils import blocks
from backend.utils.route_dist import compute_distance

router = APIRouter()


log = get_logger(__name__)


@router.get("/trip/{trip_id}", response_model=Optional[Trip])
@limiter.limit("30/minute")
def get_trip(request: Request, trip_id: int, redis=Depends(get_redis)):
    try:
        trip = journeys.get_trip(trip_id, 0, redis)

        return trip
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/distance", response_model=dict)
@limiter.limit("20/minute")
def get_distance(
    request: Request,
    trip_id: int,
    atco_on: str,
    atco_off: str,
    redis=Depends(get_redis),
):
    try:
        distance = compute_distance(atco_on, atco_off, trip_id, redis)

        return {"distance_meters": distance}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/dbjourney/{journey_id}", response_model=Optional[Trip])
@limiter.limit("30/minute")
def get_db_journey(
    request: Request, journey_id: int, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        service_date = datetime.now(LONDON).date()

        db_journey = (
            db.query(Journey)
            .filter(Journey.id == journey_id)
            .options(
                selectinload(Journey.stop_times).options(
                    load_only(StopTime.id, StopTime.stop_id, StopTime.stop_sequence),
                    selectinload(StopTime.stop).options(load_only(Stop.atco_code)),
                ),
                selectinload(Journey.service).options(load_only(Service.line_name)),
            )
            .first()
        )

        if not db_journey:
            raise HTTPException(404, detail="Journey not found")

        track = db_journey.get_track(db)

        stops = []

        for stoptime in sorted(db_journey.stop_times, key=lambda st: st.stop_sequence):
            departure = stoptime.departure_datetime(service_date).isoformat()
            stoptime_obj = StopTimeSchema(
                stop_id=stoptime.stop_id,
                name=stoptime.stop.name if stoptime.stop else "Unknown",
                aimed_time=departure,
                expt_time=departure,
                coords=stoptime.stop.location if stoptime.stop else [0.0, 0.0],
                track=track.get(stoptime.stop_id, []),
                set_down=stoptime.drop_off,
                pick_up=stoptime.pick_up,
                timing_status=stoptime.timing_status,
            )
            stops.append(stoptime_obj)

        trip = Trip(
            vehicle_journey_code=db_journey.vehicle_journey_code,
            ticket_machine_code=db_journey.ticket_machine_code,
            route_name=db_journey.service.line_name,
            destination=db_journey.headsign,
            block=db_journey.block_id,
            service_id=0,
            stops=stops,
        )

        return trip

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/dbjourney/{journey_id}/whatbus", response_model=dict)
@limiter.limit("20/minute")
def get_bus_on_prev_journey(
    request: Request, journey_id: int, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        bus, away = blocks.find_bus_on_block(
            db,
            journey_id=journey_id,
        )

        if bus is None:
            raise HTTPException(404, detail="No bus found on previous journey")

        bus_id = bus.get("id")
        bus_data = build_bus(bus_id, redis, get_journey=False)

        return {
            "away": away,
            "bus": bus_data,
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
