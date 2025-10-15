import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import get_logger, setup_logging
from backend.tasks.import_all_datasets import import_datasets, import_weekly_data
from backend.tasks.reset_bt_trip_ids import reset_trip_ids

log = get_logger(__name__)

async def main():
    scheduler = AsyncIOScheduler()
    
    event = asyncio.Event()

    scheduler.add_job(
        import_datasets,
        CronTrigger(hour="2", minute="0", second="0"),  # daily at 2am
        id="import_datasets",
        replace_existing=True,
    )
    scheduler.add_job(
        reset_trip_ids,
        CronTrigger(hour="1", minute="55", second="0"),  # daily at 1:55am
        id="reset_trip_ids",
        replace_existing=True,
    )
    scheduler.add_job(
        import_weekly_data,
        CronTrigger(day_of_week="0", hour="5", minute="30", second="0"),  # weekly at 5:30am Sunday
        id="import_weekly_data",
        replace_existing=True,
    )

    scheduler.start()
    log.info("Data scheduler started.")
    try:
        await event.wait() # keep the scheduler running indefinitely
    except (KeyboardInterrupt, SystemExit):
        event.set()
        scheduler.shutdown(wait=False)

if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())