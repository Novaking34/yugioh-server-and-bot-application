#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Discord Bot Configuration Engine
=============================================================================
Centralizes all settings, intents, and guild configurations for
The Great Kasutamaiza modular Discord bot:
- Discord Bot Token resolution (with fallback to config.json)
- Target Guild ID for application slash commands (/)
- Command prefix for non-slash commands
- Database path resolution for card lookups and player deckbuilding
=============================================================================
"""

import os
import sys
import json
from typing import Dict, Any, Optional

from config.paths import BASE_DIR, STORY_DB_PATH, BOT_DIR
from config.settings import settings


def load_bot_config() -> Dict[str, Any]:
    """Load and resolve Discord bot configuration dictionary.
    
    Resolution Priority:
    1. Environment variables / .env (via config.settings)
    2. Local discord_bot/config.json (if present)
    3. Default fallbacks
    
    Returns:
        Dict[str, Any]: Resolved dictionary containing:
            - token (str): Discord Bot Token
            - prefix (str): Command prefix string
            - guild_id (Optional[int]): Guild/server ID for slash command synchronization
            - client_id (Optional[int]): Application client ID
            - db_path (str): Filesystem path to SQLite story database
            - base_dir (str): Project root directory path
    """
    token = settings.discord.bot_token
    prefix = settings.discord.command_prefix
    guild_id = settings.discord.guild_id
    client_id = settings.discord.client_id

    # Check for legacy JSON override file if present
    local_json = os.path.join(BOT_DIR, "config.json")
    if os.path.exists(local_json):
        try:
            with open(local_json, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = token or cfg.get("token")
                prefix = cfg.get("prefix", prefix)
                if cfg.get("guild_id"):
                    guild_id = int(cfg.get("guild_id"))
        except Exception:
            pass

    return {
        "token": token,
        "prefix": prefix,
        "guild_id": guild_id,
        "client_id": client_id,
        "db_path": STORY_DB_PATH,
        "base_dir": BASE_DIR,
    }


# Global configuration instance exported for bot runners and cogs
BOT_CONFIG: Dict[str, Any] = load_bot_config()


if __name__ == "__main__":
    print(f"Bot Guild ID  : {BOT_CONFIG.get('guild_id')}")
    print(f"Bot Prefix    : {BOT_CONFIG.get('prefix')}")
    print(f"Database Path : {BOT_CONFIG.get('db_path')}")
    print(f"Token Present : {'Yes' if BOT_CONFIG.get('token') else 'No'}")
