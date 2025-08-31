import asyncio
import os
import pathlib
from backend.tasks.import_holidays import import_bank_holidays
from backend.tasks.import_txc import import_txc_zip, TXCImporter
from backend.tasks.import_naptan import import_naptan_data


async def do_import():
    # Always resolve static_data relative to this script
    script_dir = pathlib.Path(__file__).resolve().parent
    static_data_dir = script_dir / "../../static_data"
    static_data_dir = static_data_dir.resolve()  # normalize path

    # Example imports
    import_naptan_data(static_data_dir / "190.xml")
    print("✔ NAPTAN data imported successfully")

    for txc_file in ["64_txc.xml", "67_txc.xml"]:
        txc_importer = TXCImporter(static_data_dir / txc_file)
        await txc_importer.handle_txc_file()
    print("✔ TXC data imported successfully")

    import_bank_holidays()
    print("✔ Bank holidays imported successfully")
    print("✔ Full import completed successfully")


if __name__ == "__main__":
    asyncio.run(do_import())
