from fastapi import APIRouter, Depends, Request, HTTPException
import logging
from backend.deps import get_redis, limiter

# from backend.schemas.line import Line
from backend.models import Line
from backend.db.db import get_db
from geoalchemy2.shape import to_shape

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/{line_id}")
@limiter.limit("45/minute")
async def line(
    request: Request, line_id: str, redis=Depends(get_redis), db=Depends(get_db)
):
    try:
        line = db.query(Line).filter(Line.id == line_id).first()

        if line and line.geometry:
            geom = to_shape(line.geometry)
            from shapely.geometry import MultiLineString, LineString

            if isinstance(geom, LineString):
                line.geometry = [[lat, lon] for lon, lat in geom.coords]
            elif isinstance(geom, MultiLineString):
                # For MultiLineString or similar
                line.geometry = [
                    [[lat, lon] for lon, lat in linestring.coords]
                    for linestring in geom.geoms
                    if hasattr(linestring, "coords")
                ]
            else:
                line.geometry = []

        return line
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occured")
