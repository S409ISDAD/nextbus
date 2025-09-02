import asyncio
from collections import defaultdict

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from sqlalchemy_searchable import search

from backend.db.db import SessionLocal
from backend.models import Line, Service, Stop, Operator


def fuzzy_search_service(query, db, limit=10, threshold=0.2):
    # Fuzzy search on Service.description and Service.line_names
    return (
        db.query(Service)
        .filter(
            or_(
                func.similarity(Service.description, query) > threshold,
                func.similarity(Service.line_names, query) > threshold,
            )
        )
        .order_by(
            func.greatest(
                func.similarity(Service.description, query),
                func.similarity(Service.line_names, query),
            ).desc()
        )
        .limit(limit)
        .all()
    )


async def search_db(query: str, db: Session, limit: int = 10):
    results = defaultdict(list)

    operators_query = search(select(Operator), query).limit(limit)
    operators = list(db.scalars(operators_query).all())
    results["operators"] = operators

    service_query = search(select(Service), query).limit(limit)
    service = list(db.scalars(service_query).all())
    # If not enough results, try fuzzy search
    if len(service) < limit:
        fuzzy_services = fuzzy_search_service(query, db, limit=limit)
        # Avoid duplicates
        service_ids = {s.service_code for s in service}
        for s in fuzzy_services:
            if s.service_code not in service_ids:
                service.append(s)
        service = service[:limit]
    results["service"] = service

    line_query = search(select(Line), query).limit(limit)
    line = list(db.scalars(line_query).all())
    results["line"] = line

    stops_query = search(select(Stop), query).limit(limit)
    stops = list(db.scalars(stops_query).all())
    results["stops"] = stops

    print(f"Search results for query '{query}':")
    for category, items in results.items():
        print(f"\n{category.capitalize()}:")
        for item in items:
            if isinstance(item, Operator):
                print(f"- {item.name} (NOC: {item.noc})")
            elif isinstance(item, Service):
                print(
                    f"- {item.description} | {item.line_names} (ID: {item.service_code})"
                )
            elif isinstance(item, Line):
                print(f"- {item.line_name} | {item.outbound_description}")
            elif isinstance(item, Stop):
                print(f"- {item.common_name} (ID: {item.atco_code})")

    return results


if __name__ == "__main__":
    search_query = "64 Morn Hill, Alresford, Four Marks"
    with SessionLocal() as db:
        asyncio.run(search_db(search_query, db))
