import asyncio
import os
import signal
import dotenv
from backend.bot.bot import bot, send_message
from backend.config import get_logger, setup_logging

setup_logging()

log = get_logger()

log.debug("Starting discord bot...")
dotenv.load_dotenv()
token = os.getenv("BOT_TOKEN")
env = os.getenv("ENV", "development")
disabled = os.getenv("BOT_DISABLED", "false").lower() == "true"


async def run_bot(token):
    stop_event = asyncio.Event()

    def handle_sigterm():
        log.debug("Received SIGTERM, shutting down bot...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    loop.add_signal_handler(signal.SIGINT, handle_sigterm)

    try:
        bot_task = asyncio.create_task(bot.start(token))
        await stop_event.wait()
        await bot.close()
        bot_task.cancel()
    except Exception as e:
        log.debug(f"Bot error: {e}")
        await bot.close()


# if env == "development":
#     log.debug("Running in development mode, bot will not start.")
# else:
if disabled:
    log.debug("Bot is disabled via BOT_DISABLED environment variable.")
elif token:
    asyncio.run(run_bot(token))
else:
    log.debug("No BOT_TOKEN found in environment, bot will not start.")
