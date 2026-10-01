#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Server Platform - Centralized Path Definitions
=============================================================================
Defines standard paths across the organized architecture:
- Production Main (Server services: simulator, web catalog, discord bot, GUI)
- Production Shared (Client/Player distribution: CDB, Lua scripts, decks)
- Development (Tools, pipelines, schema, tests, docs)
=============================================================================
"""

import os
import sys

# Root directory of the repository
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Top-level folders
PROD_DIR = os.path.join(BASE_DIR, "production")
DEV_DIR = os.path.join(BASE_DIR, "development")

# Production: Main (Server Services)
PROD_MAIN_DIR = os.path.join(PROD_DIR, "main")
SIMULATOR_DIR = os.path.join(PROD_MAIN_DIR, "simulator")
SIMULATOR_CONFIG_DIR = os.path.join(SIMULATOR_DIR, "config")
SIMULATOR_REPLAYS_DIR = os.path.join(SIMULATOR_DIR, "replays")

WEB_DIR = os.path.join(PROD_MAIN_DIR, "web")
STORY_DB_PATH = os.path.join(WEB_DIR, "ygo_story.db")
TEMPLATES_DIR = os.path.join(WEB_DIR, "templates")

BOT_DIR = os.path.join(PROD_MAIN_DIR, "discord_bot")
ASSETS_DIR = os.path.join(PROD_MAIN_DIR, "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
APP_PY_PATH = os.path.join(PROD_MAIN_DIR, "app.py")

# Production: Shared (Clients / Players / Distribution)
PROD_SHARED_DIR = os.path.join(PROD_DIR, "shared")
EXPANSIONS_DIR = os.path.join(PROD_SHARED_DIR, "expansions")
CDB_OUTPUT_PATH = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR = os.path.join(EXPANSIONS_DIR, "scripts")
DECKS_DIR = os.path.join(PROD_SHARED_DIR, "decks")

# Development (Tools, Tests, DB migrations, Docs)
TOOLS_DIR = os.path.join(DEV_DIR, "tools")
TESTS_DIR = os.path.join(DEV_DIR, "tests")
DATABASE_DIR = os.path.join(DEV_DIR, "database")
SCHEMA_PATH = os.path.join(DATABASE_DIR, "schema.sql")
SEED_SCRIPT_PATH = os.path.join(DATABASE_DIR, "seed_story_data.py")
DOCS_DIR = os.path.join(DEV_DIR, "docs")


def ensure_directories():
    """Ensure all required runtime directories exist."""
    dirs = [
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
        DOCS_DIR
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


if __name__ == "__main__":
    ensure_directories()
    print("Project Base Dir:", BASE_DIR)
    print("Story Database  :", STORY_DB_PATH)
    print("Compiled CDB    :", CDB_OUTPUT_PATH)
    print("Lua Scripts Dir :", SCRIPTS_DIR)
    print("Decks Dir       :", DECKS_DIR)
