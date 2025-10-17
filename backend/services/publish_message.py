import json
from backend.deps import LONDON, DateTimeEncoder, get_redis
from backend.tasks.import_txc_new import Statistics
from backend.schemas.discord_bot import ImportMessage, SimpleStatistics
from datetime import datetime


async def queue_import_message(time_taken: float, stats: Statistics):
    redis = await get_redis()

    timestamp = datetime.now(tz=LONDON)

    simple_stats = SimpleStatistics(
        sc=stats.services_created,
        su=len(stats.services_updated),
        sd=stats.services_deactivated,
        ss=stats.services_skipped,
        tc=stats.timetables_created,
        tu=len(stats.timetables_updated),
        td=stats.timetables_deleted,
        ts=len(stats.timetables_skipped),
        jc=stats.journeys_created,
        stc=stats.stop_times_created,
        stpc=stats.stops_created,
        stpu=stats.stops_updated,
    )
    msg = ImportMessage(time_taken=time_taken, timestamp=timestamp, stats=simple_stats)

    payload = {
        "type": "import",
        "data": msg.model_dump(),
    }

    await redis.publish("discord_messages", json.dumps(payload, cls=DateTimeEncoder))
