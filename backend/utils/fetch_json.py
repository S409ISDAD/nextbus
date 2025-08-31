import aiohttp
import ssl
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

ssl_context = ssl.create_default_context(cafile=certifi.where())

RTT_USERNAME = os.getenv("RTT_USERNAME")
RTT_PASSWORD = os.getenv("RTT_PASSWORD")

if not RTT_USERNAME or not RTT_PASSWORD:
    raise RuntimeError("RTT_USERNAME and RTT_PASSWORD must be set")
auth = aiohttp.BasicAuth(RTT_USERNAME, RTT_PASSWORD)


async def fetch_json(url) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers={"Accept": "application/json"}, ssl=ssl_context
        ) as response:
            if response.status != 200:
                return None
            return await response.json()


async def fetch_rtt_json(url: str) -> dict | None:
    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(
            url, headers={"Accept": "application/json"}, ssl=ssl_context
        ) as response:
            if response.status != 200 or "error" in (await response.json()):
                print(f"RTT API failed: {response.status}")
                print(url)
                print(await response.json())
                return None
            return await response.json()
