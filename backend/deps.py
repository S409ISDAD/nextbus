from datetime import datetime, timedelta, timezone
import json
from backend.config import get_logger
import pathlib
from redis.asyncio import Redis, ConnectionPool
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from zoneinfo import ZoneInfo
from pathlib import Path

UTC = timezone.utc
LONDON = ZoneInfo("Europe/London")

log = get_logger()


script_dir = pathlib.Path(__file__).resolve().parent
static_data_dir = script_dir / "../static_data"
STATIC_DATA_DIR = static_data_dir.resolve()  # normalize path


def get_version() -> str:
    try:
        return Path("/app/version.txt").read_text().strip()
    except FileNotFoundError:
        return "dev"


VERSION = get_version()

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


def get_redis_url() -> str:
    return os.getenv("REDIS_HOST", "redis://localhost:6379")


def get_redis_client() -> Redis:
    redis_host = get_redis_url()
    if not redis_host:
        log.debug(
            "Warning: REDIS_HOST environment variable not set. Using default 'localhost:6379'."
        )
        return Redis(host="localhost", port=6379, db=0, decode_responses=True)

    else:
        return Redis.from_url(redis_host, decode_responses=True)


async def get_redis() -> Redis:
    global _redis_pool, _redis_client

    if _redis_client is None:
        redis_url = get_redis_url()
        _redis_pool = ConnectionPool.from_url(redis_url, decode_responses=True)
        _redis_client = Redis(connection_pool=_redis_pool)
    return _redis_client


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
