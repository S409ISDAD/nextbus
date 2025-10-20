import re
from fastapi import APIRouter, Depends, HTTPException, Request

from sqlalchemy import distinct, func
from backend.models import DataSource, Journey, Service, Timetable
from backend.db.db import get_db
from sqlalchemy.orm import selectinload, joinedload

from backend.utils.time_taken import time_taken
from backend.deps import get_logger

router = APIRouter()


log = get_logger(__name__)


def natural_sort_key(text: str):
    """
    Returns a tuple that sorts:
    - pure numbers numerically first
    - then alphanumeric lines naturally
    """
    if not text:
        return (float("inf"),)  # empty lines go last

    if text.isdigit():
        return (int(text),)  # purely numeric: sort by number

    # alphanumeric: split letters/numbers
    chunks = re.split(r"(\d+)", text)
    key = []
    for c in chunks:
        if c.isdigit():
            key.append(int(c))
        else:
            key.append(c.lower())
    return (float("inf"),) + tuple(key)  # put after pure numbers


@router.get("/")
async def all_sources(
    request: Request,
    db=Depends(get_db),
):
    try:
        sources = (
            db.query(
                DataSource,
                func.count(distinct(Service.id)).label("service_count"),
                func.count(distinct(Timetable.id)).label("timetable_count"),
            )
            .outerjoin(Service, Service.data_source_id == DataSource.id)
            .outerjoin(Timetable, Timetable.data_source_id == DataSource.id)
            .options(joinedload(DataSource.versions))
            .group_by(DataSource.id)
            .order_by(DataSource.id)
            .all()
        )

        if not sources:
            raise HTTPException(404, detail="No sources found")

        data = []

        for source_obj, service_count, timetable_count in sources:
            versions_list = [
                {
                    "id": v.id,
                    "name": f"{v.start_date} to {v.end_date}"
                    if v.start_date and v.end_date
                    else v.name,
                    "start_date": v.start_date,
                    "end_date": v.end_date,
                    "url": v.url,
                    "bods_id": v.bods_id,
                    "last_modified": v.last_modified,
                }
                for v in sorted(source_obj.versions, key=lambda x: x.start_date or "")
            ]
            data.append(
                {
                    "id": source_obj.id,
                    "name": source_obj.name,
                    "description": source_obj.description,
                    "service_count": service_count,
                    "timetable_count": timetable_count,
                    "versions": versions_list,
                }
            )
        return data
    except Exception as e:
        import traceback

        traceback.print_exc()
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
                        Timetable.modified_at,
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
                    setattr(tt, "journey_count", journey_counts.get(tt.id, 0))
                    del tt.journeys

                    tt.end_date = tt.actual_end_date

                    service_code = tt.service_code
                    line_name = tt.line_name or "Unknown"

                    group = grouped_timetables.setdefault(service_code, {})
                    line_group = group.setdefault(
                        line_name, {"service": s, "timetables": []}
                    )
                    line_group["timetables"].append(tt)

            all_lines = [
                (line_name, service_code)
                for service_code, lines in grouped_timetables.items()
                for line_name in lines
            ]
            all_lines.sort(key=lambda x: natural_sort_key(x[0]))

            sorted_grouped_timetables: dict[str, dict] = {}
            for line_name, service_code in all_lines:
                sorted_grouped_timetables.setdefault(service_code, {})[line_name] = (
                    grouped_timetables[service_code][line_name]
                )
                sorted_grouped_timetables[service_code][line_name]["timetables"].sort(
                    key=lambda tt: tt.start_date
                )

            grouped_timetables = sorted_grouped_timetables

        return {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "services": grouped_timetables,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        log.error(f"Unexpected error: {e}")
        raise HTTPException(500, detail="An unexpected error occurred")
