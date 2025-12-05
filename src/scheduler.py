import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from croniter import croniter
from discord.ext import tasks

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
        self.cron_expression = None
        self.timezone = None
        self._parse_schedule()

    def _parse_schedule(self):
        """
        Parse SCHEDULE_CRON and TIMEZONE from environment variables.

        Cron format: "MINUTE HOUR DAY MONTH DAYOFWEEK"
        Examples:
            "*/5 * * * *"    - Every 5 minutes
            "0 8 * * *"      - Every day at 8:00 AM
            "15 13 * * *"    - Every day at 13:15 (1:15 PM)
            "0 */6 * * *"    - Every 6 hours
            "30 9 * * 1-5"   - Weekdays at 9:30 AM
            "0 0 1 * *"      - First day of every month at midnight

        Timezone: IANA timezone name (e.g., "America/New_York", "Europe/London", "UTC")
        """
        cron_str = os.getenv("SCHEDULE_CRON", "").strip()
        timezone_str = os.getenv("TIMEZONE", "UTC").strip()

        if not cron_str:
            logger.info("SCHEDULE_CRON not set, automatic updates disabled")
            return

        try:
            self.timezone = ZoneInfo(timezone_str)
            logger.info(f"Using timezone: {timezone_str}")
        except Exception as e:
            logger.warning(f"Invalid timezone '{timezone_str}', falling back to UTC: {e}")
            self.timezone = ZoneInfo("UTC")
            timezone_str = "UTC"

        try:
            # Validate cron expression
            base_time = datetime.now(self.timezone)
            cron = croniter(cron_str, base_time)
            next_run = cron.get_next(datetime)

            self.cron_expression = cron_str
            logger.info(f"Cron schedule set: '{cron_str}' (timezone: {timezone_str})")
            logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        except Exception as e:
            logger.error(f"Invalid cron expression '{cron_str}': {e}")

    def start(self):
        """
        Start the scheduled update task if cron expression is configured
        """
        if self.cron_expression:
            self.scheduled_update.start()
            logger.info(f"Scheduled updates enabled with cron: {self.cron_expression}")
        else:
            logger.info("Scheduled updates not started (no schedule configured)")

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
        Background task that runs based on cron schedule.
        """
        if not self.cron_expression:
            return

        try:
            now = datetime.now(self.timezone)
            
            logger.info("⏰ Running scheduled update...")
            results = await self.updater.update_all_guilds()
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            logger.info(f"Scheduled update complete: {successful}/{total} guilds updated")

            # Calculate seconds until next run
            cron = croniter(self.cron_expression, now)
            next_run = cron.get_next(datetime)
            seconds_until_next = (next_run - now).total_seconds()

            logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')} (in {seconds_until_next:.0f}s)")

            # Change interval for next iteration
            self.scheduled_update.change_interval(seconds=max(1, seconds_until_next))

        except Exception as e:
            logger.error(f"Error in scheduled update: {e}", exc_info=True)
            # Fallback to 60 seconds on error
            self.scheduled_update.change_interval(seconds=60)

    @scheduled_update.before_loop
    async def before_scheduled_update(self):
        #Wait for bot to be ready before starting scheduled updates
        await self.bot.wait_until_ready()
        logger.info("Bot ready, scheduled updates will now run at configured times")

    @scheduled_update.error
    async def scheduled_update_error(self, error):
        logger.error(f"Unhandled error in scheduled update: {error}", exc_info=error)
