from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from backend.schemas.bus import TrackedBus
from backend.services import bus
from backend.deps import get_redis

from backend.deps import get_logger
from backend.deps import limiter

router = APIRouter()


log = get_logger(__name__)


@router.get("/", response_model=Optional[TrackedBus])
@limiter.limit("30/minute")
async def get_bus(request: Request, bus_id: int, redis=Depends(get_redis)):
    try:
        this_bus = await bus.build_bus(bus_id, redis)

        return this_bus
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
