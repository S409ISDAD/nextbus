from fastapi import APIRouter, Depends, Request, HTTPException
import logging
from backend.deps import get_redis, limiter
from backend.models.service import Service
from backend.services import services

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/", response_model=Service)
@limiter.limit("45/minute")
async def service_details(request: Request, service_id: int, redis=Depends(get_redis)):
    try:
        service_details = await services.get_service_info(service_id, redis)

        return Service(
            id=service_details.id,
            line_name=service_details.line_name,
            detail=service_details.detail,
        )
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
