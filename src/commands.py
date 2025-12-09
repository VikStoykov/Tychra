import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class CommandsCog(commands.Cog):
    def __init__(self, bot, config_manager, chart_generator=None):
        self.bot = bot
        self.config_manager = config_manager
        self.chart_generator = chart_generator

    async def _perform_update(self, guild_id):
        from src.updater import Updater
        updater = Updater(self.bot, self.config_manager)
        return await updater.update_guild(guild_id)

    async def _update_and_respond(self, interaction, success_msg, error_msg=None):
        try:
            await self._perform_update(interaction.guild.id)
            await interaction.followup.send(
                f"{success_msg}\n🔄 Updated successfully!",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error during update: {e}")
            fallback = error_msg or f"{success_msg}\n⚠️ Update will be applied on next scheduled run."
            await interaction.followup.send(fallback, ephemeral=True)

    @app_commands.command(name="setnickname", description="Set the bot's nickname template")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(template="Template for nickname (e.g., 'F/G: {m.index}')")
    async def set_nickname(self, interaction, template: str):

        if len(template) > 32:
            await interaction.response.send_message(
                f"❌ Template is too long ({len(template)} chars). Discord nicknames must be 32 characters or less.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        success = self.config_manager.set_guild_template(
            interaction.guild.id,
            "nickname",
            template
        )

        if success:
            await self._update_and_respond(
                interaction,
                f"✅ Nickname template updated to: `{template}`"
            )
        else:
            await interaction.followup.send(
                "❌ Failed to update nickname template.",
                ephemeral=True
            )

    @app_commands.command(name="setstatus", description="Set the bot's status template")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(template="Template for status (e.g., '{m.emotion} {m.emoji}')")
    async def set_status(self, interaction, template: str):

        await interaction.response.defer(ephemeral=True)

        success = self.config_manager.set_guild_template(
            interaction.guild.id,
            "status",
            template
        )

        if success:
            await self._update_and_respond(
                interaction,
                f"✅ Status template updated to: `{template}`"
            )
        else:
            await interaction.followup.send(
                "❌ Failed to update status template.",
                ephemeral=True
            )

    @app_commands.command(name="showtemplates", description="Show current templates")
    @app_commands.default_permissions(administrator=True)
    async def show_templates(self, interaction):
        config = self.config_manager.get_guild_config(interaction.guild.id)

        embed = discord.Embed(
            title="📋 Current Templates",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Nickname Template",
            value=f"`{config.get('nickname_template', 'Not set')}`",
            inline=False
        )

        embed.add_field(
            name="Status Template",
            value=f"`{config.get('status_template', 'Not set')}`",
            inline=False
        )

        embed.add_field(
            name="Available Placeholders",
            value=(
                "**Stock Market (m):**\n"
                "`{m.index}` - Index value (0-100)\n"
                "`{m.emotion}` - Emotion label\n"
                "`{m.emoji}` - Emotion emoji\n"
                "`{m.trend}` - Trend indicator\n\n"
                "**Crypto Market (c):**\n"
                "`{c.index}` - Index value (0-100)\n"
                "`{c.emotion}` - Emotion label\n"
                "`{c.emoji}` - Emotion emoji\n"
                "`{c.trend}` - Trend indicator\n"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="forceupdate", description="Force an immediate update")
    @app_commands.default_permissions(administrator=True)
    async def force_update(self, interaction):

        await interaction.response.defer(ephemeral=True)

        try:
            success = await self._perform_update(interaction.guild.id)

            if success:
                await interaction.followup.send("✅ Update completed successfully!", ephemeral=True)
            else:
                await interaction.followup.send("⚠️ Update completed with some errors. Check logs.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in force update: {e}")
            await interaction.followup.send(f"❌ Error during update: {str(e)}", ephemeral=True)

    @app_commands.command(name="about", description="Show bot information")
    async def about(self, interaction):
        try:
            from version import __version__, __release_date__
            version_str = f"v{__version__} ({__release_date__})"
        except ImportError:
            version_str = "v1.2.0"

        embed = discord.Embed(
            title="🌊 Tychra",
            description="A Discord bot that tracks market sentiment indicators.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Data Sources",
            value=(
                "• Stock Market F&G Index (CNN)"
                "• Crypto Market F&G Index (Alternative.me)"
            ),
            inline=False
        )

        embed.add_field(
            name="💬 Commands",
            value=(
                "`/setnickname` - Set nickname template\n"
                "`/setstatus` - Set status template\n"
                "`/showtemplates` - View current templates\n"
                "`/forceupdate` - Trigger immediate update\n"
                "`/chart` - Generate F&G Index chart\n"
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

    @app_commands.command(name="chart", description="Generate Fear & Greed Index chart")
    @app_commands.describe(
        days="Number of days to show (default: 10, max: 365)",
        provider="Data source: market (stocks) or crypto (default: market)"
    )
    @app_commands.choices(provider=[
        app_commands.Choice(name="Stock Market", value="market"),
        app_commands.Choice(name="Cryptocurrency", value="crypto")
    ])
    async def chart(
        self, 
        interaction: discord.Interaction,
        days: int = 10,
        provider: app_commands.Choice[str] = None
    ):
        """Generate and display Fear & Greed Index chart."""

        # Check if chart generator is available
        if not self.chart_generator:
            await interaction.response.send_message(
                "❌ Chart generation is not available.",
                ephemeral=True
            )
            return

        # Validate days parameter
        if days < 1:
            await interaction.response.send_message(
                "❌ Number of days must be at least 1.",
                ephemeral=True
            )
            return

        if days > 365:
            await interaction.response.send_message(
                "❌ Number of days cannot exceed 365.",
                ephemeral=True
            )
            return

        # Check if chart generation is already in progress
        if await self.chart_generator.is_busy():
            await interaction.response.send_message(
                "⏳ Chart generation is already in progress. Please try again in a moment.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Determine provider
            provider_value = provider.value if provider else "market"
            provider_name = "Stock Market" if provider_value == "market" else "Cryptocurrency"
            
            logger.info(f"📊 Generating {provider_name} chart for {days} days (requested by {interaction.user})")
            
            # Generate chart
            chart_url = await self.chart_generator.generate_chart(days, provider_value)
            
            if chart_url:
                embed = discord.Embed(
                    title=f"📈 {provider_name} Fear & Greed Index",
                    description=f"Showing last {days} day{'s' if days != 1 else ''}",
                    color=discord.Color.blue()
                )
                embed.set_image(url=chart_url)
                embed.set_footer(text=f"Requested by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    "❌ Failed to generate chart. Please try again later.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            await interaction.followup.send(
                f"❌ Error generating chart: {str(e)}",
                ephemeral=True
            )

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command.",
                ephemeral=True
            )
        else:
            logger.error(f"Command error: {error}", exc_info=error)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ An error occurred: {str(error)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ An error occurred: {str(error)}",
                    ephemeral=True
                )

async def setup_commands(bot, config_manager, chart_generator=None):
    # Check if cog is already loaded (happens on reconnect)
    if bot.get_cog("CommandsCog") is not None:
        logger.info("✅ Commands already loaded, skipping setup")
        return

    cog = CommandsCog(bot, config_manager, chart_generator)
    await bot.add_cog(cog)

    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"🔄 Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"⛔ Failed to sync commands: {e}")
