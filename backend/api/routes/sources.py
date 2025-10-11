from fastapi import APIRouter, Depends, HTTPException, Request
import logging

from sqlalchemy import distinct, func
from backend.models import DataSource, Journey, Service, Timetable
from backend.db.db import get_db
from sqlalchemy.orm import load_only, selectinload

from backend.utils.time_taken import time_taken

router = APIRouter()

log = logging.getLogger(__name__)


@router.get("/")
async def all_sources(
    request: Request,
    db=Depends(get_db),
):
    try:
        sources = (
            db.query(
                DataSource.id,
                DataSource.name,
                DataSource.description,
                DataSource.url,
                DataSource.bods_id,
                DataSource.last_modified,
                func.count(distinct(Service.id)).label("service_count"),
                func.count(distinct(Timetable.id)).label("timetable_count"),
            )
            .outerjoin(Service, Service.data_source_id == DataSource.id)
            .outerjoin(Timetable, Timetable.data_source_id == DataSource.id)
            .group_by(DataSource.id)
            .order_by(DataSource.id)
            .all()
        )

        if not sources:
            raise HTTPException(404, detail="No sources found")

        data = []

        for source in sources:
            data.append(
                {
                    "id": source.id,
                    "name": source.name,
                    "description": source.description,
                    "url": source.url,
                    "bods_id": source.bods_id,
                    "last_modified": source.last_modified,
                    "service_count": source.service_count,
                    "timetable_count": source.timetable_count,
                }
            )
        return data
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")


@router.get("/{id}/")
async def source(
    request: Request,
    id: int,
    db=Depends(get_db),
):
    try:
        with time_taken("Fetch data source details"):
            source = (
                db.query(DataSource)
                .options(
                    # Load services
                    selectinload(DataSource.services)
                    .load_only(
                        Service.id,
                        Service.line_name,
                        Service.service_code,
                        Service.last_modified,
                    )
                    # Also prefetch timetables for each service
                    .selectinload(Service.timetables)
                    .load_only(
                        Timetable.id,
                        Timetable.service_code,
                        Timetable.line_name,
                        Timetable.start_date,
                        Timetable.end_date,
                        Timetable.revision_number,
                    )
                    .selectinload(Timetable.journeys)
                    .load_only(Journey.id),
                )
                .filter(DataSource.id == id)
                .first()
            )
        if not source:
            raise HTTPException(404, detail="Data source not found")

        with time_taken("Process journey counts"):
            journey_counts = dict(
                db.query(Timetable.id, func.count(Journey.id))
                .join(Journey, Journey.timetable_id == Timetable.id)
                .filter(Timetable.data_source_id == id)
                .group_by(Timetable.id)
                .all()
            )

        with time_taken("Group services and timetables"):
            grouped_timetables: dict[str, dict] = {}

            for s in source.services:
                for tt in s.timetables:
                    if tt.service_code not in grouped_timetables:
                        grouped_timetables[tt.service_code] = {}

                    group = grouped_timetables[tt.service_code]

                    del tt.journeys

                    tt.end_date = tt.actual_end_date

                    setattr(tt, "journey_count", journey_counts.get(tt.id, 0))

                    if tt.line_name not in group:
                        group[tt.line_name] = {"service": s, "timetables": []}

                    group[tt.line_name]["timetables"].append(tt)

        return {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "bods_id": source.bods_id,
            "services": grouped_timetables,
        }
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")
