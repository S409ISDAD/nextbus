from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import DataSource
from backend.utils.bulk_upsert import bulk_upsert
import json

log = get_logger(__name__)


def setup():
    with open("backend/commands/sources.json", "r") as f:
        datasources = json.load(f)
        log.debug(f"Loaded {len(datasources)} datasources from sources.json")

    for ds in datasources:
        if "disabled" not in ds:
            ds["disabled"] = False

    with SessionLocal() as db:
        bulk_upsert(
            db,
            DataSource,
            datasources,
            ["name"],
            ["url", "noc", "search", "disabled"],
        )


if __name__ == "__main__":
    setup_logging()
    setup()
