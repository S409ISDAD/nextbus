from typing import Optional
from fastapi import APIRouter, Depends, Request
from backend.models.bus import TrackedBus
from backend.services import bus
from backend.deps import get_redis

from backend.deps import limiter

router = APIRouter()


@router.get("/", response_model=Optional[TrackedBus])
@limiter.limit("20/minute")
async def get_bus(request: Request, bus_id: int, redis=Depends(get_redis)):
    this_bus = await bus.build_bus(bus_id, redis)

    return this_bus
