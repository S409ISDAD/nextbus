import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import get_redis, limiter
from backend.models.trains import TrainResponse
from backend.services.trains import get_departures, get_arrivals
from enum import Enum

router = APIRouter()

log = logging.getLogger(__name__)


class TrainDataType(str, Enum):
    departures = "departures"
    arrivals = "arrivals"


@router.get("/", response_model=TrainResponse)
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
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
