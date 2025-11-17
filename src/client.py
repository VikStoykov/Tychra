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
            command_prefix='!',  # Fallback prefix
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

def create_bot():
    bot = Tychra()
    return bot
