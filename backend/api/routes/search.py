from fastapi import APIRouter, Depends, HTTPException
import logging
from backend.db.db import get_db
from backend.utils.search import search_db

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/")
async def search(query: str, db=Depends(get_db)):
    try:
        if not query or len(query) < 1:
            raise HTTPException(400, detail="Query can't be empty")

        results = await search_db(query, db)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
