#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Configuration & Environment Loader
=============================================================================
Resolves bot credentials, command prefixes, and database locations from:
1. Environment variables (DISCORD_BOT_TOKEN)
2. Project `.env` file
3. `discord_bot/config.json`
=============================================================================
"""

import os
import json
from typing import Dict, Any, Optional

try:
    from config.paths import STORY_DB_PATH, BASE_DIR
    DB_PATH = STORY_DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(BASE_DIR, "production", "main", "web", "ygo_story.db")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Automatically load .env if present
if os.path.exists(ENV_PATH):
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
    except ImportError:
        pass


def load_bot_config() -> Dict[str, Any]:
    """
    Loads bot configuration dictionary with defaults.
    """
    token = os.getenv("DISCORD_BOT_TOKEN")
    prefix = os.getenv("DISCORD_BOT_PREFIX", "!")
    guild_id = os.getenv("DISCORD_GUILD_ID")

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = token or cfg.get("token")
                prefix = cfg.get("prefix", prefix)
                guild_id = guild_id or cfg.get("guild_id")
        except Exception:
            pass

    return {
        "token": token,
        "prefix": prefix,
        "guild_id": int(guild_id) if guild_id else None,
        "db_path": DB_PATH,
        "base_dir": BASE_DIR
    }


BOT_CONFIG = load_bot_config()
