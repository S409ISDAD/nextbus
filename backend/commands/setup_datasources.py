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
        "name": "Stagecoach South East",
        "url": "https://opendata.stagecoachbus.com/stagecoach-scek-route-schedule-data-transxchange_2_4.zip",
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
        "name": "First Portsmouth, Fareham & Gosport",
        "bods_id": 2349,
    },
    {
        "name": "AMK",
        "bods_id": 18180,
    },
    {
        "name": "Xelabus",
        "bods_id": 18484,
    },
    {
        "name": "Bee Network",
        "bods_id": 17472,
    },
    {
        "name": "Swindon Bus Company",
        "bods_id": 15879,
    },
    {
        "name": "Thames Valley Buses",
        "url": "https://data.discoverpassenger.com/operator/courtney/dataset/current/download/txc",
    },
    {
        "name": "White Bus",
        "url": "https://opendata.ticketer.com/uk/WBSV/routes_and_timetables/current.zip",
    },
    {
        "name": "Unilink",
        "url": "https://data.discoverpassenger.com/operator/unilink/dataset/current/download/txc",
    },
    {
        "name": "Brighton & Hove",
        "url": "https://data.discoverpassenger.com/operator/brightonhove/dataset/current/download/txc",
    },
    {
        "name": "Reading Buses",
        "url": "https://data.discoverpassenger.com/operator/readingbuses/dataset/current/download/txc",
    },
    {
        "name": "Morebus",
        "url": "https://data.discoverpassenger.com/operator/morebus/dataset/current/download/txc",
    },
    {
        "name": "Newbury & District",
        "url": "https://data.discoverpassenger.com/operator/kennections/dataset/current/download/txc",
    },
    {
        "name": "Salisbury Reds",
        "url": "https://data.discoverpassenger.com/operator/salisburyreds/dataset/current/download/txc",
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
