import asyncio

from backend.db.db import SessionLocal
from backend.deps import STATIC_DATA_DIR
from backend.models import DataSource
from backend.tasks.import_txc import import_datasource


async def import_datasets():
    print("running dataset import...")
    with SessionLocal() as db:
        datasources = db.query(DataSource).all()
        for datasource in datasources:
            await import_datasource(datasource.id, STATIC_DATA_DIR)

    print("dataset import complete.")


if __name__ == "__main__":
    asyncio.run(import_datasets())
