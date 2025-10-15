from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import get_redis, limiter
from backend.schemas.trains import TrainService, StationResponse
from backend.services.trains import (
    get_departures,
    get_arrivals,
    get_detailed_route_trains,
    get_service,
)
from enum import Enum
from backend.deps import get_logger

router = APIRouter()

log = get_logger(__name__)


class TrainDataType(str, Enum):
    departures = "departures"
    arrivals = "arrivals"


@router.get("/station/{station_code}", response_model=StationResponse)
@limiter.limit("45/minute")
async def train_departures(
    request: Request,
    station_code: str,
    type: TrainDataType = TrainDataType.departures,
    redis=Depends(get_redis),
):
    try:
        if type == TrainDataType.departures:
            trains = await get_departures(station_code, redis)
        elif type == TrainDataType.arrivals:
            trains = await get_arrivals(station_code, redis)
        return trains
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/{from_station}/to/{to_station}", response_model=list[TrainService])
@limiter.limit("45/minute")
async def train_route(
    request: Request,
    from_station: str,
    to_station: str,
    redis=Depends(get_redis),
):
    try:
        trains = await get_detailed_route_trains(from_station, to_station, redis)
        return trains
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/service/{service_id}", response_model=TrainService)
@limiter.limit("45/minute")
async def train_details(
    request: Request,
    service_id: str,
    redis=Depends(get_redis),
):
    try:
        trains = await get_service(service_id, redis)
        return trains
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
