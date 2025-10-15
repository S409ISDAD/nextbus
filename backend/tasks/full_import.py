import asyncio
from backend.deps import STATIC_DATA_DIR
from backend.tasks.import_holidays import import_bank_holidays
from backend.tasks.import_txc import import_datasource
from backend.db.db import SessionLocal
from backend.models import DataSource

from backend.deps import get_logger

log = get_logger(__name__)


async def do_import():
    # Always resolve static_data relative to this script

    # import_naptan_data(static_data_dir / "NaPTAN.xml")
    # log.debug("✔ NAPTAN data imported successfully")

    scso_url = "https://opendata.stagecoachbus.com/stagecoach-scso-route-schedule-data-transxchange_2_4.zip"

    with SessionLocal() as db:
        datasource = (
            db.query(DataSource).filter(DataSource.name == "Stagecoach South").first()
        )
        if not datasource:
            datasource = DataSource(name="Stagecoach South", url=scso_url)
            db.add(datasource)
            db.commit()
            db.refresh(datasource)
        else:
            datasource.url = str(scso_url)  # type: ignore
            db.commit()
        datasource_id = datasource.id

    await import_datasource(datasource_id, STATIC_DATA_DIR)
    log.debug("✔ TXC data imported successfully")

    import_bank_holidays()
    log.debug("✔ Bank holidays imported successfully")
    log.debug("✔ Full import completed successfully")


if __name__ == "__main__":
    asyncio.run(do_import())
