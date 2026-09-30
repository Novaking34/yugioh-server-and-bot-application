#!/usr/bin/env bash
# Yu-Gi-Oh Custom Server & Story Platform CLI Manager

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

VENV_PYTHON="$BASE_DIR/venv/bin/python"

case "$1" in
    start)
        echo "[*] Starting Yu-Gi-Oh Live Duel Simulator (ygoserver)..."
        docker compose up -d
        echo "[+] Duel Simulator running on:"
        echo "    - Game Client TCP: localhost:7911"
        echo "    - Web Room Manager: http://localhost:7922"
        ;;
    stop)
        echo "[*] Stopping Yu-Gi-Oh Live Duel Simulator..."
        docker compose down
        echo "[+] Simulator stopped."
        ;;
    restart)
        echo "[*] Restarting Yu-Gi-Oh Live Duel Simulator..."
        docker compose restart
        ;;
    status)
        echo "=== Yu-Gi-Oh Story & Simulator Platform Status ==="
        echo ">> Simulator Container:"
        docker ps --filter "name=ygo-simulator-server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo ">> Database Card Count:"
        "$VENV_PYTHON" -c "import sqlite3; c=sqlite3.connect('$BASE_DIR/story_database/ygo_story.db'); print('   Registered Cards:', c.execute('SELECT COUNT(*) FROM custom_cards').fetchone()[0]); print('   Factions:', c.execute('SELECT COUNT(*) FROM factions').fetchone()[0]); print('   Decks:', c.execute('SELECT COUNT(*) FROM decks').fetchone()[0]); c.close()"
        echo ""
        echo ">> Expansions / CDB Status:"
        ls -lh "$BASE_DIR/server-data/expansions/custom_cards.cdb" 2>/dev/null || echo "   CDB not generated yet."
        echo "   Lua Effect Scripts: $(ls -1 "$BASE_DIR/server-data/expansions/scripts" 2>/dev/null | wc -l) files"
        ;;
    bot)
        echo "[*] Starting Yu-Gi-Oh Story & Duelingbook Discord Bot..."
        exec "$VENV_PYTHON" "$BASE_DIR/discord_bot/bot.py"
        ;;
    web)
        echo "[*] Launching Web Catalog & Lore Dashboard on http://localhost:8000..."
        exec "$VENV_PYTHON" -m uvicorn story_database.api_server:app --app-dir "$BASE_DIR" --host 0.0.0.0 --port 8000 --reload
        ;;
    sync)
        echo "[*] Synchronizing Story Database with Simulator CDB and Lua scripts..."
        "$VENV_PYTHON" "$BASE_DIR/tools/cdb_builder.py"
        "$VENV_PYTHON" "$BASE_DIR/tools/lua_generator.py"
        echo "[+] Sync completed."
        ;;
    import)
        if [ -z "$2" ]; then
            echo "[-] Error: Please provide a Duelingbook JSON export file."
            echo "    Usage: ./manage.sh import <path/to/cards.json>"
            exit 1
        fi
        echo "[*] Importing Duelingbook cards from $2..."
        "$VENV_PYTHON" "$BASE_DIR/tools/duelingbook_importer.py" "$2"
        ;;
    export-decks)
        echo "[*] Exporting character decks to .ydk files..."
        "$VENV_PYTHON" "$BASE_DIR/tools/export_deck.py"
        ;;
    *)
        echo "Yu-Gi-Oh Custom Server & Story Platform Manager"
        echo "Usage: ./manage.sh <command>"
        echo ""
        echo "Commands:"
        echo "  start         Start the live simulator server container (Port 7911 / 7922)"
        echo "  stop          Stop the live simulator server container"
        echo "  restart       Restart the simulator server"
        echo "  status        Display container, database, and card expansion status"
        echo "  bot           Launch the Discord story bot"
        echo "  web           Start the local web card catalog & dashboard (Port 8000)"
        echo "  sync          Rebuild the simulator custom_cards.cdb and Lua effect scripts"
        echo "  import <file> Import Duelingbook JSON card export into database and simulator"
        echo "  export-decks  Export character decks to .ydk format"
        ;;
esac
