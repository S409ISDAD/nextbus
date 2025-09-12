import asyncio
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy_searchable import search

from backend.db.db import SessionLocal
from backend.models import Line, Service, Stop, Operator


def merge_service_line(service: Service, line: Line, rank: float):
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
        "rank": rank,
    }


def search_services_and_lines(query, db: Session, limit: int = 10):
    results = []

    if len(query) <= 3:
        service_query = (
            db.query(Service, Line)
            .join(Line, Service.service_code == Line.service_code)
            .filter(
                Line.line_name.ilike(f"%{query}%"),
            )
            .add_columns(
                func.ts_rank_cd(
                    Line.search_vector, func.websearch_to_tsquery(query)
                ).label("rank")
            )
        )
    else:
        service_query = search(
            select(Service, Line).join(Line, Service.service_code == Line.service_code),
            query,
            sort=True,
        ).add_columns(
            func.greatest(
                func.ts_rank_cd(
                    Service.search_vector, func.websearch_to_tsquery(query)
                ),
                func.ts_rank_cd(Line.search_vector, func.websearch_to_tsquery(query)),
            ).label("rank")
        )

    services_and_lines = db.execute(service_query).all()
    for service, line, rank in services_and_lines:
        results.append(merge_service_line(service, line, rank))

    results.sort(key=lambda x: x["rank"], reverse=True)

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
                    print(
                        f"- {item['line_name']} | {item['description']} (rank: {item['rank']})"
                    )
                elif isinstance(item, Stop):
                    print(f"- {item.common_name} (ID: {item.atco_code})")
