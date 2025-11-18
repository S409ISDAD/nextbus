from datetime import datetime, timedelta, timezone
import json
from typing import Optional
from backend.config import get_logger
import pathlib
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from zoneinfo import ZoneInfo
from pathlib import Path

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis
from redis.connection import ConnectionPool

UTC = timezone.utc
LONDON = ZoneInfo("Europe/London")

log = get_logger(__name__)


script_dir = pathlib.Path(__file__).resolve().parent
static_data_dir = script_dir / "../static_data"
STATIC_DATA_DIR = static_data_dir.resolve()  # normalize path


def get_version() -> str:
    try:
        return Path("/app/version.txt").read_text().strip()
    except FileNotFoundError:
        return "dev"


VERSION = get_version()

_redis_sync: SyncRedis | None = None
_redis_async: AsyncRedis | None = None


def get_redis_url() -> str:
    return os.getenv("REDIS_HOST", "redis://localhost:6379")


# def get_redis_client() -> Redis:
#     redis_host = get_redis_url()
#     if not redis_host:
#         log.debug(
#             "Warning: REDIS_HOST environment variable not set. Using default 'localhost:6379'."
#         )
#         return Redis(host="localhost", port=6379, db=0, decode_responses=True)

#     else:
#         return Redis.from_url(redis_host, decode_responses=True)


def get_redis(sync: bool = True):
    global _redis_sync, _redis_async

    redis_url = get_redis_url()

    if sync:
        global _redis_sync
        if _redis_sync is None:
            _redis_sync = SyncRedis.from_url(redis_url, decode_responses=True)
        return _redis_sync
    else:
        global _redis_async
        if _redis_async is None:
            _redis_async = AsyncRedis.from_url(redis_url, decode_responses=True)
        return _redis_async


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_redis_url(),
    default_limits=["100/minute"],
)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return {"__datetime__": True, "iso": o.isoformat()}
        return super().default(o)


def datetime_decoder(obj):
    if "__datetime__" in obj:
        return datetime.fromisoformat(obj["iso"])
    return obj


def floor_to_30s(ts: datetime) -> datetime:
    ts = ts.replace(microsecond=0)
    return ts - timedelta(seconds=ts.second % 30)
