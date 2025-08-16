from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
import logging

from backend.db.db import get_db
from backend.deps import floor_to_30s, get_redis
from backend.models import ActiveUsersSnapshot
from fastapi import Query
from datetime import timedelta

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/")
async def stats(redis=Depends(get_redis)):
    try:
        total_ws_connections = int(await redis.get("total_ws_connections") or 0)
        unique_ws_connections = await redis.scard("clients")
        return {
            "total_active": total_ws_connections,
            "unique_active": unique_ws_connections,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeseries")
def get_active_user_stats(
    start: datetime = Query(default_factory=lambda: datetime.now() - timedelta(days=1)),
    end: datetime = Query(default_factory=datetime.now),
    db=Depends(get_db),
):
    rows = (
        db.query(ActiveUsersSnapshot)
        .filter(
            ActiveUsersSnapshot.timestamp >= start,
            ActiveUsersSnapshot.timestamp <= end,
        )
        .order_by(ActiveUsersSnapshot.timestamp)
        .all()
    )

    data_by_ts = {r.timestamp: r for r in rows}

    interval = timedelta(seconds=30)
    current = floor_to_30s(start)
    end = floor_to_30s(end)
    result = []
    while current <= end:
        row = data_by_ts.get(current)
        result.append(
            {
                "timestamp": current.isoformat(),
                "total": row.total_connections if row else None,
                "unique": row.unique_connections if row else None,
            }
        )
        current += interval

    return result
