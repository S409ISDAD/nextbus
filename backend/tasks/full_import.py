from backend.tasks.import_holidays import import_bank_holidays
from backend.tasks.import_txc import import_txc_zip, TXCImporter
from backend.tasks.import_naptan import import_naptan_data


# import_naptan_data("NaPTAN.xml")
import_naptan_data("static_data/190.xml")
print("✔ NAPTAN data imported successfully")
txc_importer = TXCImporter("static_data/64_txc.xml")
txc_importer.handle_txc_file()
txc_importer = TXCImporter("static_data/67_txc.xml")
txc_importer.handle_txc_file()
# import_txc_zip("scso_all.zip")
print("✔ TXC data imported successfully")
import_bank_holidays()
print("✔ Bank holidays imported successfully")
