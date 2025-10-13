from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
import logging
from backend.db.db import get_db
from backend.deps import LONDON, get_redis, limiter
from backend.models import Service
from backend.utils.generate_timetable import generate_timetable
from backend.services.caching import TIMETABLE_CACHE, get_cached

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/{service_id}")
@limiter.limit("45/minute")
async def service_timetable(
    request: Request,
    service_id: int,
    inbound: bool = True,
    db=Depends(get_db),
    redis=Depends(get_redis),
):
    try:

        async def fetch(service_id, inbound):
            today = datetime.now(tz=LONDON)

            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                raise HTTPException(
                    status_code=404, detail=f"Service {service_id} not found"
                )

            timetable = generate_timetable(service, today, db, inbound=inbound)
            return timetable

        timetable = await get_cached(
            f"timetable:{service_id}:{'in' if inbound else 'out'}",
            fetch,
            (service_id, inbound),
            TIMETABLE_CACHE,
            redis,
        )

        return timetable
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
