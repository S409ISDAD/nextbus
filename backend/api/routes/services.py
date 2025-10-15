from fastapi import APIRouter, Depends, Request, HTTPException
from backend.deps import get_redis, limiter
from backend.schemas.service import Service
from backend.services import services
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.get("/", response_model=Service)
@limiter.limit("45/minute")
async def service_details(request: Request, service_id: int, redis=Depends(get_redis)):
    try:
        service_details = await services.get_service_info(service_id, redis)

        return service_details
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
