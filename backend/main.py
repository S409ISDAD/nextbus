import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import timedelta, timezone, datetime

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
)
from backend.config import config
from backend.db.db import SessionLocal, get_db
from backend.deps import (
    floor_to_30s,
    get_redis_client,
    get_redis,
    limiter,
    VERSION,
)
from backend.models import ActiveUsersSnapshot
from backend.tasks.import_all_datasets import import_datasets, import_weekly_data
from backend.websockets.routes import ws_router

log = logging.getLogger(__name__)


# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     datefmt="%H:%M:%S",
# )


async def clear_redis_stats(redis):
    print("Clearing Redis stats...")
    await redis.delete("total_buses")
    await redis.delete("total_stops")
    await redis.delete("total_users")


async def record_snapshot(redis):
    try:
        async with asyncio.timeout(5):
            with SessionLocal() as db:
                total = int(await redis.get("total_ws_connections") or 0)
                unique = int(await redis.scard("total_clients") or 0)

                await redis.delete("total_clients")
                clients = await redis.smembers("clients")
                if clients:
                    await redis.sadd("total_clients", *clients)

                timestamp = floor_to_30s(datetime.now(timezone.utc))

                exists = (
                    db.query(ActiveUsersSnapshot).filter_by(timestamp=timestamp).first()
                )
                if not exists:
                    print(f"Logging {unique} active users at {timestamp.isoformat()}")
                    db.add(
                        ActiveUsersSnapshot(
                            total_connections=total,
                            unique_connections=unique,
                            timestamp=timestamp,
                        )
                    )

                cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
                db.query(ActiveUsersSnapshot).filter(
                    ActiveUsersSnapshot.timestamp < cutoff
                ).delete()
                db.commit()
    except Exception as e:
        print("Error recording active users:", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = get_redis_client()
    if await redis.ping():
        print("Redis Connected.")
    else:
        print("Redis did not respond.")
    await redis.close()
    is_leader = await redis.set("app:leader", "1", nx=True, ex=60)
    if is_leader:
        print("This instance is the leader.")
        await redis.delete("total_clients")
        redis.sadd("total_clients", *[])
        await redis.delete("clients")
        redis.sadd("clients", *[])
        await redis.set("total_ws_connections", "0")
    else:
        print("This instance is not the leader.")

    scheduler = AsyncIOScheduler()
    if is_leader:
        scheduler.add_job(
            record_snapshot,
            CronTrigger(second="0,30"),  # run every 30 seconds
            id="record_active_users",
            replace_existing=True,
            args=[redis],
        )
        scheduler.add_job(
            clear_redis_stats,
            CronTrigger(hour="0", minute="0", second="0"),  # daily at midnight
            id="clear_redis_stats",
            replace_existing=True,
            args=[redis],
        )
        scheduler.add_job(
            import_datasets,
            CronTrigger(hour="2", minute="0", second="0"),  # daily at 2am
            id="import_datasets",
            replace_existing=True,
        )
        scheduler.add_job(
            import_weekly_data,
            CronTrigger(day_of_week="0", hour="1", minute="30", second="0"),  # weekly at 1:30am on sunday
            id="import_weekly_data",
            replace_existing=True,
        )
    scheduler.start()
    print("App startup complete.")

    # print("Starting full import...")
    # asyncio.create_task(asyncio.to_thread(do_import))
    # print("Import started in background.")
    try:
        yield
    finally:
        if is_leader:
            await redis.delete("app:leader")
        scheduler.shutdown(wait=False)


if config.env != "development":
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


print(f"running in {config.env} mode")
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
    redis = await get_redis()
    start = time.time()
    client_id = request.headers.get("X-Client-ID")
    if client_id:
        await redis.sadd("total_clients", client_id)  # type: ignore
        await redis.sadd("total_users", client_id)  # type: ignore
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.method} {request.url} completed in {duration:.3f}s")
    response.headers["X-Version"] = VERSION
    return response


@app.get("/api/v1/health/")
async def health_check(db: Session = Depends(get_db), redis=Depends(get_redis)):
    try:
        # Simple test query
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        await redis.ping()
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
