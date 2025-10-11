import asyncio
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy_searchable import search

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import Service, Stop, Operator, Locality
import sys

log = get_logger(__name__)


def search_services(query, db: Session, limit: int = 10):
    results = []

    if len(query) <= 3:
        service_query = (
            select(
                Service,
                func.ts_rank_cd(
                    Service.search_vector, func.websearch_to_tsquery(query)
                ).label("rank"),
            )
            .where(Service.line_name.ilike(f"%{query}%"))
            .limit(100)
        )
    else:
        service_query = (
            search(
                select(Service),
                query,
                sort=True,
            )
            .add_columns(
                func.ts_rank_cd(
                    Service.search_vector, func.websearch_to_tsquery(query)
                ).label("rank")
            )
            .limit(100)
        )

    services = db.execute(service_query).all()
    for service, rank in services:
        data = service.with_timetable()
        if data is None:
            log.warning(f"Service {service.id} returned None from with_timetable()")
            continue
        data["rank"] = rank or 0.0
        data["service_id"] = service.id
        results.append(data)

    results.sort(key=lambda x: x["rank"], reverse=True)

    # return results[:limit]
    return results


async def search_db(query: str, db: Session, limit: int = 20):
    results = defaultdict(list)

    operators_query = search(select(Operator), query, sort=True).limit(limit)
    operators = list(db.scalars(operators_query).all())
    results["operators"] = operators

    services = []
    service_ids = set()

    if len(query) >= 4:
        localities_query = search(select(Locality), query, sort=True).limit(500)
        localities = list(db.scalars(localities_query).all())
        localities = [loc for loc in localities if loc.has_stops]
        for loc in localities:
            del loc.point
            del loc.stops
            del loc.parent
            del loc.district
            del loc.admin_area
            setattr(loc, "full_name", loc.get_full_name)
        results["localities"] = localities
    else:
        results["localities"] = []

    services = search_services(query, db, limit)
    service_ids.update(set([s["service_id"] for s in services]))

    services_served = set()

    if len(results["localities"]) <= 4:
        for locality in results["localities"]:
            served = locality.services_served()
            for service in served:
                if service:
                    services_served.add(service.id)

    if len(results["operators"]) <= 2:
        for operator in results["operators"]:
            served = operator.services
            for service in served:
                if service:
                    services_served.add(service.id)

    service_query = db.query(Service).filter(Service.id.in_(services_served)).all()

    for service in service_query:
        if service.id not in service_ids:
            data = service.with_timetable()
            if data is None:
                log.warning(f"Service {service.id} returned None from with_timetable()")
                continue
            data["rank"] = 0.0
            services.append(data)

    results["services"] = services

    results["services"].sort(key=lambda x: x["rank"], reverse=True)

    for operator in results["operators"]:
        del operator.services

    from fastapi.encoders import jsonable_encoder

    results["localities"] = [jsonable_encoder(loc) for loc in results["localities"]]

    results["operators"] = [jsonable_encoder(op) for op in results["operators"]]

    return results


if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) > 1:
        search_query = sys.argv[1]
    else:
        search_query = ""
    with SessionLocal() as db:
        results = asyncio.run(search_db(search_query, db))
        print(f"Search results for query '{search_query}':")
        for category, items in results.items():
            print(f"\n{category.capitalize()}:")
            for item in items:
                if isinstance(item, Operator):
                    print(f"- {item.name} (NOC: {item.noc})")
                elif isinstance(item, dict):
                    print(
                        f"- {item['line_name']} | {item['description']} (rank: {item['rank']})"
                    )
                elif isinstance(item, Stop):
                    print(f"- {item.name} (ID: {item.atco_code})")
                elif isinstance(item, Locality):
                    print(f"- {item.get_full_name}")
