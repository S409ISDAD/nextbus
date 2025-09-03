import asyncio
import os
import signal
import dotenv
from backend.bot.bot import bot

print("Starting discord bot...")
dotenv.load_dotenv()
token = os.getenv("BOT_TOKEN")


async def run_bot(token):
    stop_event = asyncio.Event()

    def handle_sigterm():
        print("Received SIGTERM, shutting down bot...")
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
        print(f"Bot error: {e}")
        await bot.close()


if token:
    asyncio.run(run_bot(token))
else:
    print("No BOT_TOKEN found in environment, bot will not start.")
