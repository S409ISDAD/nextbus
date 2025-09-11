from fastapi import APIRouter, Depends, Request, HTTPException
import logging
from backend.deps import get_redis, limiter

# from backend.schemas.line import Line
from backend.models import Line, Service
from backend.db.db import get_db
from sqlalchemy.orm import joinedload
from backend.utils.match_bt import match_service_line
from backend.utils.search import merge_service_line

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/{line_id}")
@limiter.limit("45/minute")
async def line(
    request: Request, line_id: str, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        if line_id.isdigit():
            line = await match_service_line(db, int(line_id), redis)
            if not line:
                raise HTTPException(
                    404, detail=f"Line not found with bt service id {line_id}"
                )
            line_id = str(line.id)

        line: Line = (
            db.query(Line)
            .options(joinedload(Line.service).joinedload(Service.operator))
            .filter(Line.id == line_id)
            .first()
        )

        if not line:
            raise HTTPException(404, detail="Line not found")

        service = line.service
        line_service = merge_service_line(service, line)

        return line_service
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
