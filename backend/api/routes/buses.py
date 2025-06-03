from typing import Optional
from fastapi import APIRouter, Depends
from backend.models.trackedbus import TrackedBus
from backend.services import bus
from backend.deps import get_redis

router = APIRouter()


@router.get("/", response_model=Optional[TrackedBus])
async def get_bus(bus_id: int, redis=Depends(get_redis)):
    this_bus = await bus.build_bus(bus_id, None, redis)

    return this_bus
