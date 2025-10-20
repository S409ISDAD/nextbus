from datetime import datetime
from pathlib import Path
from time import sleep
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from backend.config import get_logger
from backend.deps import LONDON
from backend.models import DataSource, DataSourceVersion
from backend.tasks.import_txc_new import Statistics, import_txc_zip
from backend.utils.download_if_modified import download_if_modified
from sqlalchemy.orm import Session
import requests

log = get_logger(__name__)


def scrape_passenger_versions(
    db: Session, datasource: DataSource
) -> list[DataSourceVersion]:
    versions = []

    try:
        response = requests.get(datasource.url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        log.warning(f"Failed to fetch {datasource.url}: {e}")
        sleep(5)
        return []

    soup = BeautifulSoup(response.text, "lxml")

    for heading in soup.find_all("h3"):
        heading_text = heading.get_text(strip=True)
        if " to " not in heading_text:
            continue

        date_text = heading_text.replace("Current Data (", "").replace(")", "")
        try:
            start_date, end_date = [d.strip() for d in date_text.split(" to ")]
        except ValueError:
            continue

        for sibling in heading.next_siblings:
            if not isinstance(sibling, Tag):
                continue

            link = sibling.find("a", string="Download TransXChange")
            if link and "/txc" in link.get("href", ""):
                url = urljoin(response.url, link["href"])
                version_obj = get_version(db, datasource, (start_date, end_date), url)
                versions.append(version_obj)
                break

    return sorted(versions, key=lambda x: x.start_date or "")


def get_version(
    db: Session, source: DataSource, date_range: tuple[str, str], url: str
) -> DataSourceVersion:
    start_date_str, end_date_str = date_range
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    version = (
        db.query(DataSourceVersion)
        .filter(
            DataSourceVersion.data_source_id == source.id,
            DataSourceVersion.start_date == start_date,
            DataSourceVersion.end_date == end_date,
        )
        .first()
    )

    if not version:
        version = DataSourceVersion(
            data_source_id=source.id,
            name=f"{source.name} {start_date_str} to {end_date_str}",
            description=f"Passenger data from {start_date_str} to {end_date_str}",
            start_date=start_date,
            end_date=end_date,
            url=url,
        )
        db.add(version)
        db.commit()
        db.refresh(version)
    else:
        version.url = url
        db.commit()
        db.refresh(version)

    return version


async def handle_passenger(
    db: Session,
    datasource: DataSource,
    folder: Path,
    skip_checks: bool,
):
    duration = None
    stats = Statistics()

    versions = scrape_passenger_versions(db, datasource)
    if not versions:
        log.debug(f"No versions found for Passenger datasource {datasource.name}")
        return duration, stats

    start = time.time()
    for version in versions:
        version.imported_at = datetime.now(tz=LONDON)
        passenger_folder = folder / "passenger"
        passenger_folder.mkdir(parents=True, exist_ok=True)
        filename = passenger_folder / f"passenger_{version.id}.zip"

        path = download_if_modified(version, filename, skip_checks)

        if path:
            log.debug(
                f"Importing Passenger data ({version.start_date} - {version.end_date}) from {path}..."
            )
            _, stats = await import_txc_zip(
                filename, datasource.id, version.id, skip_checks=skip_checks
            )
            stats += stats
        else:
            log.debug(
                f"No updates for {version.data_source.name} Passenger data ({version.start_date} - {version.end_date})"
            )

    current_ids = [v.id for v in versions]

    old_versions = (
        db.query(DataSourceVersion)
        .filter(
            DataSourceVersion.id.notin_(current_ids),
            DataSourceVersion.data_source_id == datasource.id,
        )
        .all()
    )
    for v in old_versions:
        log.debug(f"deleting Passenger version {v.id} ({v.start_date} - {v.end_date})")
        db.delete(v)
    db.commit()

    time_taken = time.time() - start

    duration = ""
    if time_taken >= 3600:
        hours = int(time_taken // 3600)
        minutes = int((time_taken % 3600) // 60)
        duration = f"{hours}h {minutes}m"
    elif time_taken >= 60:
        minutes = int(time_taken // 60)
        seconds = int(time_taken % 60)
        duration = f"{minutes}m {seconds}s"
    else:
        duration = f"{int(time_taken)}s"

    return duration, stats
