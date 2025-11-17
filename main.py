from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import sys
import logging
import logging.handlers
import asyncio
from src.client import create_bot
from src.commands import setup_commands

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

async def main():
    # for more info on setting up logging,
    # see https://discordpy.readthedocs.io/en/latest/logging.html and https://docs.python.org/3/howto/logging.html

    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

    # Console handler for logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler for logging
    file_handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("🌙 Summoning Tychra...")

    token = getenv("DISCORD_TOKEN")
    if not token:
        logger.error("⚠️ DISCORD_TOKEN environment variable not set")
        sys.exit(1)

    bot = create_bot()

    @bot.event
    async def on_ready():
        await setup_commands(bot)
        logger.info(f"🧘🏻‍♀️ Whispering to the gods of chance! Logged in as {bot.user}")

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("😴 Tychra closes her eyes to the market...")
    except Exception as e:
        logger.error(f"⛔ Error running Tychra: {e}")
        sys.exit(1)
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
