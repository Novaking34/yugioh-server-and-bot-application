#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Centralized Path Resolution Module
=============================================================================
Defines standard, canonical filesystem paths across the entire platform
architecture, ensuring consistent access across all runtime modules:
- Configuration Subsystem: config/ (settings, paths, simulator, bot, client)
- Server Services: production/main/ (web, discord bot, simulator, desktop GUI)
- Client Distribution: production/shared/ & packages/client/ (expansions, decks)
- Release Packaging: dist/ & packages/ (standalone installation packages)
- Development & Tooling: development/ (tools, database schemas, test suite, docs)
=============================================================================
"""

import os
import sys
from typing import List

# =============================================================================
# 1. Base Directory Resolution
# =============================================================================
# Root directory of the repository (/home/.../yugioh-server)
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure BASE_DIR is present in Python's module search path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# =============================================================================
# 2. Configuration Subsystem Paths (config/)
# =============================================================================
CONFIG_DIR: str = os.path.join(BASE_DIR, "config")

# Client connection manifest folder & file
CLIENT_CONFIG_DIR: str = os.path.join(CONFIG_DIR, "client")
CLIENT_CONFIG_PATH: str = os.path.join(CLIENT_CONFIG_DIR, "config.json")

# Discord bot configuration folder & template
BOT_CONFIG_DIR: str = os.path.join(CONFIG_DIR, "bot")
BOT_EXAMPLE_CONFIG_PATH: str = os.path.join(BOT_CONFIG_DIR, "config.example.json")

# Environment secret files
ENV_FILE_PATH: str = os.path.join(BASE_DIR, ".env")
ENV_EXAMPLE_PATH: str = os.path.join(BASE_DIR, ".env.example")

# Simulator configuration folder containing room config, bans, and dialogues
SIMULATOR_CONFIG_DIR: str = os.path.join(CONFIG_DIR, "simulator")
SIMULATOR_CONFIG_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "config.json")
SIMULATOR_ADMIN_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "admin_user.json")
SIMULATOR_BADWORDS_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "badwords.json")
SIMULATOR_DIALOGUES_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "dialogues.json")
SIMULATOR_TIPS_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "tips.json")

# DNS & domain configuration folder and BIND zone file
DNS_CONFIG_DIR: str = os.path.join(CONFIG_DIR, "dns")
DNS_ZONE_FILE_PATH: str = os.path.join(DNS_CONFIG_DIR, "thelandofkustomazi.com.zone")

# =============================================================================
# 3. Top-Level Architectural Folders
# =============================================================================
PROD_DIR: str = os.path.join(BASE_DIR, "production")
DEV_DIR: str = os.path.join(BASE_DIR, "development")
PACKAGES_DIR: str = os.path.join(BASE_DIR, "packages")
DIST_DIR: str = os.path.join(BASE_DIR, "dist")
LOGS_DIR: str = os.path.join(BASE_DIR, "logs")


# =============================================================================
# 4. Production Main: Host Server Services (production/main/)
# =============================================================================
PROD_MAIN_DIR: str = os.path.join(PROD_DIR, "main")

# Simulator runtime paths
SIMULATOR_DIR: str = os.path.join(PROD_MAIN_DIR, "simulator")
SIMULATOR_REPLAYS_DIR: str = os.path.join(SIMULATOR_DIR, "replays")

# FastAPI Web Catalog & Lore Database
WEB_DIR: str = os.path.join(PROD_MAIN_DIR, "web")
STORY_DB_PATH: str = os.path.join(WEB_DIR, "ygo_story.db")
TEMPLATES_DIR: str = os.path.join(WEB_DIR, "templates")

# The Great Kasutamaiza Discord Bot
BOT_DIR: str = os.path.join(PROD_MAIN_DIR, "discord_bot")
BOT_COGS_DIR: str = os.path.join(BOT_DIR, "cogs")

# Desktop Platform Manager GUI & Assets
ASSETS_DIR: str = os.path.join(PROD_MAIN_DIR, "assets")
ICON_PATH: str = os.path.join(ASSETS_DIR, "icon.png")
APP_PY_PATH: str = os.path.join(PROD_MAIN_DIR, "app.py")

# =============================================================================
# 5. Production Shared: Client Expansions & Decks (production/shared/)
# =============================================================================
PROD_SHARED_DIR: str = os.path.join(PROD_DIR, "shared")
EXPANSIONS_DIR: str = os.path.join(PROD_SHARED_DIR, "expansions")
CDB_OUTPUT_PATH: str = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR: str = os.path.join(EXPANSIONS_DIR, "scripts")
DECKS_DIR: str = os.path.join(PROD_SHARED_DIR, "decks")

# =============================================================================
# 6. Installation Packages (packages/ & dist/)
# =============================================================================
SERVER_PACKAGE_DIR: str = os.path.join(PACKAGES_DIR, "server")
CLIENT_PACKAGE_DIR: str = os.path.join(PACKAGES_DIR, "client")

# Standalone release archive paths
CLIENT_ZIP_PATH: str = os.path.join(DIST_DIR, "ygo-client-package.zip")
SERVER_TAR_PATH: str = os.path.join(DIST_DIR, "ygo-server-package.tar.gz")
CHECKSUMS_PATH: str = os.path.join(DIST_DIR, "SHA256SUMS.txt")

# =============================================================================
# 7. Development Tools, Tests, Schemas & Docs (development/)
# =============================================================================
TOOLS_DIR: str = os.path.join(DEV_DIR, "tools")
TESTS_DIR: str = os.path.join(DEV_DIR, "tests")
DATABASE_DIR: str = os.path.join(DEV_DIR, "database")
SCHEMA_PATH: str = os.path.join(DATABASE_DIR, "schema.sql")
SEED_SCRIPT_PATH: str = os.path.join(DATABASE_DIR, "seed_story_data.py")
DOCS_DIR: str = os.path.join(DEV_DIR, "docs")


def get_all_runtime_directories() -> List[str]:
    """Retrieve all directories required for runtime operation across the platform.
    
    Returns:
        List[str]: List of absolute filesystem directory paths.
    """
    return [
        CONFIG_DIR,
        BOT_CONFIG_DIR,
        CLIENT_CONFIG_DIR,
        DNS_CONFIG_DIR,
        SIMULATOR_CONFIG_DIR,
        SIMULATOR_REPLAYS_DIR,
        EXPANSIONS_DIR,
        SCRIPTS_DIR,
        DECKS_DIR,
        TEMPLATES_DIR,
        ASSETS_DIR,
        TOOLS_DIR,
        TESTS_DIR,
        DATABASE_DIR,
        DOCS_DIR,
        PACKAGES_DIR,
        SERVER_PACKAGE_DIR,
        CLIENT_PACKAGE_DIR,
        DIST_DIR,
        LOGS_DIR,
    ]


def ensure_directories() -> None:
    """Ensure all required runtime directories exist on the filesystem.
    
    Creates missing directories idempotently with appropriate permissions.
    """
    for d in get_all_runtime_directories():
        os.makedirs(d, exist_ok=True)


if __name__ == "__main__":
    ensure_directories()
    print(f"Yu-Gi-Oh! Platform Base Directory: {BASE_DIR}")
    print(f"Configuration Directory         : {CONFIG_DIR}")
    print(f"Story Database Path             : {STORY_DB_PATH}")
    print(f"Compiled CDB Path               : {CDB_OUTPUT_PATH}")
    print(f"Lua Scripts Directory           : {SCRIPTS_DIR}")
    print(f"Shared Decks Directory          : {DECKS_DIR}")
    print(f"Simulator Config Directory      : {SIMULATOR_CONFIG_DIR}")
