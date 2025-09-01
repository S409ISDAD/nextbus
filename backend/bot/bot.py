import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from backend.db.db import SessionLocal
from backend.models import Line, BotConfig
from backend.utils.fetch_json import fetch_json
from datetime import datetime
from sqlalchemy import event
import os


@event.listens_for(Line, "after_insert")
@event.listens_for(Line, "after_update")
@event.listens_for(Line, "after_delete")
def route_changed(mapper, connection, target):
    # update the message as a line has been added
    asyncio.create_task(update_dashboard())


intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

DASHBOARD_CHANNEL_ID = 1411756379542392953


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


async def update_dashboard():
    print("Updating dashboard message...")
    with SessionLocal() as db:
        lines = db.query(Line).join(Line.service).all()
        lines_text = ""
        for line in lines:
            bustimes_id = await line.get_bt_service_id()
            bt_service = await fetch_json(
                f"https://bustimes.org/api/services/{bustimes_id}"
            )
            if not bt_service:
                lines_text += f"{line.line_name} | {line.service.origin} - {line.service.destination}\n"
            else:
                slug = bt_service.get("slug", "")
                bustimes_link = f"(https://bustimes.org/services/{slug})"
                lines_text += f"[{line.line_name} | {line.service.origin} - {line.service.destination}]{bustimes_link}\n"
        msg_content = (
            "# This channel is for requesting routes to be added to the system until I set up a full import.\n\nThese routes have advanced capabilities over other routes. e.g. predicting buses using blocks.\n## Routes in the system:\n"
            + lines_text
            + "\nPlease provide the name of the route and where it is located. (bustimes.org link is preferred)"
            + f"\n\n-# updated <t:{int(datetime.now().timestamp())}:R>"
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
