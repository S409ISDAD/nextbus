import aiohttp
import ssl
import certifi
import os
from dotenv import load_dotenv
from backend.config import config

from backend.deps import get_logger

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


async def fetch_json(url) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers={"Accept": "application/json", "User-Agent": "nextbus/1.0"},
            ssl=ssl_context,
            timeout=timeout,
        ) as response:
            if response.status != 200:
                log.error(f"API failed: {response.status} for URL {url}")
                return None
            return await response.json()


async def fetch_rtt_json(url: str) -> dict | None:
    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(
            url,
            headers={"Accept": "application/json", "User-Agent": "nextbus/1.0"},
            ssl=ssl_context,
            timeout=timeout,
        ) as response:
            if response.status != 200 or "error" in (await response.json()):
                log.error(f"RTT API failed: {response.status}")
                log.error(url)
                log.error(await response.json())
                return None
            return await response.json()
