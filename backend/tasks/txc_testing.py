import logging

from backend.deps import STATIC_DATA_DIR
from backend.transxchange.txc import TransXChange
from backend.utils.time_taken import time_taken

log = logging.getLogger(__name__)

file = STATIC_DATA_DIR / "64_txc.xml"

with time_taken():
    txc = TransXChange(file)

for service in txc.services.values():
    log.debug(service.service_code)
    for line in service.lines:
        log.debug(line.line_name)

        journeys = txc.get_journeys(service.service_code, line.id)

        log.debug(f"Journeys: {len(journeys)}")
