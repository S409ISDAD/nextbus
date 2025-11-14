from fastapi import APIRouter, Depends, HTTPException, Request

from backend.db.db import get_db
from backend.deps import get_redis
from backend.models import Service, Stop, Operator

from backend.services.caching import get_cached
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.get("/")
async def stats(redis=Depends(get_redis)):
    try:
        total_buses = await redis.scard("total_buses")
        total_stops = await redis.scard("total_stops")
        return {
            "total_buses": total_buses,
            "total_stops": total_stops,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db")
async def db_stats(request: Request, db=Depends(get_db), redis=Depends(get_redis)):
    async def get_stats(db):
        total_services = db.query(Service).filter(Service.current).count()
        total_stops = db.query(Stop).filter(Stop.active).count()
        total_operators = db.query(Operator).count()
        return {
            "lines": total_services,
            "stops": total_stops,
            "operators": total_operators,
        }

    try:
        cached_stats = await get_cached(
            "db_stats",
            get_stats,
            (db,),
            300,  # 5 minutes
            redis,
        )
        return cached_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
