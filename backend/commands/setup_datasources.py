from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.models import DataSource
from backend.utils.bulk_upsert import bulk_upsert

log = get_logger(__name__)

datasources = [
    {
        "name": "Stagecoach South",
        "url": "https://opendata.stagecoachbus.com/stagecoach-scso-route-schedule-data-transxchange_2_4.zip",
    },
    {
        "name": "Cresta Coaches",
        "bods_id": 18347,
    },
    {
        "name": "Centrebus Group",
        "bods_id": 16467,
    },
    {
        "name": "Bluestar",
        "bods_id": 15872,
    },
    {
        "name": "Unilink",
        "url": "https://data.discoverpassenger.com/operator/unilink/dataset/current/download/txc",
    },
    {
        "name": "Brighton & Hove",
        "url": "https://data.discoverpassenger.com/operator/brightonhove/dataset/current/download/txc",
    },
]


def setup():
    with SessionLocal() as db:
        bulk_upsert(
            db,
            DataSource,
            datasources,
            ["name"],
            ["url", "bods_id"],
        )


if __name__ == "__main__":
    setup_logging()
    setup()
