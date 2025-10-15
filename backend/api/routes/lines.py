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
async def service(
    request: Request, service_id: str, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        service: Service = (
            db.query(Service)
            .options(
                joinedload(Service.timetables),
                joinedload(Service.operator),
                joinedload(Service.data_source),
            )
            .filter(Service.id == service_id)
            .first()
        )

        if not service:
            raise HTTPException(404, detail="Service not found")

        timetable = service.timetables[0] if service.timetables else None
        operator = service.operator

        if timetable:
            return {
                "service_id": service.id,
                "line_name": timetable.line_name,
                "inbound_description": timetable.inbound_description,
                "outbound_description": timetable.outbound_description,
                "geometry": None,
                "bt_service_id": service.bt_service_id,
                "service_code": service.service_code,
                "description": service.description,
                "origin": timetable.origin,
                "destination": timetable.destination,
                "vias": timetable.vias,
                "operator_noc": operator.noc,
                "operator": operator.name,
                "last_modified": timetable.modified_at
                or service.data_source.last_modified,
            }
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
