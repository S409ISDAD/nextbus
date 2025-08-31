import asyncio
from datetime import timedelta, timezone, datetime
import os
import time
import dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.api.routes import (
    departures,
    lines,
    location,
    stats,
    stops,
    services,
    buses,
    livery,
    trains,
)
from sqlalchemy.orm import Session
from backend.db.db import SessionLocal, sync_search_vectors, engine, get_db
from backend.models import ActiveUsersSnapshot, Base
from backend.websockets.routes import ws_router
from backend.deps import floor_to_30s, get_redis_client, get_redis, limiter
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.tasks.full_import import do_import
from backend.bot.bot import bot


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
    bot_task = None
    redis = get_redis_client()
    if await redis.ping():
        print("Redis Connected.")
    else:
        print("Redis did not respond.")
    await redis.close()
    await redis.delete("total_clients")
    redis.sadd("total_clients", *[])
    await redis.delete("clients")
    redis.sadd("clients", *[])
    await redis.set("total_ws_connections", "0")
    print("Setting up database...")
    Base.metadata.create_all(bind=engine)
    print("Syncing search vectors...")
    asyncio.create_task(asyncio.to_thread(sync_search_vectors))
    print("Database setup complete.")

    print("Starting discord bot...")
    dotenv.load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if token:
        bot_task = asyncio.create_task(bot.start(token))
    else:
        print("No BOT_TOKEN found in environment, bot will not start.")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        record_snapshot,
        CronTrigger(second="0,30"),  # run every 30 seconds
        id="record_active_users",
        replace_existing=True,
        args=[redis],
    )
    scheduler.add_job(
        clear_redis_stats,
        CronTrigger(hour="0", minute="0", second="0"),
        id="clear_redis_stats",
        replace_existing=True,
        args=[redis],
    )
    scheduler.start()

    # print("Starting full import...")
    # asyncio.create_task(asyncio.to_thread(do_import))
    # print("Import started in background.")
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)

        if bot_task:
            print("Shutting down bot...")
            await bot.close()
            await bot_task


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
        await redis.sadd("total_clients", client_id)
        await redis.sadd("total_users", client_id)
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.method} {request.url} completed in {duration:.3f}s")
    return response


@app.get("/api/v1/health/")
async def health_check(db: Session = Depends(get_db), redis=Depends(get_redis)):
    try:
        # Simple test query
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        await redis.ping()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
