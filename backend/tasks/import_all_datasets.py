import asyncio

from backend.config import setup_logging, get_logger
from backend.db.db import SessionLocal
from backend.deps import STATIC_DATA_DIR
from backend.models import DataSource
from backend.tasks import import_nptg, import_naptan, import_holidays
from backend.tasks.import_txc import import_datasource

log = get_logger(__name__)


async def import_weekly_data():
    log.debug("importing holidays")
    import_holidays.import_bank_holidays()

    log.debug("importing nptg")
    import_nptg.main()

    log.debug("importing naptan")
    import_naptan.main()


async def import_datasets():
    log.debug("running dataset import...")
    with SessionLocal() as db:
        datasource_ids = [id[0] for id in db.query(DataSource.id).all()]
    for id in datasource_ids:
        await import_datasource(id, STATIC_DATA_DIR)

    log.debug("dataset import complete.")


if __name__ == "__main__":
    setup_logging()
    # asyncio.run(import_weekly_data())
    asyncio.run(import_datasets())
