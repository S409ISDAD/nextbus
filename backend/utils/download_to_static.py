
import requests

from backend.deps import STATIC_DATA_DIR

from backend.deps import get_logger

log = get_logger(__name__)


def download_to_static(url: str, filename: str):
    path = STATIC_DATA_DIR / filename

    response = requests.get(url, stream=True)

    if response.status_code == 200:
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=102400):
                f.write(chunk)
        log.debug(f"Downloaded updated file: {path}")

        return path
    return None
