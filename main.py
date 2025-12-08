import asyncio
import logging
import logging.handlers
import os
import sys
from dotenv import load_dotenv
from src.client import create_bot
from src.config_manager import ConfigManager
from src.commands import setup_commands
from src.updater import Updater
from src.scheduler import UpdateScheduler
from src.chart_generator import ChartGenerator

load_dotenv()

async def run_bot(logger):

    logger.info("🌙 Summoning Tychra...")

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        sys.exit(1)

    bot = create_bot()
    config_manager = ConfigManager()
    bot.config_manager = config_manager

    updater = Updater(bot, config_manager)
    scheduler = UpdateScheduler(bot, config_manager, updater)
    chart_generator = ChartGenerator()

    @bot.event
    async def on_ready():
        await setup_commands(bot, config_manager, chart_generator)
        logger.info(f"🧘🏻‍♀️ Whispering to the gods of chance! Logged in as {bot.user}")

        logger.info("Running initial update for all guilds...")
        try:
            #updater = Updater(bot, config_manager)
            results = await updater.update_all_guilds()
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            logger.info(f"Initial update complete: {successful}/{total} guilds updated successfully")

            scheduler.start()
        except Exception as e:
            logger.error(f"Error during initial update: {e}")

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("😴 Tychra closes her eyes to the market...")
    except Exception as e:
        logger.error(f"⛔ Error running Tychra: {e}")
        sys.exit(1)
    finally:
        scheduler.stop()
        await bot.close()


def main():

    # for more info on setting up logging,
    # see https://discordpy.readthedocs.io/en/latest/logging.html and https://docs.python.org/3/howto/logging.html

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

    # Console handler for logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for logging
    file_handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logger = logging.getLogger(__name__)

    try:
        asyncio.run(run_bot(logger))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
