from fastapi import APIRouter, Depends, HTTPException, Request
import logging
from backend.models import Locality, District, Region, AdminArea
from backend.db.db import get_db

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/localities/{id}")
async def localities(
    request: Request,
    id: str,
    db=Depends(get_db),
):
    try:
        locality: Locality | None = db.query(Locality).filter(Locality.id == id).first()
        if not locality:
            raise HTTPException(404, detail="Locality not found")

        lines = locality.lines_served()
        stops = locality.stops

        for line in lines:
            line.geometry = None

        for stop in stops:
            stop.point = None

        return {
            "id": locality.id,
            "name": locality.name,
            "qualifier": locality.qualifier_name,
            "lines": lines,
            "stops": stops,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/districts/{id}")
async def districts(
    request: Request,
    id: str,
    db=Depends(get_db),
):
    try:
        district: District | None = db.query(District).filter(District.id == id).first()
        if not district:
            raise HTTPException(404, detail="District not found")

        localities = district.localities

        for locality in localities:
            locality.point = None

        return {
            "id": district.id,
            "name": district.name,
            "localities": localities,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/admin_areas/{id}")
async def admin_areas(
    request: Request,
    id: str,
    db=Depends(get_db),
):
    try:
        admin_area: AdminArea | None = (
            db.query(AdminArea).filter(AdminArea.id == id).first()
        )
        if not admin_area:
            raise HTTPException(404, detail="Admin Area not found")

        districts = admin_area.districts
        for district in districts:
            district.point = None

        return {
            "id": admin_area.id,
            "name": admin_area.name,
            "districts": districts,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/regions/{id}")
async def regions(
    request: Request,
    id: str,
    db=Depends(get_db),
):
    try:
        region: Region | None = db.query(Region).filter(Region.id == id).first()
        if not region:
            raise HTTPException(404, detail="Region not found")

        admin_areas = region.admin_areas

        for area in admin_areas:
            area.point = None

        return {
            "id": region.id,
            "name": region.name,
            "admin_areas": admin_areas,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")
