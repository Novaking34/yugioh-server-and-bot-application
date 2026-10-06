#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: production.main.discord_bot.bot_config
Architecture: Hybrid Systems Engineering (L2/L3 Domain Service Configuration)
Subsystem: The Great Kasutamaiza Discord Bot Platform
Description:
    Authoritative Discord Bot Configuration Subsystem.
    Provides strongly-typed runtime settings, credential resolution hierarchy,
    Discord gateway intents, UI theme color palettes, and two-tier SQLite attach bridge
    for The Great Kasutamaiza Discord bot platform.

Resolution Hierarchy:
    1. Environment variables (.env / OS environment via config.settings singleton)
    2. Local JSON overrides (production/main/discord_bot/config.json)
    3. Safe enterprise defaults

Exported Interface:
    - BOT_CONFIG: Canonical configuration dictionary for legacy cog consumers
    - BOT_SETTINGS: Strongly-typed BotRuntimeConfig dataclass instance
    - load_bot_config(): Fresh resolution loader function
    - get_runtime_settings(): Fresh typed configuration factory
    - get_bot_intents(): Discord Gateway Intents factory
    - UI theme color constants (EMBED_COLOR_DEFAULT, EMBED_COLOR_SUCCESS, etc.)
    - Two-tier SQLite attach bridge for aiosqlite
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Ensure project root is available in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_DIR)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config.paths import (
    BASE_DIR,
    CONTENT_DB_PATH,
    TELEMETRY_DB_PATH,
    STORY_DB_PATH,
    ENV_FILE_PATH,
    BOT_DIR,
)
from config.settings import settings

# Canonical Database & File Paths
DB_PATH: str = CONTENT_DB_PATH
CONTENT_DB: str = CONTENT_DB_PATH
TELEMETRY_DB: str = TELEMETRY_DB_PATH
ENV_PATH: str = ENV_FILE_PATH
CONFIG_PATH: str = os.path.join(_CURRENT_DIR, "config.json")
EXAMPLE_CONFIG_PATH: str = os.path.join(_CURRENT_DIR, "config.example.json")
BOT_EXAMPLE_CONFIG_PATH: str = EXAMPLE_CONFIG_PATH

# Two-tier SQLite attach bridge for aiosqlite
try:
    import aiosqlite
    if not getattr(aiosqlite, "_two_tier_attached", False):
        _original_aiosqlite_connect = aiosqlite.connect

        class _TwoTierContextManager:
            def __init__(self, db_path, *args, **kwargs):
                self._cm = _original_aiosqlite_connect(db_path, *args, **kwargs)
                self.db_path = str(db_path)

            async def __aenter__(self):
                conn = await self._cm.__aenter__()
                if (self.db_path == CONTENT_DB_PATH or self.db_path.endswith("content.db")) and os.path.exists(TELEMETRY_DB_PATH):
                    try:
                        await conn.execute(f"ATTACH DATABASE '{TELEMETRY_DB_PATH}' AS telemetry")
                    except Exception:
                        pass
                elif (self.db_path == TELEMETRY_DB_PATH or self.db_path.endswith("telemetry.db")) and os.path.exists(CONTENT_DB_PATH):
                    try:
                        await conn.execute(f"ATTACH DATABASE '{CONTENT_DB_PATH}' AS content")
                    except Exception:
                        pass
                return conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return await self._cm.__aexit__(exc_type, exc_val, exc_tb)

        aiosqlite.connect = _TwoTierContextManager
        aiosqlite._two_tier_attached = True
except ImportError:
    pass


# =============================================================================
# BLOCK 3: BODY BLOCK (Configuration Architecture & Theme Foundations)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Canonical UI & Embed Theme Color Palettes
# -----------------------------------------------------------------------------
EMBED_COLOR_DEFAULT: int = 0x1E1F22    # Discord dark theme neutral background
EMBED_COLOR_INFO: int = 0x58A6FF       # Informational / Blue
EMBED_COLOR_SUCCESS: int = 0x57F287    # Success / Green
EMBED_COLOR_WARNING: int = 0xFEE75C    # Cautionary / Amber
EMBED_COLOR_ERROR: int = 0xED4245      # Diagnostic failpoint / Red
EMBED_COLOR_PRIMARY: int = 0x8957E5    # Special Summon / Magic Purple
EMBED_COLOR_GOLD: int = 0xD4AF37       # Divine / Tournament Gold


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Strongly-Typed Bot Runtime Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class BotRuntimeConfig:
    """Strongly-typed runtime configuration for The Great Kasutamaiza Discord Bot."""
    token: Optional[str]
    prefix: str
    guild_id: Optional[int]
    client_id: Optional[int]
    db_path: str
    content_db_path: str
    telemetry_db_path: str
    story_db_path: str
    base_dir: str
    bot_dir: str
    config_path: str
    env_path: str

    @property
    def is_configured(self) -> bool:
        """Returns True if bot token is non-empty, non-placeholder, and configured."""
        return bool(self.token and len(self.token.strip()) > 10 and "YOUR_DISCORD_BOT_TOKEN" not in self.token)

    def to_dict(self) -> Dict[str, Any]:
        """Convert runtime configuration to dictionary for legacy cog consumers."""
        return {
            "token": self.token,
            "prefix": self.prefix,
            "guild_id": self.guild_id,
            "client_id": self.client_id,
            "db_path": self.db_path,
            "content_db_path": self.content_db_path,
            "telemetry_db_path": self.telemetry_db_path,
            "story_db_path": self.story_db_path,
            "base_dir": self.base_dir,
            "bot_dir": self.bot_dir,
            "config_path": self.config_path,
            "env_path": self.env_path,
            "is_configured": self.is_configured,
        }


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Configuration Resolution Engine
# -----------------------------------------------------------------------------
def load_bot_config() -> Dict[str, Any]:
    """Load and resolve the authoritative Discord bot configuration dictionary.
    
    Inspects environment variables first via the centralized `settings` singleton,
    then checks for optional local JSON override configuration files for local
    developer workflows or container volume overrides.
    
    Returns:
        Dict[str, Any]: Resolved dictionary containing:
            - token (Optional[str]): Discord Bot Token
            - prefix (str): Command prefix string (default: '!')
            - guild_id (Optional[int]): Target Guild ID for instant slash command sync
            - client_id (Optional[int]): Application client ID
            - db_path (str): Canonical path to content database
            - content_db_path (str): Path to authoritative content store
            - telemetry_db_path (str): Path to dynamic telemetry store
            - story_db_path (str): Backward-compatibility alias
            - base_dir (str): Canonical project root directory path
            - bot_dir (str): Canonical bot package directory path
            - config_path (str): Path to active config.json override
            - env_path (str): Path to root .env file
            - is_configured (bool): Validation status flag
    """
    token: Optional[str] = settings.discord.bot_token
    prefix: str = settings.discord.command_prefix
    guild_id: Optional[int] = settings.discord.guild_id
    client_id: Optional[int] = settings.discord.client_id

    # Check for local JSON override file in production/main/discord_bot/config.json
    local_bot_json = CONFIG_PATH
    if os.path.exists(local_bot_json) and not os.path.islink(local_bot_json):
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

    is_valid = bool(token and len(token.strip()) > 10 and "YOUR_DISCORD_BOT_TOKEN" not in token)

    return {
        "token": token,
        "prefix": prefix,
        "guild_id": guild_id,
        "client_id": client_id,
        "db_path": DB_PATH,
        "content_db_path": CONTENT_DB,
        "telemetry_db_path": TELEMETRY_DB,
        "story_db_path": STORY_DB_PATH,
        "base_dir": BASE_DIR,
        "bot_dir": _CURRENT_DIR,
        "config_path": CONFIG_PATH,
        "env_path": ENV_PATH,
        "is_configured": is_valid,
    }


def get_runtime_settings() -> BotRuntimeConfig:
    """Returns strongly-typed BotRuntimeConfig dataclass instance."""
    cfg = load_bot_config()
    return BotRuntimeConfig(
        token=cfg["token"],
        prefix=cfg["prefix"],
        guild_id=cfg["guild_id"],
        client_id=cfg["client_id"],
        db_path=cfg["db_path"],
        content_db_path=cfg["content_db_path"],
        telemetry_db_path=cfg["telemetry_db_path"],
        story_db_path=cfg["story_db_path"],
        base_dir=cfg["base_dir"],
        bot_dir=cfg["bot_dir"],
        config_path=cfg["config_path"],
        env_path=cfg["env_path"],
    )


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Discord Gateway Intents Factory
# -----------------------------------------------------------------------------
def get_bot_intents(with_privileged: bool = True) -> Any:
    """Constructs and returns discord.Intents instance for bot lifecycle initialization."""
    try:
        import discord
        intents = discord.Intents.default()
        if with_privileged:
            intents.message_content = True
            intents.members = True
        return intents
    except ImportError:
        return None


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest & CLI Inspector)
# =============================================================================

# Global configuration singletons
BOT_CONFIG: Dict[str, Any] = load_bot_config()
BOT_SETTINGS: BotRuntimeConfig = get_runtime_settings()

__all__ = [
    # Configuration Singletons & Factories
    "BOT_CONFIG",
    "BOT_SETTINGS",
    "BotRuntimeConfig",
    "load_bot_config",
    "get_runtime_settings",
    "get_bot_intents",
    # UI Theme Palette Constants
    "EMBED_COLOR_DEFAULT",
    "EMBED_COLOR_INFO",
    "EMBED_COLOR_SUCCESS",
    "EMBED_COLOR_WARNING",
    "EMBED_COLOR_ERROR",
    "EMBED_COLOR_PRIMARY",
    "EMBED_COLOR_GOLD",
    # Canonical Paths
    "BASE_DIR",
    "DB_PATH",
    "CONTENT_DB",
    "TELEMETRY_DB",
    "CONFIG_PATH",
    "ENV_PATH",
    "EXAMPLE_CONFIG_PATH",
    "BOT_EXAMPLE_CONFIG_PATH",
]


if __name__ == "__main__":
    print("=== 🤖 Yu-Gi-Oh! Discord Bot Authoritative Configuration ===")
    print(f"Token Configured : {'Yes' if BOT_SETTINGS.is_configured else 'No'}")
    print(f"Target Guild ID  : {BOT_SETTINGS.guild_id}")
    print(f"Command Prefix   : {BOT_SETTINGS.prefix}")
    print(f"Client ID        : {BOT_SETTINGS.client_id}")
    print(f"Content DB Path  : {BOT_SETTINGS.content_db_path}")
    print(f"Telemetry DB Path: {BOT_SETTINGS.telemetry_db_path}")
    print(f"Base Directory   : {BOT_SETTINGS.base_dir}")
    print(f"Bot Directory    : {BOT_SETTINGS.bot_dir}")
