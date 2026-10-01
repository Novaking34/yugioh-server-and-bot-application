#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Custom Server, Story Platform & Simulator Master CLI Manager
# =============================================================================
# This script orchestrates all subsystems:
# - Live Duel Simulator Container (ocgcore / EDOPro TCP: 7911, Web: 7922)
# - FastAPI Web Catalog & Lore Dashboard (Port: 8000)
# - Modular Discord Story Bot (Slash commands, Deckbuilder, Interactive Duels)
# - CDB Compiler, Lua Effect Generator & Duelingbook Importer Pipeline
# - Pytest Unit Test Suite & Lua Syntax Validation
# =============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

VENV_PYTHON="$BASE_DIR/venv/bin/python"
VENV_PYTEST="$BASE_DIR/venv/bin/pytest"

# Color constants for terminal formatting
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
NC="\033[0m" # No Color

case "$1" in
    start)
        echo -e "${BLUE}[*] Starting Yu-Gi-Oh! Live Duel Simulator (ygoserver container)...${NC}"
        docker compose up -d
        echo -e "${GREEN}[+] Duel Simulator active and listening on:${NC}"
        echo "    - Game Client TCP: localhost:7911 (or LAN IP for EDOPro / YGOPro)"
        echo "    - Web Room Manager: http://localhost:7922"
        ;;

    stop)
        echo -e "${YELLOW}[*] Stopping Yu-Gi-Oh! Live Duel Simulator...${NC}"
        docker compose down
        echo -e "${GREEN}[+] Simulator stopped.${NC}"
        ;;

    restart)
        echo -e "${BLUE}[*] Restarting Yu-Gi-Oh! Live Duel Simulator...${NC}"
        docker compose restart
        echo -e "${GREEN}[+] Simulator restarted.${NC}"
        ;;

    status)
        echo -e "${BOLD}=== 🌌 Yu-Gi-Oh! Story & Simulator Platform Status ===${NC}"
        echo -e "${BLUE}>> Live Duel Simulator Container:${NC}"
        docker ps --filter "name=ygo-simulator-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
        echo ""
        echo -e "${BLUE}>> Story Database Statistics:${NC}"
        "$VENV_PYTHON" -c "
import sqlite3
c = sqlite3.connect('$BASE_DIR/story_database/ygo_story.db')
print('   • Custom Cards in Pool :', c.execute('SELECT COUNT(*) FROM custom_cards').fetchone()[0])
print('   • Factions / Archetypes:', c.execute('SELECT COUNT(*) FROM factions').fetchone()[0])
print('   • Story Duelists       :', c.execute('SELECT COUNT(*) FROM characters').fetchone()[0])
print('   • Pre-made Story Decks :', c.execute('SELECT COUNT(*) FROM decks').fetchone()[0])
print('   • Active Player Decks  :', c.execute('SELECT COUNT(DISTINCT user_id) FROM player_decks').fetchone()[0])
c.close()
"
        echo ""
        echo -e "${BLUE}>> Expansions & Simulator CDB Status:${NC}"
        if [ -f "$BASE_DIR/server-data/expansions/custom_cards.cdb" ]; then
            ls -lh "$BASE_DIR/server-data/expansions/custom_cards.cdb" | awk '{print "   • Compiled CDB: "$9" ("$5")"}'
        else
            echo "   • CDB not generated yet. Run: ./manage.sh sync"
        fi
        LUA_COUNT=$(ls -1 "$BASE_DIR/server-data/expansions/scripts" 2>/dev/null | wc -l)
        echo "   • Lua Effect Scripts: $LUA_COUNT files in server-data/expansions/scripts/"
        ;;

    bot)
        echo -e "${BLUE}[*] Starting Modular Yu-Gi-Oh! Story & Duel Discord Bot...${NC}"
        exec "$VENV_PYTHON" "$BASE_DIR/discord_bot/bot.py"
        ;;

    web)
        echo -e "${BLUE}[*] Launching Web Catalog & Lore Dashboard on http://localhost:8000...${NC}"
        exec "$VENV_PYTHON" -m uvicorn story_database.api_server:app --app-dir "$BASE_DIR" --host 0.0.0.0 --port 8000 --reload
        ;;

    sync)
        echo -e "${BLUE}[*] Synchronizing Story Database with Simulator CDB and Lua scripts...${NC}"
        "$VENV_PYTHON" "$BASE_DIR/tools/cdb_builder.py"
        "$VENV_PYTHON" "$BASE_DIR/tools/lua_generator.py"
        echo -e "${GREEN}[+] Synchronization completed successfully.${NC}"
        ;;

    import)
        if [ -z "$2" ]; then
            echo -e "${RED}[-] Error: Please provide a Duelingbook JSON export file.${NC}"
            echo "    Usage: ./manage.sh import <path/to/cards.json>"
            exit 1
        fi
        echo -e "${BLUE}[*] Importing Duelingbook cards from $2...${NC}"
        "$VENV_PYTHON" "$BASE_DIR/tools/duelingbook_importer.py" "$2"
        ;;

    export-decks)
        echo -e "${BLUE}[*] Exporting character story decks to .ydk files...${NC}"
        "$VENV_PYTHON" "$BASE_DIR/tools/export_deck.py"
        ;;

    export-player)
        if [ -z "$2" ]; then
            echo -e "${RED}[-] Error: Please provide a Discord User ID.${NC}"
            echo "    Usage: ./manage.sh export-player <discord_user_id>"
            exit 1
        fi
        echo -e "${BLUE}[*] Exporting player deck for user $2 to .ydk file...${NC}"
        "$VENV_PYTHON" -c "import sys; sys.path.insert(0, '$BASE_DIR/tools'); from export_deck import export_player_deck; export_player_deck('$2')"
        ;;

    test)
        echo -e "${BLUE}[*] Running Unit Test Suite with Pytest...${NC}"
        "$VENV_PYTEST" -v "$BASE_DIR/tests"
        ;;

    validate-lua)
        echo -e "${BLUE}[*] Validating all generated Lua effect scripts using luac compiler...${NC}"
        if which luac >/dev/null 2>&1; then
            luac -p "$BASE_DIR/server-data/expansions/scripts"/*.lua
            echo -e "${GREEN}[+] All Lua scripts passed syntax validation without errors!${NC}"
        else
            echo -e "${YELLOW}[!] luac compiler not found on host. Run: sudo apt-get install lua5.3${NC}"
        fi
        ;;

    app|gui)
        echo -e "${BLUE}[*] Launching Yu-Gi-Oh! Platform Manager Desktop Application...${NC}"
        exec "$VENV_PYTHON" "$BASE_DIR/app.py"
        ;;

    *)
        echo -e "${BOLD}🌌 Yu-Gi-Oh! Story & Simulator Platform Manager${NC}"
        echo "Usage: ./manage.sh <command>"
        echo ""
        echo "Simulator Commands:"
        echo "  start                 Start live simulator container (Port 7911 / 7922)"
        echo "  stop                  Stop live simulator container"
        echo "  restart               Restart live simulator container"
        echo "  status                Display container, database, and card expansion status"
        echo ""
        echo "Application Services:"
        echo "  app                   Launch native desktop control panel application"
        echo "  web                   Start local web card catalog & dashboard (Port 8000)"
        echo "  bot                   Launch modular Discord story & duel bot"
        echo ""
        echo "Card Pipeline & Synchronization:"
        echo "  sync                  Rebuild simulator custom_cards.cdb and Lua effect scripts"
        echo "  import <file.json>    Import Duelingbook JSON cards into database and simulator"
        echo "  export-decks          Export character decks to standard .ydk format"
        echo "  export-player <uid>   Export a Discord player's active deck to .ydk format"
        echo ""
        echo "Quality & Testing:"
        echo "  test                  Run the comprehensive Pytest test suite"
        echo "  validate-lua          Verify syntax of all generated Lua scripts with luac"
        ;;
esac
