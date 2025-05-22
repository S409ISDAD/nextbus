from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.routes import departures
from backend.deps import get_redis_client
import logging


log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis = get_redis_client()
        if await redis.ping():
            log.info("Redis Connected.")
        else:
            log.warning("Redis did not respond.")
        await redis.close()

    except Exception as e:
        log.error(f"Redis connection failed: {e}")

    yield


origins = [
    "http://localhost:5173",
    "http://localhost",
]

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(departures.router, prefix="/api/v1/departures")
