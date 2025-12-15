from datetime import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Request

from backend.db.db import get_db
from backend.deps import UTC, get_redis, limiter
from backend.models import Journey, Service, Stop, StopTime
from backend.schemas.departures import DeparturesResponse
from backend.services import bus, stops
from backend.tasks.get_departures import get_departures, get_scheduled
from backend.deps import get_logger
from backend.utils.time_taken import time_taken
from sqlalchemy.orm import selectinload

router = APIRouter()


log = get_logger(__name__)


@router.get("/scheduled", response_model=DeparturesResponse)
@limiter.limit("45/minute")
def departures_scheduled(
    request: Request, stop_id: str, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        redis.sadd("total_stops", stop_id)  # track number of stops requested
        times = get_scheduled(
            stop_id, redis
        )  # get scheduled times from helper function

        # generate list of all StopTime object IDs to preload
        stop_time_ids = [t["st"].id for t in times if t.get("source") == "db"]

        # preload all StopTime objects beforehand to speed up processing
        preloaded = (
            db.query(StopTime)
            .filter(StopTime.id.in_(stop_time_ids))
            .options(
                selectinload(StopTime.journey).selectinload(Journey.timetable),
                selectinload(StopTime.journey)
                .selectinload(Journey.service)
                .selectinload(Service.operators),
                selectinload(StopTime.journey)
                .selectinload(Journey.destination)
                .selectinload(Stop.locality),
            )
            .all()
        )

        stop_time_map = {st.id: st for st in preloaded}  # map of StopTime ID to object

        buses = []
        with time_taken("building scheduled buses"):
            for _time in times:
                # loop through each scheduled time and build bus object
                if _time.get("source") == "db":
                    # if the departure came from the database, use the StopTime object to build
                    buses.append(
                        bus.build_scheduled_db(
                            time=_time,
                            trip_id=_time.get("trip_id"),
                            st=_time.get("st"),
                            st_map=stop_time_map,
                            r=redis,
                            get_prev=False,
                        )
                    )
                else:
                    # otherwise, it came from bustimes.org, build normally
                    buses.append(bus.build_scheduled(_time, redis))

        # filter out any None values (failed/not included buses)
        buses = [bus for bus in buses if bus is not None]

        log.debug(len([b for b in buses if b.source == "db"]))

        current_time = dt.now(tz=UTC).isoformat()
        return {
            "buses": buses,
            "timestamp": current_time,
        }  # return buses with current timestamp
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")


@router.get("/live", response_model=DeparturesResponse)
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


@router.get("/", response_model=DeparturesResponse)
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
