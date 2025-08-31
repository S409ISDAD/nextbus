from backend.tasks.import_holidays import import_bank_holidays
from backend.tasks.import_txc import import_txc_zip, TXCImporter
from backend.tasks.import_naptan import import_naptan_data
import os
import pathlib


def do_import():
    project_root = pathlib.Path(__file__).resolve()
    while project_root.name != "nextbus":
        if project_root.parent == project_root:
            raise RuntimeError("Could not find 'nextbus' root directory.")
        project_root = project_root.parent
    static_data_dir = project_root / "static_data"

    # import_naptan_data("NaPTAN.xml")
    import_naptan_data(os.path.join(static_data_dir, "190.xml"))
    print("✔ NAPTAN data imported successfully")
    txc_importer = TXCImporter(os.path.join(static_data_dir, "64_txc.xml"))
    txc_importer.handle_txc_file()
    txc_importer = TXCImporter(os.path.join(static_data_dir, "67_txc.xml"))
    txc_importer.handle_txc_file()
    # import_txc_zip(os.path.join(static_data_dir, "scso_all.zip"))
    print("✔ TXC data imported successfully")
    import_bank_holidays()
    print("✔ Bank holidays imported successfully")
    print("✔ Full import completed successfully")


if __name__ == "__main__":
    do_import()
