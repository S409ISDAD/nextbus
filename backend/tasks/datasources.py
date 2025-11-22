from datetime import datetime
from pathlib import Path
from backend.config import get_logger
from backend.db.db import SessionLocal
from backend.deps import LONDON
from backend.models import DataSource, DataSourceVersion
from backend.tasks.import_txc_new import Statistics, import_txc_zip
from backend.tasks.import_bods import handle_bods
from backend.tasks.import_passenger import handle_passenger
from backend.utils.download_if_modified import download_if_modified

log = get_logger(__name__)


def import_datasource(id, folder: Path, skip_checks=False) -> "Statistics":
    logs: list[tuple[datetime, str]] = []
    stats = Statistics()
    duration = None
    with SessionLocal() as db:
        datasource = db.query(DataSource).filter(DataSource.id == id).first()
        name = datasource.name if datasource else "Unknown"

        if not datasource:
            log.debug(f"No DataSource with id {id} found.")
            logs.append((datetime.now(tz=LONDON), f"No DataSource with id {id} found."))
            return stats

        if datasource.disabled:
            log.debug(f"DataSource {name} is disabled, skipping import.")
            logs.append(
                (
                    datetime.now(tz=LONDON),
                    f"DataSource {name} is disabled, skipping import.",
                )
            )
            return stats

        logs.append(
            (
                datetime.now(tz=LONDON),
                f"Trying to import data source {name} from {datasource.url or datasource.noc or datasource.search}...",
            )
        )

        if datasource.url and (
            "data.discoverpassenger" in datasource.url or "open-data" in datasource.url
        ):
            log.debug(f"Handling Passenger datasource {datasource.name}")
            duration, stats = handle_passenger(db, datasource, folder, skip_checks)

        elif datasource.search or datasource.noc:
            log.debug(f"Handling BODS datasource {datasource.name}")
            duration, stats = handle_bods(db, datasource, folder, skip_checks)
            if not duration:
                logs.append(
                    (datetime.now(tz=LONDON), f"No updates for data source {name}")
                )
                log.debug(f"No updates for data source {name}")

        else:
            log.debug(f"Handling url datasource {datasource.name}")
            datasource_version = (
                db.query(DataSourceVersion)
                .filter(DataSourceVersion.url == datasource.url)
                .first()
            )

            if not datasource_version:
                datasource_version = DataSourceVersion(
                    data_source_id=datasource.id,
                    name=datasource.name,
                    url=datasource.url,
                )
                db.add(datasource_version)
                db.commit()
                db.refresh(datasource_version)

            datasource_version.imported_at = datetime.now(tz=LONDON)
            path = download_if_modified(
                datasource_version, folder / f"txc_source_{id}.zip", skip_checks
            )

            if path:
                logs.append((datetime.now(tz=LONDON), f"Importing data from {path}..."))
                log.debug(f"Importing data from {path}")

                duration, stats = import_txc_zip(
                    folder / f"txc_source_{id}.zip",
                    id,
                    datasource_version.id,
                    skip_checks,
                )
            else:
                logs.append(
                    (datetime.now(tz=LONDON), f"No updates for data source {name}")
                )
                log.debug(f"No updates for data source {name}")

    logs.append(
        (
            datetime.now(tz=LONDON),
            f"Import completed for data source {name}"
            + (f" in {duration}" if duration else ""),
        )
    )
    log.debug(
        f"Import completed for data source {name}"
        + (f" in {duration}" if duration else "")
    )
    if stats:
        for item in stats.output():
            logs.append((datetime.now(tz=LONDON), item))

    log_dir = folder / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"import_log_{id}.log"

    log_file.touch()

    with log_file.open("w") as f:
        for txc_log in logs:
            f.write(f"{txc_log[0].strftime('%d/%m/%Y, %H:%M:%S')} - {txc_log[1]}\n")

    return stats
