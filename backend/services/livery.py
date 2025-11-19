from backend.config import API_BASE
from backend.schemas.livery import Livery
from backend.services.caching import LIVERY_CACHE, get_cached
from backend.utils.fetch_json import fetch_json

from backend.deps import get_logger

log = get_logger(__name__)


def get_livery(id: int, r):
    def fetch(id: int):
        data = fetch_json(
            API_BASE + f"/liveries/{id}",
        )

        if data:
            return {
                "id": id,
                "name": data.get("name"),
                "left_css": data.get("left_css"),
                "right_css": data.get("right_css"),
            }

    livery = get_cached(
        key=f"liveries:{id}",
        func=fetch,
        args=(id,),
        exp=LIVERY_CACHE,
        r=r,
    )

    if not livery:
        return None

    if livery.get("css"):
        livery["left_css"] = livery["css"]
        livery["right_css"] = livery["css"]
        del livery["css"]

    return Livery(**livery) if livery else None
