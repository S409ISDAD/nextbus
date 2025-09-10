import asyncio
import pathlib
from backend.tasks.import_holidays import import_bank_holidays
from backend.tasks.import_txc import import_txc_zip, import_datasource
from backend.tasks.import_naptan import import_naptan_data
from backend.db.db import SessionLocal
from backend.models import DataSource


async def do_import():
    # Always resolve static_data relative to this script
    script_dir = pathlib.Path(__file__).resolve().parent
    static_data_dir = script_dir / "../../static_data"
    static_data_dir = static_data_dir.resolve()  # normalize path

    # import_naptan_data(static_data_dir / "NaPTAN.xml")
    # print("✔ NAPTAN data imported successfully")

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
            datasource.url = str(scso_url)
            db.commit()
        datasource_id = datasource.id

    await import_datasource(datasource_id, static_data_dir)
    print("✔ TXC data imported successfully")

    import_bank_holidays()
    print("✔ Bank holidays imported successfully")
    print("✔ Full import completed successfully")


if __name__ == "__main__":
    asyncio.run(do_import())
