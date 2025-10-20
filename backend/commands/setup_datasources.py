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
    # {
    #     "name": "Stagecoach South East",
    #     "url": "https://opendata.stagecoachbus.com/stagecoach-scek-route-schedule-data-transxchange_2_4.zip",
    # },
    {
        "name": "Cresta Coaches",
        "noc": "CRES",
    },
    # {
    #     "name": "Centrebus Group",
    #     "bods_id": 16467,
    # },
    {
        "name": "Bluestar",
        "noc": "BLUS",
        "search": "bluestar",
    },
    {
        "name": "First Portsmouth, Fareham & Gosport",
        "noc": "FHAM",
        "search": "portsmouth",
    },
    {
        "name": "AMK",
        "noc": "AMKC",
        "search": "amk",
    },
    {
        "name": "Xelabus",
        "noc": "XLBL",
        "search": "xelabus",
    },
    # {
    #     "name": "Bee Network",
    #     "url": "https://odata.tfgm.com/opendata/downloads/TfGMtxcnew.zip",
    # },
    {
        "name": "Swindon Bus Company",
        "noc": "TDTR",
        "search": "swindon bus company",
    },
    {
        "name": "Thames Valley Buses",
        "url": "https://data.discoverpassenger.com/operator/courtney",
    },
    {
        "name": "White Bus",
        "url": "https://opendata.ticketer.com/uk/WBSV/routes_and_timetables/current.zip",
    },
    {
        "name": "Unilink",
        "url": "https://data.discoverpassenger.com/operator/unilink",
    },
    {
        "name": "Brighton & Hove",
        "url": "https://data.discoverpassenger.com/operator/brightonhove",
    },
    {
        "name": "Reading Buses",
        "url": "https://data.discoverpassenger.com/operator/readingbuses",
    },
    {
        "name": "Morebus",
        "url": "https://data.discoverpassenger.com/operator/morebus",
    },
    {
        "name": "Newbury & District",
        "url": "https://data.discoverpassenger.com/operator/kennections",
    },
    {
        "name": "Salisbury Reds",
        "url": "https://data.discoverpassenger.com/operator/salisburyreds",
    },
]


def setup():
    with SessionLocal() as db:
        bulk_upsert(
            db,
            DataSource,
            datasources,
            ["name"],
            ["url", "noc", "search"],
        )


if __name__ == "__main__":
    setup_logging()
    setup()
