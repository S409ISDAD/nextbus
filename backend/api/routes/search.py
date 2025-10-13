from fastapi import APIRouter, Depends, HTTPException
import logging
from backend.db.db import get_db
from backend.deps import get_redis
from backend.utils.search import search_db
from backend.services.caching import get_cached

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/")
async def search(
    query: str, limit: int = 10, db=Depends(get_db), redis=Depends(get_redis)
):
    try:
        if not query or len(query) < 1:
            raise HTTPException(400, detail="Query can't be empty")

        async def fetch(query, limit):
            return await search_db(query, db, limit)

        results = await get_cached(
            f"search:{query}:{limit}", fetch, args=(query, limit), exp=30, r=redis
        )

        return results

    except Exception as e:
        log.error(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
