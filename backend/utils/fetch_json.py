import aiohttp
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers={"Accept": "application/json"}, ssl=ssl_context
        ) as response:
            if response.status != 200:
                return None
            return await response.json()
