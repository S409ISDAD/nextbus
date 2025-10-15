import xml.etree.ElementTree as ET

import requests
from sqlalchemy_searchable import sync_trigger

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal, engine

log = get_logger(__name__)


def get_mode(mode):
    """
    from bustimes.org import_noc.py
    """
    if not mode.isupper():
        mode = mode.lower()
    match mode:
        case "ct operator" | "ct operaor" | "CT":
            return "community transport"
        case "DRT":
            return "demand responsive transport"
        case "partly drt":
            return "partly DRT"
    return mode


def import_noc_data():
    log.debug("Importing NOC data...")
    with SessionLocal() as db:
        try:
            url = "https://www.travelinedata.org.uk/noc/api/1.0/nocrecords.xml"

            file = requests.get(url)

            element = ET.fromstring(file.text)

            public_names = {}
            for e in element.find("PublicName"):
                e_id = e.findtext("PubNmId")
                assert e_id not in public_names
                public_names[e_id] = e

            noc_lines = {
                line.findtext("NOCCODE").removeprefix("="): line
                for line in element.find("NOCLines")
            }


            for e in element.find("NOCTable"):
                noc = e.findtext("NOCCODE").removeprefix("=")

                if noc in noc_lines:
                    noc_line = noc_lines[noc]
                else:
                    continue

                vehicle_mode = get_mode(noc_line.findtext("Mode"))
                if vehicle_mode == "airline":
                    log.debug(f"Skipping airline NOC {noc}")
                    continue

                public_name = public_names[e.findtext("PubNmId")]

                name = public_name.findtext("OperatorPublicName")

                log.debug(f"Processing NOC {noc} - {name} ({vehicle_mode})")

            log.debug("Committing...")
            db.commit()
            log.debug("Import complete")
            log.debug("Syncing search vectors")
            with engine.begin() as conn:
                sync_trigger(
                    conn,
                    "operator",
                    "search_vector",
                    [
                        "noc",
                        "name",
                    ],
                )
        except Exception as e:
            log.debug(f"Error during import: {e}")
            db.rollback()


def main():
    setup_logging()
    try:
        import_noc_data()
    except KeyboardInterrupt:
        log.debug("Stopped by user.")


if __name__ == "__main__":
    main()
