from fastapi import APIRouter, Depends, Request, HTTPException
from backend.deps import get_redis, limiter

from backend.models import Service
from backend.db.db import get_db
from sqlalchemy.orm import joinedload
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.get("/{service_id}")
@limiter.limit("45/minute")
def service(
    request: Request, service_id: str, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        service: Service = (
            db.query(Service)
            .options(
                joinedload(Service.timetables),
                joinedload(Service.operators),
                joinedload(Service.data_source),
            )
            .filter(Service.id == service_id)
            .first()
        )

        if not service:
            raise HTTPException(404, detail="Service not found")

        return service.with_timetable()
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
