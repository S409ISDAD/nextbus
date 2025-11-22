import xml.etree.ElementTree as ET

import requests
from sqlalchemy_searchable import sync_trigger
from sqlalchemy.orm import joinedload
from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal, engine
from backend.models import Operator, OperatorCode
from backend.utils.bulk_upsert import bulk_upsert
from slugify import slugify

log = get_logger(__name__)

CODE_SOURCES = ["LO", "SW", "WM", "WA", "YO", "NW", "NE", "SC", "SE", "EA", "EM"]


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


def get_op_codes(noc, operator_id, noc_line):
    codes = [(operator_id, noc)]
    op_codes = [OperatorCode(code=noc, operator_id=operator_id)]

    for source in CODE_SOURCES:
        code = noc_line.find(source).text

        if code:
            code = code.removeprefix("=")
            if code != noc:
                key = (operator_id, code)
                if key not in codes:
                    codes.append(key)
                    op_codes.append(OperatorCode(code=code, operator_id=operator_id))

    return op_codes, set(codes)


def import_noc_data():
    log.debug("Importing NOC data...")
    with SessionLocal() as db:
        try:
            url = "https://www.travelinedata.org.uk/noc/api/1.0/nocrecords.xml"
            file = requests.get(url)
            element = ET.fromstring(file.text)

            operators = db.query(Operator).options(joinedload(Operator.codes)).all()
            operator_dict = {op.noc: op for op in operators}
            existing_op_codes = set(
                (code.operator_id, code.code) for code in db.query(OperatorCode).all()
            )

            operators_by_slug = {op.slug: op for op in operators}

            to_add_operators = []
            to_update_operators = []
            op_codes_to_add = []

            merged_op_codes = {
                code.code: code
                for operator in operators
                for code in operator.codes
                if code.code != operator.noc
            }

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
                if noc not in noc_lines:
                    continue

                noc_line = noc_lines[noc]
                operator = operator_dict.get(noc)
                public_name = public_names[e.findtext("PubNmId")]
                name = public_name.findtext("OperatorPublicName")
                vehicle_mode = get_mode(noc_line.findtext("Mode"))

                if noc in merged_op_codes:
                    continue

                if vehicle_mode == "airline":
                    log.debug(f"Skipping airline NOC {noc} - {name}")
                    continue

                if not operator:
                    # new operator
                    operator = Operator(noc=noc, name=name, mode=vehicle_mode)
                    slug = slugify(name)
                    if slug in operators_by_slug:
                        to_update_operators.append(operator)
                    else:
                        operator.slug = slug
                        to_add_operators.append(operator)
                    operator_dict[noc] = operator
                    operators_by_slug[slug] = operator
                    db.add(operator)
                    db.flush()  # ensure ID is available

                else:
                    # existing operator, update if needed
                    if operator.name != name or operator.mode != vehicle_mode:
                        operator.name = name
                        operator.mode = vehicle_mode
                        to_update_operators.append(operator)

                # generate operator codes
                generated_codes, generated_keys = get_op_codes(
                    noc, operator.id, noc_line
                )
                new_codes = [
                    c
                    for c, key in zip(generated_codes, generated_keys)
                    if key not in existing_op_codes
                ]
                op_codes_to_add.extend(new_codes)
                existing_op_codes.update((c.operator_id, c.code) for c in new_codes)

            if to_update_operators:
                db.bulk_save_objects(to_update_operators)
            if to_add_operators:
                db.bulk_save_objects(to_add_operators)
            if op_codes_to_add:
                db.bulk_save_objects(op_codes_to_add)

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
