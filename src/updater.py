import logging
import re

logger = logging.getLogger(__name__)


class Updater:

    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager
        self.provider_cache = {}

    async def fetch_all_providers(self):
        from providers import MarketProvider, CryptoProvider

        providers = { 'm': MarketProvider(), 'c': CryptoProvider() }
        
        for name, provider in providers.items():
            try:
                data = await provider.fetch()
                self.provider_cache[name] = data
                logger.info(f"✓ {name}: {data}")
            except Exception as e:
                logger.error(f"✗ Failed to fetch {name}: {e}")
                self.provider_cache[name] = {}

    def render_template(self, template):
        result = template

        # Find all placeholders like {provider.key}
        placeholders = re.findall(r'\{(\w+)\.(\w+)\}', template)

        for provider_name, key in placeholders:
            placeholder = f"{{{provider_name}.{key}}}"

            # Get value from cache
            if provider_name in self.provider_cache:
                provider_data = self.provider_cache[provider_name]
                value = provider_data.get(key, f"?{key}?")
                result = result.replace(placeholder, str(value))
            else:
                logger.warning(f"Provider '{provider_name}' not found in cache")
                result = result.replace(placeholder, f"?{provider_name}?")

        return result

    async def update_guild(self, guild_id):
        """
        Update a specific guild's nickname and status.
        Returns True if successful.
        """
        try:
            # Fetch provider data if cache is empty
            if not self.provider_cache:
                logger.info("Provider cache empty, fetching data...")
                await self.fetch_all_providers()

            # Get guild
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.warning(f"Guild {guild_id} not found")
                return False

            # Get config
            config = self.config_manager.get_guild_config(guild_id)

            # Render templates
            nickname_template = config.get("nickname_template", "")
            status_template = config.get("status_template", "")

            nickname = self.render_template(nickname_template)
            status = self.render_template(status_template)

            logger.info(f"Updating {guild.name}:")
            logger.info(f"  Nickname: {nickname}")
            logger.info(f"  Status: {status}")

            # Update nickname
            nickname_success = await self.bot.update_nickname(guild, nickname)

            # Update status (global, but we do it per guild for now)
            emotion = self.provider_cache.get('m', {}).get('emotion')
            status_success = await self.bot.update_status(status, emotion=emotion)

            return nickname_success or status_success

        except Exception as e:
            logger.error(f"Error updating guild {guild_id}: {e}")
            return False

    async def update_all_guilds(self):
        """
        Update all guilds the bot is in.
        Returns dict of guild_id -> success.
        """
        # First, fetch all provider data
        await self.fetch_all_providers()

        # Update each guild
        results = {}
        for guild in self.bot.guilds:
            success = await self.update_guild(guild.id)
            results[guild.id] = success

        # Log summary
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Update complete: {successful}/{len(results)} guilds updated successfully")

        return results
