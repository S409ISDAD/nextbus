import asyncio
from collections import defaultdict

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from sqlalchemy_searchable import search

from backend.db.db import SessionLocal
from backend.models import Line, Service, Stop, Operator


def fuzzy_search_service(query, db, limit=10, threshold=0.3):
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


def merge_service_line(service: Service, line: Line):
    return {
        "line_id": line.id,
        "line_name": line.line_name,
        "inbound_description": line.inbound_description,
        "outbound_description": line.outbound_description,
        "geometry": None,
        "bt_service_id": line.bt_service_id,
        "service_code": service.service_code if service else line.service_code,
        "description": service.description if service else None,
        "origin": service.origin if service else None,
        "destination": service.destination if service else None,
        "vias": service.vias if service else None,
        "operator_noc": service.operator_noc if service else None,
        "line_names": service.line_names if service else line.line_name,
    }


def search_services_and_lines(query, db: Session, limit: int = 10):
    results = []

    service_query = search(select(Service), query, sort=True).limit(limit)
    services = list(db.scalars(service_query).all())
    # If not enough results, try fuzzy search
    if len(services) < limit:
        fuzzy_services = fuzzy_search_service(query, db, limit=limit)
        # Avoid duplicates
        service_ids = {s.service_code for s in services}
        for s in fuzzy_services:
            if s.service_code not in service_ids:
                services.append(s)
        services = services[:limit]

    line_query = search(select(Line), query, sort=True).limit(limit)
    lines = list(db.scalars(line_query).all())

    seen_line_ids = set()

    for service in services:
        for line in service.lines:
            if line.id not in seen_line_ids:
                seen_line_ids.add(line.id)
                results.append(merge_service_line(service, line))

    for line in lines:
        if line.id not in seen_line_ids:
            seen_line_ids.add(line.id)
            results.append(merge_service_line(line.service, line))

    return results[:limit]


async def search_db(query: str, db: Session, limit: int = 10):
    results = defaultdict(list)

    operators_query = search(select(Operator), query, sort=True).limit(limit)
    operators = list(db.scalars(operators_query).all())
    results["operators"] = operators

    services_and_lines = search_services_and_lines(query, db, limit)
    results["lines"].extend(services_and_lines)

    stops_query = search(select(Stop), query, sort=True).limit(limit)
    stops = list(db.scalars(stops_query).all())
    for s in stops:
        if hasattr(s, "point"):
            setattr(s, "point", None)
    results["stops"] = stops

    return results


if __name__ == "__main__":
    search_query = "alton"
    with SessionLocal() as db:
        results = asyncio.run(search_db(search_query, db))
        print(f"Search results for query '{search_query}':")
        for category, items in results.items():
            print(f"\n{category.capitalize()}:")
            for item in items:
                if isinstance(item, Operator):
                    print(f"- {item.name} (NOC: {item.noc})")
                elif isinstance(item, dict):
                    print(f"- {item['line_name']} | {item['description']}")
                elif isinstance(item, Stop):
                    print(f"- {item.common_name} (ID: {item.atco_code})")
