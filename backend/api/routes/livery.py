from fastapi import APIRouter, Depends, Request

from backend.deps import get_redis, limiter
from backend.models.livery import Livery
from backend.services.livery import get_livery


router = APIRouter()


@router.get("/", response_model=Livery | None)
@limiter.limit("5/minute")
async def livery(request: Request, id: int, redis=Depends(get_redis)):
    livery = await get_livery(id, redis)

    return livery
