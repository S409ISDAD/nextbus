from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy_searchable import search

from backend.db.db import SessionLocal
from backend.models import Line, Service, Stop, Operator


def search_db(query: str, db: Session, limit: int = 10):
    results = defaultdict(list)

    operators_query = search(select(Operator), query).limit(limit)
    operators = list(db.scalars(operators_query).all())
    results["operators"] = operators

    service_query = search(select(Service), query).limit(limit)
    service = list(db.scalars(service_query).all())
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
    search_query = "alresford"
    with SessionLocal() as db:
        search_db(search_query, db)
