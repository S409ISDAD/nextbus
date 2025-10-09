from datetime import datetime
import requests
from pathlib import Path
from backend.models import DataSource
from backend.db.db import SessionLocal
from backend.config import config
from dateutil.parser import isoparse
import logging

log = logging.getLogger(__name__)


def download_if_modified(
    datasource: DataSource, file: Path, skip_checks=False
) -> Path | None:
    try:
        if datasource.bods_id is not None:  # is a bods source, use the api
            log.debug(f"Checking BODS source {datasource.name}")
            if config.bods_api_key is None:
                raise ValueError("BODS API key not set in config")
            url = (
                "https://data.bus-data.dft.gov.uk/api/v1/dataset/"
                + str(datasource.bods_id)
                + "?api_key="
                + config.bods_api_key
            )

            data = requests.get(url).json()
            download_url = data.get("url")
            modified = isoparse(data.get("modified"))

            if (
                datasource.last_modified is not None
                and modified <= datasource.last_modified
                and not skip_checks
            ):
                log.debug(f"data not modified: {datasource.bods_id}")
                return None

            file_data = requests.get(download_url)

            with open(file, "wb") as f:
                f.write(file_data.content)
            log.debug(f"Downloaded updated file: {file}")

            with SessionLocal() as db:
                datasource.last_modified = modified  # type: ignore
                db.merge(datasource)
                db.commit()

            return file

        else:
            headers = {}
            if datasource.last_modified is not None and not skip_checks:
                headers["If-Modified-Since"] = datasource.last_modified.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            response = requests.get(str(datasource.url), headers=headers)

            if response.status_code == 200:
                with open(file, "wb") as f:
                    f.write(response.content)
                log.debug(f"Downloaded updated file: {file}")

                with SessionLocal() as db:
                    datasource.last_modified = datetime.strptime(  # type: ignore
                        response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT"
                    )
                    db.merge(datasource)
                    db.commit()

                return file

            else:
                log.debug(
                    f"data not modified: {datasource.url}, {response.headers['Last-Modified']}"
                )

            return None
    except Exception as e:
        log.error(f"Error downloading datasource {datasource.name}: {e}")
        return None
