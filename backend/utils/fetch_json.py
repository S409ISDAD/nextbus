import aiohttp


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"Accept": "application/json"}) as response:
            if response.status != 200:
                return None
            return await response.json()
