"""
=============================================================================
Yu-Gi-Oh! Platform - Centralized Configuration Subsystem
=============================================================================
Provides a unified access point for all configuration layers:
1. Canonical Filesystem Paths (config.paths)
2. Strongly-Typed Environment & Network Settings (config.settings)
3. Discord Bot Identity & Command Profiles (config.bot)
4. Client JSON Connection Manifest (config/client/config.json)
5. Live Duel Simulator Settings (config/simulator/)
=============================================================================
"""

from config.paths import (
    BASE_DIR,
    CONFIG_DIR,
    CLIENT_CONFIG_DIR,
    CLIENT_CONFIG_PATH,
    BOT_CONFIG_DIR,
    BOT_EXAMPLE_CONFIG_PATH,
    ENV_FILE_PATH,
    ENV_EXAMPLE_PATH,
    SIMULATOR_CONFIG_DIR,
    SIMULATOR_CONFIG_JSON,
    SIMULATOR_ADMIN_JSON,
    SIMULATOR_BADWORDS_JSON,
    SIMULATOR_DIALOGUES_JSON,
    SIMULATOR_TIPS_JSON,
    DNS_CONFIG_DIR,
    DNS_ZONE_FILE_PATH,
    PROD_DIR,
    DEV_DIR,
    PACKAGES_DIR,
    DIST_DIR,
    PROD_MAIN_DIR,
    SIMULATOR_DIR,
    SIMULATOR_REPLAYS_DIR,
    WEB_DIR,
    STORY_DB_PATH,
    TEMPLATES_DIR,
    BOT_DIR,
    BOT_COGS_DIR,
    ASSETS_DIR,
    ICON_PATH,
    APP_PY_PATH,
    PROD_SHARED_DIR,
    EXPANSIONS_DIR,
    CDB_OUTPUT_PATH,
    SCRIPTS_DIR,
    DECKS_DIR,
    SERVER_PACKAGE_DIR,
    CLIENT_PACKAGE_DIR,
    CLIENT_ZIP_PATH,
    SERVER_TAR_PATH,
    CHECKSUMS_PATH,
    TOOLS_DIR,
    TESTS_DIR,
    DATABASE_DIR,
    SCHEMA_PATH,
    SEED_SCRIPT_PATH,
    DOCS_DIR,
    get_all_runtime_directories,
    ensure_directories,
)

from config.settings import (
    Settings,
    settings,
    PlatformConfig,
    NetworkConfig,
    SimulatorConfig,
    DiscordConfig,
    CloudflareConfig,
    DuckDNSConfig,
    StorageConfig,
    PipelineConfig,
)

from config.bot import (
    load_bot_config,
    BOT_CONFIG,
)

__all__ = [
    # Global Settings Singleton
    "settings",
    "Settings",
    "PlatformConfig",
    "NetworkConfig",
    "SimulatorConfig",
    "DiscordConfig",
    "CloudflareConfig",
    "DuckDNSConfig",
    "StorageConfig",
    "PipelineConfig",
    # Discord Bot Config
    "load_bot_config",
    "BOT_CONFIG",
    # Path Constants
    "BASE_DIR",
    "CONFIG_DIR",
    "CLIENT_CONFIG_DIR",
    "CLIENT_CONFIG_PATH",
    "BOT_CONFIG_DIR",
    "BOT_EXAMPLE_CONFIG_PATH",
    "ENV_FILE_PATH",
    "ENV_EXAMPLE_PATH",
    "SIMULATOR_CONFIG_DIR",
    "SIMULATOR_CONFIG_JSON",
    "SIMULATOR_ADMIN_JSON",
    "SIMULATOR_BADWORDS_JSON",
    "SIMULATOR_DIALOGUES_JSON",
    "SIMULATOR_TIPS_JSON",
    "DNS_CONFIG_DIR",
    "DNS_ZONE_FILE_PATH",
    "PROD_DIR",
    "DEV_DIR",
    "PACKAGES_DIR",
    "DIST_DIR",
    "PROD_MAIN_DIR",
    "SIMULATOR_DIR",
    "SIMULATOR_REPLAYS_DIR",
    "WEB_DIR",
    "STORY_DB_PATH",
    "TEMPLATES_DIR",
    "BOT_DIR",
    "BOT_COGS_DIR",
    "ASSETS_DIR",
    "ICON_PATH",
    "APP_PY_PATH",
    "PROD_SHARED_DIR",
    "EXPANSIONS_DIR",
    "CDB_OUTPUT_PATH",
    "SCRIPTS_DIR",
    "DECKS_DIR",
    "SERVER_PACKAGE_DIR",
    "CLIENT_PACKAGE_DIR",
    "CLIENT_ZIP_PATH",
    "SERVER_TAR_PATH",
    "CHECKSUMS_PATH",
    "TOOLS_DIR",
    "TESTS_DIR",
    "DATABASE_DIR",
    "SCHEMA_PATH",
    "SEED_SCRIPT_PATH",
    "DOCS_DIR",
    # Helper Functions
    "get_all_runtime_directories",
    "ensure_directories",
]


