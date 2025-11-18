from datetime import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import UTC, get_redis, limiter
from backend.services import bus, stops
from backend.tasks.get_departures import get_departures, get_scheduled
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.get("/scheduled")
@limiter.limit("45/minute")
def departures_scheduled(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        redis.sadd("total_stops", stop_id)
        times = get_scheduled(stop_id, redis)

        buses = []
        for _time in times:
            if _time.get("source") == "db":
                buses.append(
                    bus.build_scheduled_db(
                        time=_time,
                        trip_id=_time.get("trip_id"),
                        st=_time.get("st"),
                        r=redis,
                        get_prev=False,
                    )
                )
            else:
                buses.append(bus.build_scheduled(_time, redis))

        buses = [bus for bus in buses if bus is not None]

        log.debug(len([b for b in buses if b.source == "db"]))

        current_time = dt.now(tz=UTC).isoformat()
        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/live")
@limiter.limit("10/minute")
def departures_live(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        services = stops.get_services_from_stop(stop_id, redis)

        service_ids = [service.get("id") for service in services]

        buses = bus.fetch_buses_live(service_ids, stop_id, redis)

        current_time = dt.now(tz=UTC).isoformat()
        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/")
@limiter.limit("20/minute")
def departures(request: Request, stop_id: str, redis=Depends(get_redis)):
    try:
        buses = get_departures(stop_id, redis)

        current_time = dt.now(tz=UTC).isoformat()

        return {"buses": buses, "timestamp": current_time}
    except Exception as e:
        import traceback

        traceback.print_exc()
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
