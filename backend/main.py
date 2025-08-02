import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.routes import (
    departures,
    location,
    stops,
    services,
    buses,
    livery,
    trains,
)
from backend.websockets.routes import ws_router
from backend.deps import get_redis_client, limiter
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


log = logging.getLogger(__name__)


# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     datefmt="%H:%M:%S",
# )


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


app = FastAPI(lifespan=lifespan, redirect_slashes=False)

Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.router.redirect_slashes = False


app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: _rate_limit_exceeded_handler(request, exc),  # type: ignore
)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.method} {request.url} completed in {duration:.3f}s")
    return response


app.include_router(ws_router)
app.include_router(departures.router, prefix="/api/v1/departures")
app.include_router(location.router, prefix="/api/v1/location")
app.include_router(stops.router, prefix="/api/v1/stops")
app.include_router(services.router, prefix="/api/v1/services")
app.include_router(buses.router, prefix="/api/v1/buses")
app.include_router(livery.router, prefix="/api/v1/liveries")
app.include_router(trains.router, prefix="/api/v1/trains")
