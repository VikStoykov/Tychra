import json
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class ConfigManager:
    
    DEFAULT_CONFIG = {
        "nickname_template": "F/G: {m.index}",
        "status_template": "{m.emotion} {m.emoji}",
        "timezone": "UTC"
    }
    
    def __init__(self, config_file = "guild_config.json"):
        self.config_file = config_file
        self.configs: Dict[str, dict] = {}
        self._load_config()
    
    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.configs = json.load(f)
                logger.info(f"Loaded config for {len(self.configs)} guilds")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.configs = {}
        else:
            logger.info("No existing config file, starting fresh")
            self.configs = {}
    
    def _save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
            logger.info(f"Saved config for {len(self.configs)} guilds")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_guild_config(self, guild_id):
        guild_id_str = str(guild_id)
        if guild_id_str not in self.configs:
            # Initialize with default config
            self.configs[guild_id_str] = self.DEFAULT_CONFIG.copy()
            self._save_config()
        return self.configs[guild_id_str].copy()
    
    def set_guild_template(self, guild_id, template_type, template):
        """
        Set a template for a guild.
        template_type: 'nickname' or 'status'
        Returns True if successful.
        """
        guild_id_str = str(guild_id)
        
        if guild_id_str not in self.configs:
            self.configs[guild_id_str] = self.DEFAULT_CONFIG.copy()
        
        if template_type == "nickname":
            # Validate nickname length (Discord limit is 32 chars)
            if len(template) > 32:
                logger.warning(f"Nickname template too long for guild {guild_id}")
                return False
            self.configs[guild_id_str]["nickname_template"] = template
        elif template_type == "status":
            self.configs[guild_id_str]["status_template"] = template
        else:
            logger.error(f"Invalid template type: {template_type}")
            return False
        
        self._save_config()
        logger.info(f"Updated {template_type} template for guild {guild_id}")
        return True
    
    def get_all_guild_ids(self):
        return [int(guild_id) for guild_id in self.configs.keys()]
    
    def remove_guild(self, guild_id: int):
        guild_id_str = str(guild_id)
        if guild_id_str in self.configs:
            del self.configs[guild_id_str]
            self._save_config()
            logger.info(f"Removed config for guild {guild_id}")
    
    def get_required_providers(self, guild_id):
        """
        Analyze templates to determine which providers are needed.
        Returns set of provider names.
        """
        config = self.get_guild_config(guild_id)
        providers = set()
        
        for template in [config.get("nickname_template", ""), config.get("status_template", "")]:
            # Simple parsing - look for {provider.key} patterns
            import re
            matches = re.findall(r'\{(\w+)\.\w+\}', template)
            providers.update(matches)

        return providers
