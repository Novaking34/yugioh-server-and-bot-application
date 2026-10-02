#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Configuration & Environment Loader (Compatibility Bridge)
=============================================================================
This module delegates configuration loading to the centralized engine at:
    config.bot (and config.settings)

It preserves backwards compatibility for all Discord cogs and runners:
- Exposes `BOT_CONFIG` dictionary
- Exposes `load_bot_config()` function
- Exposes canonical paths (`BASE_DIR`, `DB_PATH`, `CONFIG_PATH`, `ENV_PATH`)
=============================================================================
"""

import os
import sys
from typing import Dict, Any

# Ensure project root is available in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_DIR)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Import canonical paths and centralized bot loader
from config.paths import BASE_DIR, STORY_DB_PATH, ENV_FILE_PATH, BOT_EXAMPLE_CONFIG_PATH
from config.bot import load_bot_config, BOT_CONFIG

# Backwards compatibility path aliases
DB_PATH: str = STORY_DB_PATH
ENV_PATH: str = ENV_FILE_PATH
CONFIG_PATH: str = os.path.join(_CURRENT_DIR, "config.json")

__all__ = [
    "BOT_CONFIG",
    "load_bot_config",
    "BASE_DIR",
    "DB_PATH",
    "CONFIG_PATH",
    "ENV_PATH",
]


if __name__ == "__main__":
    print(f"Bot Guild ID  : {BOT_CONFIG.get('guild_id')}")
    print(f"Bot Prefix    : {BOT_CONFIG.get('prefix')}")
    print(f"Database Path : {BOT_CONFIG.get('db_path')}")
    print(f"Token Configured : {'Yes' if BOT_CONFIG.get('token') else 'No'}")

