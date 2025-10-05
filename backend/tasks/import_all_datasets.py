import asyncio
from datetime import datetime
import time

from backend.config import setup_logging, get_logger
from backend.db.db import SessionLocal
from backend.deps import LONDON, STATIC_DATA_DIR
from backend.models import DataSource
from backend.tasks import import_nptg, import_naptan, import_holidays
from backend.tasks.import_txc_new import import_datasource, Statistics

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
    start = time.time()
    full_stats = Statistics()
    with SessionLocal() as db:
        datasource_ids = [id[0] for id in db.query(DataSource.id).all()]
    for id in datasource_ids:
        stats = await import_datasource(id, STATIC_DATA_DIR)

        if stats:
            full_stats += stats

    log.debug("dataset import complete.")
    import_time = time.time() - start
    log_dir = STATIC_DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "full_import.log"
    with log_file.open("w") as f:
        f.write(
            f"Full import statistics ({datetime.now(tz=LONDON).strftime('%d/%m/%Y, %H:%M:%S')}):\n"
        )

        for k, v in full_stats.__dict__.items():
            f.write(f"{k}: {v}\n")

        f.write(f"Total import time: {import_time:.2f} seconds\n")


if __name__ == "__main__":
    setup_logging()
    # asyncio.run(import_weekly_data())
    asyncio.run(import_datasets())
