import time
from contextlib import asynccontextmanager

import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from backend.api.routes import (
    departures,
    lines,
    location,
    search,
    stats,
    stops,
    services,
    buses,
    livery,
    trains,
    journey_planning,
    places,
    timetable,
    sources,
    journeys,
)
from backend.config import config, setup_logging
from backend.db.db import get_db
from backend.deps import (
    get_redis,
    limiter,
    VERSION,
)
from backend.websockets.routes import ws_router
from backend.deps import get_logger

setup_logging()

log = get_logger(__name__)


def clear_redis_stats(redis):
    log.debug("Clearing Redis stats...")
    redis.delete("total_buses")
    redis.delete("total_stops")


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = get_redis()
    if redis.ping():
        log.info("Redis Connected.")
    else:
        log.warning("Redis did not respond.")

    is_leader = redis.set("app:leader", "1", nx=True, ex=60)
    if is_leader:
        log.debug("This instance is the leader.")
    else:
        log.debug("This instance is not the leader.")

    scheduler = None
    if is_leader:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            clear_redis_stats,
            CronTrigger(hour="0", minute="0", second="0"),  # daily at midnight
            id="clear_redis_stats",
            replace_existing=True,
            args=[redis],
        )
        scheduler.start()
    else:
        scheduler = None
    log.info("App startup complete.")

    try:
        yield
    finally:
        if is_leader:
            redis.delete("app:leader")
        if scheduler:
            scheduler.shutdown(wait=False)
        redis.close()


# if config.env != "development":
sentry_sdk.init(
    dsn="https://3da698c3793790b5233cb0a4a72d017f@o4509935722889216.ingest.de.sentry.io/4509935731277904",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    integrations=[
        SqlalchemyIntegration(),
    ],
    environment=config.env,
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=0.2,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=0.1,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)

log.info(f"running in {config.env} mode")
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
    log.debug(f"{request.method} {request.url} completed in {duration:.3f}s")
    response.headers["X-Version"] = VERSION
    return response


@app.get("/api/v1/health/")
def health_check(db: Session = Depends(get_db), redis=Depends(get_redis)):
    try:
        # Simple test query
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        redis.ping()
        return {"status": "healthy"}
    except Exception:
        return {"status": "degraded"}


app.include_router(ws_router)
app.include_router(departures.router, prefix="/api/v1/departures")
app.include_router(location.router, prefix="/api/v1/location")
app.include_router(stops.router, prefix="/api/v1/stops")
app.include_router(services.router, prefix="/api/v1/services")
app.include_router(buses.router, prefix="/api/v1/buses")
app.include_router(livery.router, prefix="/api/v1/liveries")
app.include_router(trains.router, prefix="/api/v1/trains")
app.include_router(lines.router, prefix="/api/v1/lines")
app.include_router(stats.router, prefix="/api/v1/stats")
app.include_router(search.router, prefix="/api/v1/search")
app.include_router(journey_planning.router, prefix="/api/v1/planning")
app.include_router(places.router, prefix="/api/v1/places")
app.include_router(timetable.router, prefix="/api/v1/timetable")
app.include_router(sources.router, prefix="/api/v1/sources")
app.include_router(journeys.router, prefix="/api/v1/journeys")
