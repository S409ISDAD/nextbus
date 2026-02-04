import aiohttp
import certifi

from backend.deps import get_logger
import requests

log = get_logger(__name__)


timeout = aiohttp.ClientTimeout(total=20)


def fetch_json(url) -> dict | None:
    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json", "User-Agent": "nextbus/1.0"},
            timeout=timeout.total,
            verify=certifi.where(),
        )
        if response.status_code != 200:
            log.error(f"API failed: {response.status_code} for URL {url}")
            return None
        return response.json()
    except Exception as e:
        log.error(f"Exception during fetch_json: {e}")
        return None
