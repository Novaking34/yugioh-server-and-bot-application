#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Discord Bot Configuration Subsystem
=============================================================================
Centralizes all settings, intents, credentials, and guild configurations for
The Great Kasutamaiza modular Discord bot:
- Discord Bot Token resolution (with fallback hierarchy)
- Target Guild ID for instant application slash command (/) synchronization
- Command prefix for standard message-based commands
- SQLite Story Database path resolution for card lookups and custom deckbuilding
- Application Client ID for OAuth2 invite generation

Resolution Hierarchy:
1. Environment variables (DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_COMMAND_PREFIX)
2. Centralized settings singleton (config.settings)
3. Local JSON override files (config/bot/config.json or production/main/discord_bot/config.json)
4. Safe defaults
=============================================================================
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# Ensure project root is available in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.dirname(_CURRENT_DIR)
_BASE_DIR = os.path.dirname(_CONFIG_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from config.paths import BASE_DIR, STORY_DB_PATH, BOT_DIR
from config.settings import settings


def load_bot_config() -> Dict[str, Any]:
    """Load and resolve the active Discord bot configuration dictionary.
    
    Inspects environment variables first via the centralized `settings` singleton,
    then checks for optional local JSON override configuration files for local
    developer workflows or container volume overrides.
    
    Returns:
        Dict[str, Any]: Resolved dictionary containing:
            - token (Optional[str]): Discord Bot Token
            - prefix (str): Command prefix string (e.g. '!')
            - guild_id (Optional[int]): Guild/server ID for slash command synchronization
            - client_id (Optional[int]): Application client ID
            - db_path (str): Canonical filesystem path to SQLite story database
            - base_dir (str): Canonical project root directory path
    """
    token: Optional[str] = settings.discord.bot_token
    prefix: str = settings.discord.command_prefix
    guild_id: Optional[int] = settings.discord.guild_id
    client_id: Optional[int] = settings.discord.client_id

    # Check for local JSON override file in config/bot/config.json
    local_bot_json = os.path.join(_CURRENT_DIR, "config.json")
    if os.path.exists(local_bot_json):
        try:
            with open(local_bot_json, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = cfg.get("token") or token
                prefix = cfg.get("prefix", prefix)
                if cfg.get("guild_id"):
                    guild_id = int(cfg.get("guild_id"))
                if cfg.get("client_id"):
                    client_id = int(cfg.get("client_id"))
        except Exception as e:
            sys.stderr.write(f"[WARN] Failed to parse {local_bot_json}: {e}\n")

    # Check for legacy JSON override file in production/main/discord_bot/config.json
    legacy_json = os.path.join(BOT_DIR, "config.json")
    if os.path.exists(legacy_json) and not os.path.islink(legacy_json):
        try:
            with open(legacy_json, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = cfg.get("token") or token
                prefix = cfg.get("prefix", prefix)
                if cfg.get("guild_id"):
                    guild_id = int(cfg.get("guild_id"))
                if cfg.get("client_id"):
                    client_id = int(cfg.get("client_id"))
        except Exception as e:
            sys.stderr.write(f"[WARN] Failed to parse {legacy_json}: {e}\n")

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

__all__ = [
    "load_bot_config",
    "BOT_CONFIG",
]


if __name__ == "__main__":
    print("=== 🤖 Yu-Gi-Oh! Discord Bot Configuration ===")
    print(f"Token Configured : {'Yes' if BOT_CONFIG.get('token') else 'No'}")
    print(f"Target Guild ID  : {BOT_CONFIG.get('guild_id')}")
    print(f"Command Prefix   : {BOT_CONFIG.get('prefix')}")
    print(f"Client ID        : {BOT_CONFIG.get('client_id')}")
    print(f"Story DB Path    : {BOT_CONFIG.get('db_path')}")
    print(f"Base Directory   : {BOT_CONFIG.get('base_dir')}")
