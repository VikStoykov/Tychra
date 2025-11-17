import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class CommandsCog(commands.Cog):
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager

    @app_commands.command(name="about", description="Show bot information")
    async def about(self, interaction):
        try:
            from version import __version__, __release_date__
            version_str = f"v{__version__} ({__release_date__})"
        except ImportError:
            version_str = "v1.0.0"

        embed = discord.Embed(
            title="🌊 Tychra",
            description="A Discord bot that tracks market sentiment indicators.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Data Sources",
            value=(
                "• Stock Market F&G Index (CNN)\n"
                "• Crypto Market F&G Index (Alternative.me)"
            ),
            inline=False
        )

        embed.add_field(
            name="💬 Commands",
            value=(
                "`/about` - Show this information"
            ),
            inline=False
        )

        embed.add_field(
            name="🔗 Links",
            value="[GitHub](https://github.com/VikStoykov/Tychra) • [Documentation](https://github.com/VikStoykov/Tychra#readme)",
            inline=False
        )

        embed.set_footer(text=f"Version {version_str} • Built with discord.py")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup_commands(bot):
    # Check if cog is already loaded (happens on reconnect)
    if bot.get_cog("CommandsCog") is not None:
        logger.info("✅ Commands already loaded, skipping setup")
        return

    cog = CommandsCog(bot, None)  # config_manager can be None for now
    await bot.add_cog(cog)

    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"🔄 Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"⛔ Failed to sync commands: {e}")
