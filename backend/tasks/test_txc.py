from backend.deps import STATIC_DATA_DIR
from backend.transxchange.transxchange_parser.txc import TransXChange
from backend.utils.time_taken import time_taken

file = STATIC_DATA_DIR / "64_txc.xml"

with time_taken():
    txc = TransXChange(file)

for service in txc.services.values():
    print(service.service_code)
    for line in service.lines:
        print(line.line_name)

        journeys = txc.get_journeys(service.service_code, line.id)

        print(f"Journeys: {len(journeys)}")
