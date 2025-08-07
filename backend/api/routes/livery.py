from fastapi import APIRouter, Depends, HTTPException, Request
import logging
from backend.deps import get_redis, limiter
from backend.schemas.livery import Livery
from backend.services.livery import get_livery


router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/", response_model=Livery | None)
@limiter.limit("20/minute")
async def livery(request: Request, id: int, redis=Depends(get_redis)):
    try:
        livery = await get_livery(id, redis)

        return livery
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
