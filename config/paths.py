#!/usr/bin/env python3
"""
=============================================================================
BLOCK 1: METADATA BLOCK
=============================================================================
Module: config.paths
Architecture: Platform Path Resolution & Filesystem Hierarchy Manifest
Domain: Cross-Subsystem Filesystem Standards & Directory Bootstrapping
Description: Centralized authority for all filesystem paths across the entire
             platform. Organizes all assets, relational stores, binary
             compilations, trackers, decks, and simulator configurations under
             the unified data/ directory, with clean separation from code and
             deployment packages.

Invariants:
  - All paths are absolute, derived dynamically from BASE_DIR.
  - DATA_DIR (/data) is the singular root for all persistent and compiled data.
  - ensure_directories() creates all runtime operational paths idempotently.
=============================================================================
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Base Path Resolution)
# =============================================================================
import os
import sys
from typing import List

# Root directory of the repository (/home/.../yugioh-server)
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure BASE_DIR is present in Python's module search path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# =============================================================================
# BLOCK 3: BODY BLOCK (Core Path Hierarchy & Subsystem Specifications)
# =============================================================================

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.1: Unified Data Subsystem Paths (data/)
# -----------------------------------------------------------------------------
DATA_DIR: str = os.path.join(BASE_DIR, "data")

# 1. Authoritative Master Stores (Single Source of Truth)
AUTHORITATIVE_DATA_DIR: str = os.path.join(DATA_DIR, "authoritative")
CONTENT_DB_PATH: str = os.path.join(AUTHORITATIVE_DATA_DIR, "content.db")
STORY_DB_PATH: str = CONTENT_DB_PATH  # Direct alias to authoritative content store
SCHEMA_PATH: str = os.path.join(AUTHORITATIVE_DATA_DIR, "schema.sql")
SCHEMA_CONTENT_PATH: str = os.path.join(AUTHORITATIVE_DATA_DIR, "schema_content.sql")
SCHEMA_TELEMETRY_PATH: str = os.path.join(AUTHORITATIVE_DATA_DIR, "schema_telemetry.sql")
SEED_SCRIPT_PATH: str = os.path.join(AUTHORITATIVE_DATA_DIR, "seed_databases.py")
DATABASE_DIR: str = AUTHORITATIVE_DATA_DIR  # Canonical backward-compatibility alias

# 2. Master Card Trackers (Spreadsheets & Ingestion Data)
TRACKERS_DIR: str = os.path.join(DATA_DIR, "trackers")
DEFAULT_TRACKER_CSV: str = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv")
DEFAULT_TRACKER_TSV: str = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv")

# 3. Card Artwork Assets (Raw High-Res Originals)
ARTWORK_DIR: str = os.path.join(DATA_DIR, "artwork")
RAW_CARD_ART_DIR: str = os.path.join(ARTWORK_DIR, "raw")

# 4. Compiled Simulator Engine Expansions
EXPANSIONS_DIR: str = os.path.join(DATA_DIR, "expansions")
CDB_OUTPUT_PATH: str = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR: str = os.path.join(EXPANSIONS_DIR, "scripts")
PICS_DIR: str = os.path.join(EXPANSIONS_DIR, "pics")
THUMBNAILS_DIR: str = os.path.join(PICS_DIR, "thumbnail")

# 5. Pre-Made Story & Character Decks (.ydk format)
DECKS_DIR: str = os.path.join(DATA_DIR, "decks")

# 6. Canonical World Lore & Story Campaign Seed Data
LORE_DATA_DIR: str = os.path.join(DATA_DIR, "lore")
STORY_DATA_DIR: str = os.path.join(DATA_DIR, "story")

# 7. Simulator Runtime Datasets & Replay Telemetry
SIMULATOR_DATA_DIR: str = os.path.join(DATA_DIR, "simulator")
SIMULATOR_DIR: str = SIMULATOR_DATA_DIR
SIMULATOR_CONFIG_DIR: str = os.path.join(SIMULATOR_DATA_DIR, "config")
SIMULATOR_CONFIG_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "config.json")
SIMULATOR_ADMIN_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "admin_user.json")
SIMULATOR_BADWORDS_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "badwords.json")
SIMULATOR_DIALOGUES_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "dialogues.json")
SIMULATOR_TIPS_JSON: str = os.path.join(SIMULATOR_CONFIG_DIR, "tips.json")
SIMULATOR_REPLAYS_DIR: str = os.path.join(SIMULATOR_DATA_DIR, "replays")

# 8. Dynamic Telemetry & Competitive Player Runtime Database
TELEMETRY_DATA_DIR: str = os.path.join(DATA_DIR, "telemetry")
TELEMETRY_DB_PATH: str = os.path.join(TELEMETRY_DATA_DIR, "telemetry.db")

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.2: Configuration Subsystem Paths (config/)
# -----------------------------------------------------------------------------
CONFIG_DIR: str = os.path.join(BASE_DIR, "config")
LOGGING_CONFIG_DIR: str = os.path.join(CONFIG_DIR, "logging")
DEBUGGER_CONFIG_DIR: str = os.path.join(CONFIG_DIR, "debugger")

ENV_FILE_PATH: str = os.path.join(BASE_DIR, ".env")
ENV_EXAMPLE_PATH: str = os.path.join(BASE_DIR, ".env.example")

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.3: Production Main Server Services (production/main/)
# -----------------------------------------------------------------------------
PROD_DIR: str = os.path.join(BASE_DIR, "production")
PROD_MAIN_DIR: str = os.path.join(PROD_DIR, "main")
PROD_SHARED_DIR: str = os.path.join(PROD_DIR, "shared")

# FastAPI Web Catalog
WEB_DIR: str = os.path.join(PROD_MAIN_DIR, "web")
TEMPLATES_DIR: str = os.path.join(WEB_DIR, "templates")
STATIC_DIR: str = os.path.join(WEB_DIR, "static")

# Discord Bot
BOT_DIR: str = os.path.join(PROD_MAIN_DIR, "discord_bot")
BOT_COGS_DIR: str = os.path.join(BOT_DIR, "cogs")
BOT_CONFIG_DIR: str = BOT_DIR
BOT_CONFIG_PATH: str = os.path.join(BOT_DIR, "config.json")
BOT_EXAMPLE_CONFIG_PATH: str = os.path.join(BOT_DIR, "config.example.json")

# Desktop Platform Manager GUI & Static UI Assets
ASSETS_DIR: str = os.path.join(PROD_MAIN_DIR, "assets")
ICON_PATH: str = os.path.join(ASSETS_DIR, "icon.png")
APP_PY_PATH: str = os.path.join(PROD_MAIN_DIR, "app.py")

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.4: Development, Packaging & Documentation Paths
# -----------------------------------------------------------------------------
DEV_DIR: str = os.path.join(BASE_DIR, "development")
TOOLS_DIR: str = os.path.join(DEV_DIR, "tools")
TESTS_DIR: str = os.path.join(DEV_DIR, "tests")
TESTS_UNIT_DIR: str = os.path.join(TESTS_DIR, "unit")
TESTS_INTEGRATION_DIR: str = os.path.join(TESTS_DIR, "integration")
TESTS_FUNCTIONAL_DIR: str = os.path.join(TESTS_DIR, "functional")
DEV_DOCS_DIR: str = os.path.join(DEV_DIR, "docs")
DOCS_DIR: str = os.path.join(BASE_DIR, "docs")

PACKAGES_DIR: str = os.path.join(BASE_DIR, "packages")
SERVER_PACKAGE_DIR: str = os.path.join(PACKAGES_DIR, "server")
CLIENT_PACKAGE_DIR: str = os.path.join(PACKAGES_DIR, "client")
CLIENT_CONFIG_DIR: str = CLIENT_PACKAGE_DIR
CLIENT_CONFIG_PATH: str = os.path.join(CLIENT_PACKAGE_DIR, "config.json")
DNS_CONFIG_DIR: str = os.path.join(SERVER_PACKAGE_DIR, "dns")
DNS_ZONE_FILE_PATH: str = os.path.join(DNS_CONFIG_DIR, "thelandofkustomazi.com.zone")

DIST_DIR: str = os.path.join(BASE_DIR, "dist")
CLIENT_ZIP_PATH: str = os.path.join(DIST_DIR, "ygo-client-package.zip")
SERVER_TAR_PATH: str = os.path.join(DIST_DIR, "ygo-server-package.tar.gz")
CHECKSUMS_PATH: str = os.path.join(DIST_DIR, "SHA256SUMS.txt")

LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
COMBINED_LOG_PATH: str = os.path.join(LOGS_DIR, "combined.log")
ERRORS_LOG_PATH: str = os.path.join(LOGS_DIR, "errors.log")
AUDIT_LOG_PATH: str = os.path.join(LOGS_DIR, "audit.jsonl")
DEBUG_SNAPSHOTS_DIR: str = os.path.join(LOGS_DIR, "debug_snapshots")

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.5: Directory Verification & Idempotent Bootstrap
# -----------------------------------------------------------------------------
def get_all_runtime_directories() -> List[str]:
    """Retrieve all directories required for runtime operation across the platform.
    
    Returns:
        List[str]: List of absolute filesystem directory paths.
    """
    return [
        DATA_DIR,
        AUTHORITATIVE_DATA_DIR,
        TRACKERS_DIR,
        ARTWORK_DIR,
        RAW_CARD_ART_DIR,
        EXPANSIONS_DIR,
        SCRIPTS_DIR,
        PICS_DIR,
        THUMBNAILS_DIR,
        DECKS_DIR,
        LORE_DATA_DIR,
        STORY_DATA_DIR,
        TELEMETRY_DATA_DIR,
        SIMULATOR_DATA_DIR,
        SIMULATOR_CONFIG_DIR,
        SIMULATOR_REPLAYS_DIR,
        CONFIG_DIR,
        BOT_CONFIG_DIR,
        CLIENT_CONFIG_DIR,
        DNS_CONFIG_DIR,
        LOGGING_CONFIG_DIR,
        DEBUGGER_CONFIG_DIR,
        TEMPLATES_DIR,
        STATIC_DIR,
        ASSETS_DIR,
        TOOLS_DIR,
        TESTS_DIR,
        DOCS_DIR,
        PACKAGES_DIR,
        SERVER_PACKAGE_DIR,
        CLIENT_PACKAGE_DIR,
        DIST_DIR,
        LOGS_DIR,
        DEBUG_SNAPSHOTS_DIR,
    ]


def ensure_directories() -> None:
    """Ensure all required runtime directories exist on the filesystem.
    
    Creates missing directories idempotently with appropriate permissions.
    """
    for d in get_all_runtime_directories():
        os.makedirs(d, exist_ok=True)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports, Diagnostic Manifest & CLI Execution)
# =============================================================================

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "AUTHORITATIVE_DATA_DIR",
    "CONTENT_DB_PATH",
    "STORY_DB_PATH",
    "SCHEMA_PATH",
    "SCHEMA_CONTENT_PATH",
    "SCHEMA_TELEMETRY_PATH",
    "SEED_SCRIPT_PATH",
    "DATABASE_DIR",
    "TRACKERS_DIR",
    "DEFAULT_TRACKER_CSV",
    "DEFAULT_TRACKER_TSV",
    "ARTWORK_DIR",
    "RAW_CARD_ART_DIR",
    "EXPANSIONS_DIR",
    "CDB_OUTPUT_PATH",
    "SCRIPTS_DIR",
    "PICS_DIR",
    "THUMBNAILS_DIR",
    "DECKS_DIR",
    "LORE_DATA_DIR",
    "STORY_DATA_DIR",
    "TELEMETRY_DATA_DIR",
    "TELEMETRY_DB_PATH",
    "SIMULATOR_DATA_DIR",
    "SIMULATOR_DIR",
    "SIMULATOR_CONFIG_DIR",
    "SIMULATOR_CONFIG_JSON",
    "SIMULATOR_ADMIN_JSON",
    "SIMULATOR_BADWORDS_JSON",
    "SIMULATOR_DIALOGUES_JSON",
    "SIMULATOR_TIPS_JSON",
    "SIMULATOR_REPLAYS_DIR",
    "CONFIG_DIR",
    "CLIENT_CONFIG_DIR",
    "CLIENT_CONFIG_PATH",
    "BOT_CONFIG_DIR",
    "BOT_CONFIG_PATH",
    "BOT_EXAMPLE_CONFIG_PATH",
    "DNS_CONFIG_DIR",
    "DNS_ZONE_FILE_PATH",
    "LOGGING_CONFIG_DIR",
    "DEBUGGER_CONFIG_DIR",
    "ENV_FILE_PATH",
    "ENV_EXAMPLE_PATH",
    "PROD_MAIN_DIR",
    "WEB_DIR",
    "TEMPLATES_DIR",
    "BOT_DIR",
    "BOT_COGS_DIR",
    "ASSETS_DIR",
    "ICON_PATH",
    "APP_PY_PATH",
    "DEV_DIR",
    "TOOLS_DIR",
    "TESTS_DIR",
    "TESTS_UNIT_DIR",
    "TESTS_INTEGRATION_DIR",
    "TESTS_FUNCTIONAL_DIR",
    "DOCS_DIR",
    "DEV_DOCS_DIR",
    "PACKAGES_DIR",
    "SERVER_PACKAGE_DIR",
    "CLIENT_PACKAGE_DIR",
    "CLIENT_ZIP_PATH",
    "SERVER_TAR_PATH",
    "CHECKSUMS_PATH",
    "DIST_DIR",
    "PROD_DIR",
    "PROD_SHARED_DIR",
    "LOGS_DIR",
    "COMBINED_LOG_PATH",
    "ERRORS_LOG_PATH",
    "AUDIT_LOG_PATH",
    "DEBUG_SNAPSHOTS_DIR",
    "get_all_runtime_directories",
    "ensure_directories",
]

if __name__ == "__main__":
    ensure_directories()
    print(f"Yu-Gi-Oh! Platform Base Directory: {BASE_DIR}")
    print(f"Unified Data Root (DATA_DIR)    : {DATA_DIR}")
    print(f"Authoritative SQLite DB Path    : {STORY_DB_PATH}")
    print(f"Master Card Trackers Directory  : {TRACKERS_DIR}")
    print(f"Compiled CDB Path               : {CDB_OUTPUT_PATH}")
    print(f"Lua Scripts Directory           : {SCRIPTS_DIR}")
    print(f"Card Artwork Images (PICS_DIR)  : {PICS_DIR}")
    print(f"Shared Decks Directory          : {DECKS_DIR}")
    print(f"Simulator Config Directory      : {SIMULATOR_CONFIG_DIR}")

