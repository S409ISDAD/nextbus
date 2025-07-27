import asyncio
import datetime
import math
from datetime import datetime as dt
from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import get_redis, limiter
from backend.services import bus, stops

router = APIRouter()


log = logging.getLogger(__name__)


@router.get("/scheduled")
@limiter.limit("20/minute")
async def departures_scheduled(
    request: Request, stop_id: str, redis=Depends(get_redis)
):
    try:
        times = await stops.get_times(stop_id, redis)

        tasks = []
        for _time in times:
            tasks.append(bus.build_scheduled(_time, redis))

        buses = await asyncio.gather(*tasks)
        buses = [bus for bus in buses if bus is not None]

        uk_timezone = datetime.timezone(timedelta(hours=1))
        current_time = math.floor(
            dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
        )
        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/live")
@limiter.limit("10/minute")
async def departures_live(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        services = await stops.get_services_from_stop(stop_id, redis)

        service_ids = [service.get("id") for service in services]

        buses = await bus.fetch_buses_live(service_ids, stop_id, redis)

        uk_timezone = datetime.timezone(timedelta(hours=1))
        current_time = math.floor(
            dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
        )
        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/")
@limiter.limit("20/minute")
async def departures(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        services = await stops.get_services_from_stop(stop_id, redis)

        service_ids = [service.get("id") for service in services]

        times = await stops.get_times(stop_id, redis)

        buses = await bus.fetch_buses(service_ids, stop_id, times, redis)

        uk_timezone = datetime.timezone(timedelta(hours=1))
        current_time = math.floor(
            dt.now(datetime.timezone.utc).astimezone(uk_timezone).timestamp()
        )
        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
