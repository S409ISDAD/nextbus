import asyncio
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy_searchable import search

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import Service, Stop, Operator, Locality
import sys

log = get_logger()


def search_services(query, db: Session, limit: int = 10):
    results = []

    if len(query) <= 3:
        service_query = select(
            Service,
            func.ts_rank_cd(
                Service.search_vector, func.websearch_to_tsquery(query)
            ).label("rank"),
        ).where(Service.line_name.ilike(f"%{query}%"))
    else:
        service_query = search(
            select(Service),
            query,
            sort=True,
        ).add_columns(
            func.ts_rank_cd(
                Service.search_vector, func.websearch_to_tsquery(query)
            ).label("rank")
        )

    services = db.execute(service_query).all()
    for service, rank in services:
        if not rank:
            rank = 1.0
        data = service.with_timetable()
        data["rank"] = rank
        results.append(data)

    results.sort(key=lambda x: x["rank"], reverse=True)

    return results[:limit]


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
        for l in localities:
            if hasattr(l, "point"):
                setattr(l, "point", None)
        results["localities"] = localities
    else:
        results["localities"] = []

    services = search_services(query, db, limit)
    service_ids.update(set([s["service_id"] for s in services]))

    services_served = set()

    for locality in results["localities"]:
        served = locality.services_served()
        for service in served:
            if service:
                services_served.add(service.id)

    service_query = db.query(Service).filter(Service.id.in_(services_served)).all()

    for service in service_query:
        if service.id not in service_ids:
            data = service.with_timetable()
            data["rank"] = 1.0
            services.append(data)

    results["lines"] = services

    results["lines"].sort(key=lambda x: x["rank"], reverse=True)

    # stops_query = search(select(Stop), query, sort=True).limit(limit)
    # stops = list(db.scalars(stops_query).all())
    # for s in stops:
    #     if hasattr(s, "point"):
    #         setattr(s, "point", None)
    # results["stops"] = stops

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
                    print(f"- {item.name} ({item.qualifier_name or 'none'})")
