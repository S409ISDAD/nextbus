import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.routes import departures, location, stops, buses, livery
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
    "http://localhost:3000",
]

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.method} {request.url} completed in {duration:.3f}s")
    return response


app.include_router(departures.router, prefix="/api/v1/departures")
app.include_router(location.router, prefix="/api/v1/location")
app.include_router(stops.router, prefix="/api/v1/stops")
app.include_router(buses.router, prefix="/api/v1/buses")
app.include_router(livery.router, prefix="/api/v1/liveries")
