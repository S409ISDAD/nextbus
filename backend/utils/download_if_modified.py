from datetime import datetime
from typing import Optional
import requests
from pathlib import Path
from backend.models import DataSource
from backend.db.db import SessionLocal


def download_if_modified(datasource: DataSource, file: Path):
    headers = {}
    if datasource.last_modified:
        headers["If-Modified-Since"] = datasource.last_modified.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

    response = requests.get(datasource.url, headers=headers)

    if response.status_code == 200:
        with open(file, "wb") as f:
            f.write(response.content)
        print(f"Downloaded updated file: {file}")

        with SessionLocal() as db:
            datasource.last_modified = datetime.strptime(
                response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT"
            )
            db.add(datasource)
            db.commit()

        return file

    return None
