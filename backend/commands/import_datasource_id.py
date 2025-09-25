import asyncio
import sys
from backend.config import get_logger, setup_logging
from backend.tasks.import_txc_new import import_datasource
from backend.deps import STATIC_DATA_DIR

log = get_logger(__name__)

if __name__ == "__main__":
    setup_logging()
    if len(sys.argv) != 2:
        log.debug("Usage: python import_datasource_id.py <ds_id>")
        exit(1)
    id = sys.argv[1]
    asyncio.run(import_datasource(id, STATIC_DATA_DIR))
