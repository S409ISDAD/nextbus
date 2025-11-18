from fastapi import APIRouter, Depends, HTTPException, Request
from backend.models import Locality, District, Region, AdminArea, Service
from backend.db.db import get_db
from sqlalchemy.orm import joinedload
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


@router.get("/localities/{id}/")
def localities(
    request: Request,
    id: str,
    db=Depends(get_db),
):
    try:
        locality: Locality | None = db.query(Locality).filter(Locality.id == id).first()
        if not locality:
            raise HTTPException(404, detail="Locality not found")

        services: list[Service] = locality.services_served()
        stops = locality.stops

        for service in services:
            service.operators = service.operators
            del service.geometry

        stops = [stop for stop in stops if stop.does_serve_buses]

        for stop in stops:
            del stop.point
            del stop.services

        stops.sort(key=lambda s: s.common_name)
        services.sort(key=lambda s: s.line_name)

        return {
            "id": locality.id,
            "name": locality.name,
            "qualifier": locality.qualifier_name,
            # "slug": locality.slug,
            "services": services,
            "stops": stops,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/districts/{id}/")
def districts(
    request: Request,
    id: str,
    db=Depends(get_db),
):
    try:
        district: District | None = (
            db.query(District)
            .filter(District.id == id)
            .options(joinedload(District.localities).joinedload(Locality.stops))
            .first()
        )
        if not district:
            raise HTTPException(404, detail="District not found")

        localities = district.localities

        valid_localities = [loc for loc in localities if loc.has_stops]

        for locality in valid_localities:
            locality.point = None
            del locality.stops

        valid_localities.sort(key=lambda loc: loc.name)

        return {
            "id": district.id,
            "name": district.name,
            "localities": valid_localities,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/admin_areas/{id}/")
def admin_areas(
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

        districts.sort(key=lambda d: d.name)

        return {
            "id": admin_area.id,
            "name": admin_area.name,
            "districts": districts,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/regions/")
def regions_all(
    request: Request,
    db=Depends(get_db),
):
    try:
        regions = db.query(Region).all()
        if not regions:
            raise HTTPException(404, detail="No regions found")

        return [
            {
                "id": region.id,
                "name": region.name,
            }
            for region in regions
        ]
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/regions/{id}/")
def regions(
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

        admin_areas.sort(key=lambda a: a.name)

        return {
            "id": region.id,
            "name": region.name,
            "admin_areas": admin_areas,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")
