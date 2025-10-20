from datetime import datetime
from pathlib import Path
from backend.config import get_logger, config
from backend.deps import LONDON
from backend.models import DataSource, DataSourceVersion
from backend.tasks.import_txc_new import Statistics, import_txc_zip
from backend.utils.download_if_modified import download_if_modified
from dateutil.parser import isoparse
from sqlalchemy.orm import Session
import requests

log = get_logger(__name__)


async def handle_bods(
    db: Session,
    datasource: DataSource,
    folder: Path,
    skip_checks: bool,
):
    duration = None
    stats = Statistics()
    if not config.bods_api_key:
        log.error("BODS API key not configured.")
        return

    bods_api = "https://data.bus-data.dft.gov.uk/api/v1/dataset?limit=1&offset=0"

    if datasource.noc:
        bods_api += f"&noc={datasource.noc}"
    if datasource.search:
        bods_api += f"&search={datasource.search}"
    bods_api += f"&status=published&api_key={config.bods_api_key}"

    response = requests.get(bods_api)
    data = response.json()

    if data["count"] == 0:
        log.debug(f"No BODS dataset found for datasource {datasource.name}")
        return
    dataset = data["results"][0]

    id = dataset["id"]
    name = dataset["name"]
    description = dataset.get("description", "")
    modified = dataset["modified"]

    start_date = (
        isoparse(dataset.get("firstStartDate")).date()
        if dataset.get("firstStartDate")
        else None
    )
    end_date = (
        isoparse(dataset.get("lastEndDate")).date()
        if dataset.get("lastEndDate")
        else None
    )

    version = (
        db.query(DataSourceVersion).filter(DataSourceVersion.bods_id == id).first()
    )

    if not version:
        version = DataSourceVersion(
            data_source_id=datasource.id,
            name=name,
            description=description,
            start_date=start_date or datetime.now(tz=LONDON).date(),
            end_date=end_date,
            bods_id=id,
        )
        db.add(version)
        db.commit()
        db.refresh(version)

    version.imported_at = datetime.now(tz=LONDON)

    bods_folder = folder / "bods"
    bods_folder.mkdir(parents=True, exist_ok=True)

    filename = bods_folder / f"bods_{id}.zip"

    path = download_if_modified(version, filename, skip_checks)

    if path:
        log.info(f"Importing BODS {id} data from {path}...")
        duration, stats = await import_txc_zip(
            filename, datasource.id, version.id, skip_checks
        )
    else:
        log.debug(f"No updates for BODS dataset {version.name} - {id}")

    return duration, stats
