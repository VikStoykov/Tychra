import logging
import os
import datetime
from zoneinfo import ZoneInfo
from discord.ext import tasks
from typing import Optional, List

logger = logging.getLogger(__name__)


class UpdateScheduler:
    """
    Handles scheduled automatic updates for the bot.
    Uses discord.ext.tasks for background task management.
    """

    def __init__(self, bot, config_manager, updater):
        self.bot = bot
        self.config_manager = config_manager
        self.updater = updater
        self.update_times: Optional[List[datetime.time]] = None
        self._parse_update_times()

    def _parse_update_times(self):
        """
        Parse UPDATE_TIMES and TIMEZONE from environment variables.
        Format: "HH:MM,HH:MM,HH:MM" (e.g., "09:00,18:00,23:30")
        Timezone: IANA timezone name (e.g., "America/New_York", "Europe/London")
        """
        update_times_str = os.getenv("UPDATE_TIMES", "").strip()
        timezone_str = os.getenv("TIMEZONE", "UTC").strip()

        if not update_times_str:
            logger.info("UPDATE_TIMES not set, automatic updates disabled")
            return

        try:
            tz = ZoneInfo(timezone_str)
            logger.info(f"Using timezone: {timezone_str}")
        except Exception as e:
            logger.warning(f"Invalid timezone '{timezone_str}', falling back to UTC: {e}")
            tz = ZoneInfo("UTC")
            timezone_str = "UTC"

        times = []

        for time_str in update_times_str.split(','):
            time_str = time_str.strip()
            try:
                hour, minute = map(int, time_str.split(':'))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    time_obj = datetime.time(hour=hour, minute=minute, tzinfo=tz)
                    times.append(time_obj)
                    logger.info(f"Scheduled update at {time_str} {timezone_str}")
                else:
                    logger.warning(f"Invalid time value: {time_str} (must be HH:MM with hour 0-23, minute 0-59)")
            except ValueError:
                logger.warning(f"Invalid time format: {time_str} (expected HH:MM)")

        if times:
            self.update_times = times
        else:
            logger.warning("No valid update times found in UPDATE_TIMES")

    def start(self):
        """
        Start the scheduled update task if times are configured
        """
        if self.update_times:
            # Dynamically change the loop interval to match configured times
            self.scheduled_update.change_interval(time=self.update_times)
            self.scheduled_update.start()
            logger.info(f"Scheduled updates enabled for {len(self.update_times)} time(s) per day")
        else:
            logger.info("Scheduled updates not started (no times configured)")

    def stop(self):
        """
        Stop the scheduled update task
        """
        if self.scheduled_update.is_running():
            self.scheduled_update.cancel()
            logger.info("Scheduled updates stopped")

    @tasks.loop()
    async def scheduled_update(self):
        """
        Background task that runs at scheduled times.
        Updates all guilds with latest market data.
        """
        try:
            logger.info("⏰ Running scheduled update...")
            results = await self.updater.update_all_guilds()
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            logger.info(f"Scheduled update complete: {successful}/{total} guilds updated")
        except Exception as e:
            logger.error(f"Error in scheduled update: {e}", exc_info=True)

    @scheduled_update.before_loop
    async def before_scheduled_update(self):
        #Wait for bot to be ready before starting scheduled updates
        await self.bot.wait_until_ready()
        logger.info("Bot ready, scheduled updates will now run at configured times")

    @scheduled_update.error
    async def scheduled_update_error(self, error):
        logger.error(f"Unhandled error in scheduled update: {error}", exc_info=error)
