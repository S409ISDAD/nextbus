from backend.tasks.import_holidays import import_bank_holidays
from backend.tasks.import_txc import import_txc_zip, TXCImporter
from backend.tasks.import_naptan import import_naptan_data


import_naptan_data("NaPTAN.xml")
# import_naptan_data("190.xml")
print("✔ NAPTAN data imported successfully")
# txc_importer = TXCImporter("test_txc.xml")
# txc_importer.handle_txc_file()
import_txc_zip("scso_all.zip")
print("✔ TXC data imported successfully")
import_bank_holidays()
print("✔ Bank holidays imported successfully")
