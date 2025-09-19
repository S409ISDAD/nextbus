import asyncio

from backend.db.db import SessionLocal
from backend.deps import STATIC_DATA_DIR
from backend.models import DataSource
from backend.tasks import import_nptg, import_naptan, import_holidays
from backend.tasks.import_txc import import_datasource


async def import_weekly_data():
    print("importing holidays")
    import_holidays.import_bank_holidays()

    print("importing nptg")
    import_nptg.main()

    print("importing naptan")
    import_naptan.main()

async def import_datasets():
    print("running dataset import...")
    with SessionLocal() as db:
        datasource_ids = [id[0] for id in db.query(DataSource.id).all()]
    for id in datasource_ids:
        await import_datasource(id, STATIC_DATA_DIR)

    print("dataset import complete.")


if __name__ == "__main__":
    # asyncio.run(import_weekly_data())
    asyncio.run(import_datasets())
