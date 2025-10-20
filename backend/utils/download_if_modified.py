from datetime import datetime
import requests
from pathlib import Path
from backend.models import DataSourceVersion
from backend.db.db import SessionLocal
from backend.config import config
from dateutil.parser import isoparse

from backend.deps import get_logger

log = get_logger(__name__)


def download_if_modified(
    datasource_ver: DataSourceVersion, file: Path, skip_checks=False
) -> Path | None:
    try:
        if datasource_ver.bods_id is not None:  # is a bods source, use the api
            log.debug(f"Checking BODS source {datasource_ver.name}")
            if config.bods_api_key is None:
                raise ValueError("BODS API key not set in config")
            url = (
                "https://data.bus-data.dft.gov.uk/api/v1/dataset/"
                + str(datasource_ver.bods_id)
                + "?api_key="
                + config.bods_api_key
            )

            data = requests.get(url).json()
            download_url = data.get("url")
            modified = isoparse(data.get("modified"))

            if (
                datasource_ver.last_modified is not None
                and modified <= datasource_ver.last_modified
                and not skip_checks
            ):
                log.debug(f"data not modified: {datasource_ver.bods_id}")
                return None

            file_data = requests.get(download_url)

            with open(file, "wb") as f:
                f.write(file_data.content)
            log.debug(f"Downloaded updated file: {file}")

            with SessionLocal() as db:
                datasource_ver.last_modified = modified  # type: ignore
                db.merge(datasource_ver)
                db.commit()

            return file

        else:
            headers = {}
            if datasource_ver.last_modified is not None and not skip_checks:
                headers["If-Modified-Since"] = datasource_ver.last_modified.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            response = requests.get(str(datasource_ver.url), headers=headers)

            if response.status_code == 200:
                etag = response.headers.get("ETag")
                if etag is not None and datasource_ver.etag == etag and not skip_checks:
                    log.debug(f"data not modified (etag): {datasource_ver.url}")
                    return None

                with open(file, "wb") as f:
                    f.write(response.content)
                log.debug(f"Downloaded updated file: {file}")

                with SessionLocal() as db:
                    datasource_ver.last_modified = datetime.strptime(  # type: ignore
                        response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT"
                    )
                    datasource_ver.etag = etag
                    db.merge(datasource_ver)
                    db.commit()

                return file

            else:
                log.debug(
                    f"data not modified: {datasource_ver.url}, {response.headers['Last-Modified']}"
                )

            return None
    except Exception as e:
        log.error(f"Error downloading datasource version {datasource_ver.id}: {e}")
        return None
