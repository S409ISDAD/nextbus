import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from backend.db.db import SessionLocal
from backend.deps import LONDON, UTC
from backend.models import Line, BotConfig, BotStatusEnum, BotStatus
from backend.utils.fetch_json import fetch_json
from datetime import datetime, timedelta
from sqlalchemy import event
from sqlalchemy.orm import joinedload

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

DASHBOARD_CHANNEL_ID = 1411756379542392953
STATUS_CHANNEL_ID = 1404456642090897669

update_queue = asyncio.Queue()


@event.listens_for(Line, "after_insert")
@event.listens_for(Line, "after_update")
@event.listens_for(Line, "after_delete")
def route_changed(mapper, connection, target):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(update_queue.put(True))
        else:
            print("No running event loop; dashboard update not queued.")
    except RuntimeError:
        print("No running event loop; dashboard update not queued.")


async def update_dashboard_worker():
    await bot.wait_until_ready()
    while True:
        await update_queue.get()
        await update_dashboard()
        update_queue.task_done()


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
    print(f"Bot logged in as {bot.user}")
    # Initial update
    if not getattr(bot, "_dashboard_worker_started", False):
        bot.loop.create_task(update_dashboard_worker())
        setattr(bot, "_dashboard_worker_started", True)
    if not getattr(bot, "_status_monitor_started", False):
        bot.loop.create_task(monitor_status())
        setattr(bot, "_status_monitor_started", True)
    await update_dashboard()


@bot.tree.command(
    name="update_dashboard", description="Manually update the dashboard message"
)
@is_admin()
async def update_dashboard_command(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    await update_dashboard()
    await interaction.followup.send("Dashboard updated.", ephemeral=True)


async def get_dashboard_message() -> discord.Message | None:
    with SessionLocal() as db:
        entry = (
            db.query(BotConfig).filter_by(channel_id=str(DASHBOARD_CHANNEL_ID)).first()
        )
        if entry is not None and entry.message_id is not None:
            channel = bot.get_channel(DASHBOARD_CHANNEL_ID)
            if channel and isinstance(channel, discord.TextChannel):
                try:
                    msg = await channel.fetch_message(int(getattr(entry, "message_id")))
                    return msg
                except discord.NotFound:
                    return None
    return None


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


async def update_dashboard():
    await bot.wait_until_ready()
    print("Updating dashboard message...")
    with SessionLocal() as db:
        lines = db.query(Line).options(joinedload(Line.service)).all()
        lines_text = ""
        num = len(lines)
        scso_total = 189
        for line in lines:
            bustimes_id = await line.get_bt_service_id(db)
            bt_service = await fetch_json(
                f"https://bustimes.org/api/services/{bustimes_id}"
            )
            if not bt_service:
                lines_text += f"{line.line_name}  "
            else:
                if num < 20:
                    slug = bt_service.get("slug", "")
                    bustimes_link = f"(https://bustimes.org/services/{slug})"
                    lines_text += f"[{line.line_name} | {line.service.origin} - {line.service.destination}]{bustimes_link}\n"
                else:
                    lines_text += f"{line.line_name}  "
        percent = round((num / scso_total) * 100, 1) if scso_total else 0
        msg_content = (
            "# This channel is for requesting routes to be added to the system until I set up a full import.\n\nThese routes have advanced capabilities over other routes. e.g. predicting buses using blocks.\n## Routes in the system:\n"
            + f"**{num} routes** ({percent}% of {scso_total} in Stagecoach South Dataset)\n\n"
            + lines_text
            + "\n\nPlease provide the name of the route and where it is located. (bustimes.org link is preferred)"
            + f"\n\n-# updated <t:{int(datetime.now(tz=UTC).timestamp())}:R>"
        )

        # Fetch the dashboard message
        message = await get_dashboard_message()

        channel = bot.get_channel(DASHBOARD_CHANNEL_ID)
        if not message and channel and isinstance(channel, discord.TextChannel):
            # Send new message if it doesn't exist
            message = await channel.send(msg_content)
            # Save message_id in DB
            db_entry = (
                db.query(BotConfig)
                .filter_by(channel_id=str(DASHBOARD_CHANNEL_ID))
                .first()
            )
            if not db_entry:
                db_entry = BotConfig(
                    channel_id=str(DASHBOARD_CHANNEL_ID), message_id=str(message.id)
                )
                db.add(db_entry)
            else:
                db_entry.message_id = str(message.id)
            db.commit()
        if message:
            await message.edit(content=msg_content, suppress=True)
            print("Dashboard message updated.")
        else:
            print("Could not find or create dashboard message.")
