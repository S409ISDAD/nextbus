from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import get_logger, setup_logging
from backend.tasks.import_all_datasets import import_datasets, import_weekly_data
from backend.tasks.reset_bt_trip_ids import reset_trip_ids
import time

log = get_logger(__name__)


def main():
    scheduler = BackgroundScheduler()

    # daily jobs
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

    # weekly job
    scheduler.add_job(
        import_weekly_data,
        CronTrigger(
            day_of_week="0", hour="5", minute="30", second="0"
        ),  # Sunday 5:30am
        id="import_weekly_data",
        replace_existing=True,
    )

    scheduler.start()
    log.info("Data scheduler started.")

    try:
        # keep it running
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    setup_logging()
    main()
