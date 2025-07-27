import aiohttp
import ssl
import certifi
import os
from dotenv import load_dotenv

ssl_context = ssl.create_default_context(cafile=certifi.where())


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers={"Accept": "application/json"}, ssl=ssl_context
        ) as response:
            if response.status != 200:
                return None
            return await response.json()


# Load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


async def fetch_rtt_json(url: str):
    RTT_USERNAME = os.getenv("RTT_USERNAME", "YOUR_USERNAME")
    RTT_PASSWORD = os.getenv("RTT_PASSWORD", "YOUR_PASSWORD")
    auth = aiohttp.BasicAuth(RTT_USERNAME, RTT_PASSWORD)

    async with aiohttp.ClientSession(auth=auth) as session:
        async with session.get(
            url, headers={"Accept": "application/json"}, ssl=ssl_context
        ) as response:
            if response.status != 200:
                print(f"RTT API failed: {response.status}")
                return None
            return await response.json()
