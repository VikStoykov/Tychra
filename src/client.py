import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class Tychra(commands.Bot):
    def __init__(self, *args, **kwargs):
        # Set up intents - using minimal intents to avoid privileged intent requirement
        # Only request what we absolutely need
        intents = discord.Intents.default()
        intents.guilds = True  # Required to see guilds
        # Note: members intent is privileged and must be enabled in Discord Developer Portal
        # We can work without it by using guild.me instead of guild.get_member()
        intents.members = False  # Set to False to avoid privileged intent requirement

        super().__init__(
            command_prefix=commands.when_mentioned,  # Only respond to mentions, not messages
            intents=intents,
            *args,
            **kwargs
        )

        self.config_manager = None

    async def setup_hook(self):
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

    async def on_ready(self):
        logger.info("✨ Fate aligns — Tychra awakens!")

        # Log all guilds we're in
        for guild in self.guilds:
            logger.info(f"  - {guild.name} (ID: {guild.id})")

    async def on_guild_join(self, guild):
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")

        # Initialize config for new guild
        if self.config_manager:
            self.config_manager.get_guild_config(guild.id)

    async def on_guild_remove(self, guild):
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")

        if self.config_manager:
            self.config_manager.remove_guild(guild.id)

    async def update_nickname(self, guild, nickname):
        try:
            member = guild.me
            if not member:
                logger.warning(f"Bot not found in guild {guild.name}")
                return False

            # Check if nickname is too long
            if len(nickname) > 32:
                logger.warning(f"Nickname too long for {guild.name}, truncating")
                nickname = nickname[:32]

            await member.edit(nick=nickname)
            logger.info(f"Updated nickname in {guild.name} to: {nickname}")
            return True

        except discord.Forbidden:
            logger.warning(f"Missing permissions to change nickname in {guild.name}")
            return False
        except Exception as e:
            logger.error(f"Error updating nickname in {guild.name}: {e}")
            return False

    async def update_status(self, status_text, activity_type = "custom"):
        try:
            # Use custom status by default (like user's status message)
            if activity_type == "custom":
                # Custom status with just text (appears below username)
                activity = discord.CustomActivity(name=status_text)
            elif activity_type == "watching":
                activity = discord.Activity(type=discord.ActivityType.watching, name=status_text)
            elif activity_type == "listening":
                activity = discord.Activity(type=discord.ActivityType.listening, name=status_text)
            elif activity_type == "competing":
                activity = discord.Activity(type=discord.ActivityType.competing, name=status_text)
            else:  # playing
                activity = discord.Game(name=status_text)

            # Update presence
            await self.change_presence(activity=activity)
            logger.info(f"Updated status to: {status_text}")
            return True

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            return False

def create_bot():
    bot = Tychra()
    return bot
