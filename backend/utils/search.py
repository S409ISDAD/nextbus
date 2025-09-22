import asyncio
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy_searchable import search

from backend.db.db import SessionLocal
from backend.models import Line, Service, Stop, Operator, Locality


def merge_service_line(service: Service, line: Line, operator: Operator, rank: float):
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
        "operator": operator.name,
        "line_names": service.line_names if service else line.line_name,
        "rank": rank,
    }


def search_services_and_lines(query, db: Session, limit: int = 10):
    results = []

    if len(query) <= 3:
        service_query = (
            db.query(Service, Line, Operator)
            .join(Line, Service.service_code == Line.service_code)
            .join(Operator, Service.operator_noc == Operator.noc)
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
            select(Service, Line, Operator).join(Line, Service.service_code == Line.service_code).join(Operator,
                                                                                                       Service.operator_noc == Operator.noc),
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
    for service, line, operator, rank in services_and_lines:
        results.append(merge_service_line(service, line, operator, rank))

    results.sort(key=lambda x: x["rank"], reverse=True)

    return results[:limit]


async def search_db(query: str, db: Session, limit: int = 20):
    results = defaultdict(list)

    operators_query = search(select(Operator), query, sort=True).limit(limit)
    operators = list(db.scalars(operators_query).all())
    results["operators"] = operators

    lines = []
    line_ids = set()

    if len(query) >= 4:
        localities_query = search(select(Locality), query, sort=True).limit(500)
        localities = list(db.scalars(localities_query).all())
        for l in localities:
            if hasattr(l, "point"):
                setattr(l, "point", None)
        results["localities"] = localities
    else:
        results["localities"] = []

    services_and_lines = search_services_and_lines(query, db, limit)
    lines.extend(services_and_lines)
    line_ids.update([l["line_id"] for l in services_and_lines])

    lines_served = set()

    for locality in results["localities"]:
        served = locality.lines_served()
        for line in served:
            if line:
                lines_served.add(line.id)

    service_query = (db.query(Service, Line, Operator)
                     .join(Line, Service.service_code == Line.service_code)
                     .join(Operator, Service.operator_noc == Operator.noc)
                     .filter(Line.id.in_(lines_served)).all())

    for service, line, operator in service_query:
        if line.id not in line_ids:
            lines.append(merge_service_line(service, line, operator, 1.0))

    results["lines"] = lines
    results["lines"].sort(key=lambda x: x["rank"], reverse=True)

    # stops_query = search(select(Stop), query, sort=True).limit(limit)
    # stops = list(db.scalars(stops_query).all())
    # for s in stops:
    #     if hasattr(s, "point"):
    #         setattr(s, "point", None)
    # results["stops"] = stops


    return results


if __name__ == "__main__":
    search_query = "hant"
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
                    print(f"- {item.name} ({item.qualifier_name or "none"})")
