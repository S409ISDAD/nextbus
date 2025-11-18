import aiohttp
import ssl
import certifi
import os
from dotenv import load_dotenv
from backend.config import config

from backend.deps import get_logger
import requests

log = get_logger(__name__)

load_dotenv()

ssl_context = ssl.create_default_context(cafile=certifi.where())

RTT_USERNAME = os.getenv("RTT_USERNAME", "abc")
RTT_PASSWORD = os.getenv("RTT_PASSWORD", "abc")
ENVIRONMENT = config.env

if ENVIRONMENT == "production":
    if not RTT_USERNAME or not RTT_PASSWORD:
        raise RuntimeError("RTT_USERNAME and RTT_PASSWORD must be set")
auth = aiohttp.BasicAuth(RTT_USERNAME, RTT_PASSWORD)


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


def fetch_rtt_json(url: str) -> dict | None:
    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json", "User-Agent": "nextbus/1.0"},
            auth=(RTT_USERNAME, RTT_PASSWORD),
            timeout=timeout.total,
            verify=certifi.where(),
        )
        json_data = response.json()
        if response.status_code != 200 or "error" in json_data:
            log.error(f"RTT API failed: {response.status_code}")
            log.error(url)
            log.error(json_data)
            return None
        return json_data
    except Exception as e:
        log.error(f"Exception during fetch_rtt_json: {e}")
        return None
