import asyncio
from datetime import datetime as dt
import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import UTC, get_redis, limiter
from backend.services import bus, stops
from backend.tasks.get_departures import get_departures, get_scheduled

router = APIRouter()


log = logging.getLogger(__name__)


@router.get("/scheduled")
@limiter.limit("45/minute")
async def departures_scheduled(
    request: Request, stop_id: str, redis=Depends(get_redis)
):
    try:
        await redis.sadd("total_stops", stop_id)
        times = await get_scheduled(stop_id, redis)

        tasks = []
        for _time in times:
            if _time.get("source") == "db":
                tasks.append(
                    bus.build_scheduled_db(
                        time=_time,
                        trip_id=_time.get("trip_id"),
                        st=_time.get("st"),
                        r=redis,
                        get_prev=False,
                    )
                )
            else:
                tasks.append(bus.build_scheduled(_time, redis))

        buses = await asyncio.gather(*tasks)
        buses = [bus for bus in buses if bus is not None]

        log.debug(len([b for b in buses if b.source == "db"]))

        current_time = dt.now(tz=UTC).isoformat()
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

        current_time = dt.now(tz=UTC).isoformat()
        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/")
@limiter.limit("20/minute")
async def departures(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        buses = await get_departures(stop_id, redis)

        current_time = dt.now(tz=UTC).isoformat()

        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
