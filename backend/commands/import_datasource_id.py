import argparse
from backend.config import get_logger, setup_logging
from backend.tasks.datasources import import_datasource
from backend.deps import STATIC_DATA_DIR

log = get_logger(__name__)

if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="Import datasource by id.")
    parser.add_argument("id", nargs="?", help="ID of the datasource to import")
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Do not exit on conflict, e.g. same file hash",
    )
    args = parser.parse_args()
    id = args.id
    skip_checks = args.skip_checks
    import_datasource(id, STATIC_DATA_DIR, skip_checks=skip_checks)
