from fastapi import APIRouter, Depends

from backend.deps import get_redis
from backend.models.livery import Livery
from backend.services.livery import get_livery


router = APIRouter()


@router.get("/", response_model=Livery | None)
async def livery(id: int, redis=Depends(get_redis)):
    livery = await get_livery(id, redis)

    return livery
