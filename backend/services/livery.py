from backend.config import API_BASE
from backend.models.livery import Livery
from backend.services.caching import LIVERY_CACHE, get_cached
from backend.utils.fetch_json import fetch_json


async def get_livery(id: int, r):
    async def fetch(id: int):
        data = await fetch_json(
            API_BASE + f"/liveries/{id}",
        )

        if data:
            return {"name": data.get("name"), "css": data.get("left_css")}

    livery = await get_cached(
        key=f"liveries:{id}",
        func=lambda *args: fetch(*args),
        args=(id,),
        exp=LIVERY_CACHE,
        r=r,
    )

    return Livery(name=livery.get("name"), css=livery.get("css"))
