import asyncio
import json
import discord
from discord import app_commands
from discord.ext import commands
from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal
from backend.deps import LONDON, UTC, datetime_decoder
from backend.models import BotStatus
from backend.deps import get_redis
from backend.utils.fetch_json import fetch_json
from backend.schemas.discord_bot import ImportMessage
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

setup_logging()
log = get_logger(__name__)

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

DASHBOARD_CHANNEL_ID = 1411756379542392953
STATUS_CHANNEL_ID = 1404456642090897669
IMPORT_CHANNEL_ID = 1425506807773921280

update_queue = asyncio.Queue()

load_dotenv()

MACHINE_NAME = os.getenv("MACHINE_NAME", "unknown-machine")


async def redis_listener():
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe("discord_messages")
    log.debug("Subscribed to Redis channel 'discord_messages'")

    async for message in pubsub.listen():
        if message is None:
            continue
        if message.get("type") == "message":
            try:
                try:
                    data = json.loads(message["data"], object_hook=datetime_decoder)
                except Exception as e:
                    log.error(f"Failed to decode JSON message: {e}")
                    continue
                if data.get("type") != "import":
                    continue
                data = ImportMessage.model_validate(data.get("data", "{}"))
                log.debug(f"Received message from Redis: {data}")
                await send_import_message(data)
            except Exception as e:  # noqa: E722
                log.error(f"Failed to parse message: {message.get('data')}, error: {e}")
                continue


def is_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        member = interaction.user
        if hasattr(member, "roles"):
            return any(role.name == "owner" for role in member.roles)
        return False

    return app_commands.check(predicate)


@bot.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message(
            "You do not have permission to run this.", ephemeral=True
        )


@bot.event
async def on_ready():
    log.debug(f"Bot logged in as {bot.user}")
    # Initial update
    if not getattr(bot, "_redis_listener_started", False):
        bot.loop.create_task(redis_listener())
        setattr(bot, "_redis_listener_started", True)
    # if not getattr(bot, "_status_monitor_started", False):
    #     bot.loop.create_task(monitor_status())
    #     setattr(bot, "_status_monitor_started", True)


async def send_import_message(data: ImportMessage):
    channel = bot.get_channel(IMPORT_CHANNEL_ID)
    if channel and isinstance(channel, discord.TextChannel):
        stats = data.stats
        duration = timedelta(seconds=data.time_taken).total_seconds()

        hours, rem = divmod(duration, 3600)
        mins, secs = divmod(rem, 60)
        time_str = (
            f"{int(hours)}h {int(mins)}m {secs:.2f}s"
            if hours
            else f"{int(mins)}m {secs:.2f}s"
            if mins
            else f"{secs:.2f}s"
        )
        embed = discord.Embed(
            title="TXC Import Completed",
            description=f"Import completed in {time_str}",
            color=discord.Color.green(),
            timestamp=data.timestamp,
        )
        embed.add_field(
            name="Services",
            value=f"{stats.sc} added, {stats.su} updated\n{stats.sd} deactivated, {stats.ss} skipped",
            inline=False,
        )
        embed.add_field(
            name="Timetables",
            value=f"{stats.tc} added, {stats.tu} updated\n{stats.td} deleted, {stats.ts} skipped",
            inline=False,
        )
        embed.add_field(
            name="Journeys",
            value=f"{stats.jc} added",
            inline=False,
        )
        embed.add_field(
            name="StopTimes",
            value=f"{stats.stc} added",
            inline=False,
        )
        embed.add_field(
            name="Stops",
            value=f"{stats.stpc} added, {stats.stpu} updated",
            inline=False,
        )
        embed.set_footer(text=MACHINE_NAME)
        await channel.send(embed=embed)
    else:
        log.error(f"Channel {IMPORT_CHANNEL_ID} not found or not a text channel")


async def get_status():
    health = await fetch_json("https://nextbus.orbitix.dev/api/v1/health/")
    status = "up"
    if not health:
        return "down"
    if health.get("status") != "healthy":
        return "degraded"
    return status


async def monitor_status(interval: int = 60):
    await bot.wait_until_ready()
    not_healthy_time = None
    while True:
        with SessionLocal() as db:
            status = await get_status()
            bot_status = (
                db.query(BotStatus)
                .filter(BotStatus.channel_id == str(STATUS_CHANNEL_ID))
                .first()
            )
            last_status = bot_status.last_status if bot_status else None
            last_not_healthy_time = bot_status.not_healthy_time if bot_status else None

            downtime_duration = None
            if status != last_status:
                if status != "up":
                    if not last_not_healthy_time:
                        not_healthy_time = datetime.now(tz=UTC)
                        if bot_status:
                            bot_status.not_healthy_time = not_healthy_time
                        else:
                            bot_status = BotStatus(
                                channel_id=int(STATUS_CHANNEL_ID),
                                last_status=status,
                                not_healthy_time=not_healthy_time,
                            )
                            db.add(bot_status)
                    else:
                        not_healthy_time = last_not_healthy_time
                else:
                    if last_not_healthy_time:
                        downtime_duration = datetime.now(tz=UTC) - last_not_healthy_time
                    not_healthy_time = None
                    if bot_status:
                        bot_status.not_healthy_time = None

                await send_status_message(status, downtime_duration)

                if bot_status:
                    bot_status.last_status = status
                else:
                    bot_status = BotStatus(
                        channel_id=str(STATUS_CHANNEL_ID),
                        last_status=status,
                        not_healthy_time=not_healthy_time,
                    )
                    db.add(bot_status)
                db.commit()
            await asyncio.sleep(interval)


async def send_status_message(status: str, downtime_duration: timedelta | None = None):
    emoji = "✅" if status == "up" else "⚠️" if status == "degraded" else "❌"
    message = f"# {emoji} nextbus is {status}"

    if downtime_duration and status == "up":
        hours = downtime_duration.total_seconds() // 3600
        minutes = (downtime_duration.total_seconds() % 3600) // 60
        seconds = int(downtime_duration.total_seconds() % 60)
        downtime_str = []
        if hours > 0:
            downtime_str.append(f"{int(hours)}h")
        if minutes > 0:
            downtime_str.append(f"{int(minutes)}m")
        if seconds > 0 or not downtime_str:
            downtime_str.append(f"{seconds}s")
        duration = " ".join(downtime_str)
        message += f"\n(down for {duration})"

    message += f"\n-# <t:{int(datetime.now(tz=LONDON).timestamp())}:F>"

    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if channel and isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def send_message(msg: str):
    message = f"# ℹ️ {msg}"
    message += f"\n-# <t:{int(datetime.now(tz=LONDON).timestamp())}:F>"

    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if channel and isinstance(channel, discord.TextChannel):
        await channel.send(message)
