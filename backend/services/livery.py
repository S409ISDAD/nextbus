from backend.config import API_BASE
from backend.schemas.livery import Livery
from backend.services.caching import LIVERY_CACHE, get_cached
from backend.utils.fetch_json import fetch_json
import logging

log = logging.getLogger(__name__)


async def get_livery(id: int, r):
    async def fetch(id: int):
        data = await fetch_json(
            API_BASE + f"/liveries/{id}",
        )

        if data:
            return {
                "name": data.get("name"),
                "left_css": data.get("left_css"),
                "right_css": data.get("right_css"),
            }

    livery = await get_cached(
        key=f"liveries:{id}",
        func=fetch,
        args=(id,),
        exp=LIVERY_CACHE,
        r=r,
    )

    if livery.get("css"):
        livery["left_css"] = livery["css"]
        livery["right_css"] = livery["css"]
        del livery["css"]

    return Livery(**livery) if livery else None
