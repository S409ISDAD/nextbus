import logging
from datetime import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.db.db import SessionLocal
from backend.deps import get_redis, limiter
from backend.models import Locality
from backend.schemas.location import LocationRequest
from backend.services.journey_planner import (
    possible_destinations,
    get_possible_journeys,
)

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/destinations")
@limiter.limit("20/minute")
async def destinations(
    request: Request,
    body: LocationRequest,
    datetime: dt | None = None,
    redis=Depends(get_redis),
):
    try:
        localities = await possible_destinations(body.lat, body.lon, datetime)
        return localities
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.post("/journeys")
@limiter.limit("10/minute")
async def journeys(
    request: Request,
    body: LocationRequest,
    locality: str,
    datetime: dt | None = None,
    redis=Depends(get_redis),
):
    try:
        journeys = await get_possible_journeys(
            body.lat, body.lon, locality, redis, datetime
        )
        return journeys
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/locality/{id}")
async def locality(request: Request, id: str):
    try:
        with SessionLocal() as db:
            db_locality = db.query(Locality).filter(Locality.id == id).first()

            if db_locality:
                return {"id": id, "name": db_locality.name}
            else:
                raise HTTPException(404, detail=f"Locality not found with id {id}")

    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
