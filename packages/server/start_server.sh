#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - Linux / macOS Server Host Launcher & Controller
# =============================================================================
# Provides local orchestration for Unix host environments to start, manage,
# and monitor the Yu-Gi-Oh! server stack (Simulator, Web Catalog API, Discord Bot)
# without requiring systemd.
#
# Usage:
#   ./start_server.sh             (Displays interactive management menu)
#   ./start_server.sh all         (Starts Simulator, Web Server, and Discord Bot)
#   ./start_server.sh simulator   (Starts ocgcore Docker Compose container)
#   ./start_server.sh web         (Starts FastAPI Web Catalog on localhost:8000)
#   ./start_server.sh bot         (Starts The Great Kasutamaiza Discord Bot)
#   ./start_server.sh sync        (Synchronizes custom card database and Lua scripts)
#   ./start_server.sh tunnel      (Starts Cloudflare HTTPS tunnel)
#   ./start_server.sh duckdns     (Updates DuckDNS dynamic DNS record)
#   ./start_server.sh stop        (Stops Docker containers and running services)
# =============================================================================

set -e

# Visual styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

# Canonical directory resolution supporting execution through symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SERVER_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"

# Resolve repository root
SEARCH_DIR="$SERVER_DIR"
BASE_DIR=""
for i in 1 2 3 4; do
    if [ -f "$SEARCH_DIR/manage.py" ] || [ -f "$SEARCH_DIR/.env" ]; then
        BASE_DIR="$SEARCH_DIR"
        break
    fi
    SEARCH_DIR="$(dirname "$SEARCH_DIR")"
done

if [ -z "$BASE_DIR" ]; then
    BASE_DIR="$(dirname "$(dirname "$SERVER_DIR")")"
fi

# Locate Python
PYTHON_BIN="$BASE_DIR/venv/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python3 || command -v python || true)"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}[-] Error: Python 3 not found in venv or system PATH.${NC}"
    exit 1
fi

do_simulator() {
    echo -e "${BLUE}[*] Starting ocgcore Live Duel Simulator Container...${NC}"
    cd "$BASE_DIR"
    docker compose up -d
    echo -e "${GREEN}[+] Simulator container is active.${NC}"
}

do_web() {
    echo -e "${BLUE}[*] Launching FastAPI Web Catalog on http://localhost:8000...${NC}"
    cd "$BASE_DIR"
    exec "$PYTHON_BIN" -m uvicorn production.main.web.api_server:app --host 0.0.0.0 --port 8000 --reload
}

do_bot() {
    echo -e "${BLUE}[*] Launching Discord Story & Duel Bot...${NC}"
    cd "$BASE_DIR"
    exec "$PYTHON_BIN" "$BASE_DIR/production/main/discord_bot/bot.py"
}

do_sync() {
    echo -e "${BLUE}[*] Synchronizing custom card database and Lua scripts...${NC}"
    cd "$BASE_DIR"
    "$PYTHON_BIN" "$BASE_DIR/manage.py" sync
}

do_tunnel() {
    "$SERVER_DIR/scripts/setup_cloudflare_tunnel.sh" "$@"
}

do_duckdns() {
    "$SERVER_DIR/scripts/update_duckdns.sh" "$@"
}

do_stop() {
    echo -e "${YELLOW}[*] Stopping Docker containers...${NC}"
    cd "$BASE_DIR"
    docker compose down
    echo -e "${GREEN}[+] Containers stopped.${NC}"
}

do_all() {
    do_simulator
    echo -e "${BLUE}[*] Launching Web Catalog and Discord Bot as background processes...${NC}"
    cd "$BASE_DIR"
    "$PYTHON_BIN" -m uvicorn production.main.web.api_server:app --host 0.0.0.0 --port 8000 > /tmp/ygo_web.log 2>&1 &
    WEB_PID=$!
    "$PYTHON_BIN" "$BASE_DIR/production/main/discord_bot/bot.py" > /tmp/ygo_bot.log 2>&1 &
    BOT_PID=$!

    echo -e "${GREEN}[+] Services launched in background:${NC}"
    echo -e "    - Simulator : localhost:7911 (Docker)"
    echo -e "    - Web API   : http://localhost:8000 (PID $WEB_PID, log: /tmp/ygo_web.log)"
    echo -e "    - Bot       : Discord Gateway (PID $BOT_PID, log: /tmp/ygo_bot.log)"
}

# CLI Argument Routing
case "$1" in
    all)
        do_all
        exit 0
        ;;
    simulator)
        do_simulator
        exit 0
        ;;
    web)
        do_web
        exit 0
        ;;
    bot)
        do_bot
        exit 0
        ;;
    sync)
        do_sync
        exit 0
        ;;
    tunnel)
        shift
        do_tunnel "$@"
        exit 0
        ;;
    duckdns)
        shift
        do_duckdns "$@"
        exit 0
        ;;
    stop)
        do_stop
        exit 0
        ;;
    "")
        # Interactive Menu
        ;;
    *)
        echo -e "${RED}[-] Unknown argument: $1${NC}"
        echo "    Available: all, simulator, web, bot, sync, tunnel, duckdns, stop"
        exit 1
        ;;
esac

echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BOLD}${BLUE}  🖥️  Yu-Gi-Oh! Server Host Management Console (Unix)                ${NC}"
echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo ""
echo "  1. Start Full Server Stack (Simulator + Web API + Discord Bot)"
echo "  2. Start Live Duel Simulator Container (ocgcore on TCP 7911/7922)"
echo "  3. Start Web Catalog & REST API Server (FastAPI on Port 8000)"
echo "  4. Start Discord Story & Duel Bot (The Great Kasutamaiza)"
echo "  5. Synchronize Custom Cards (Compile CDB & Lua effect scripts)"
echo "  6. Start Cloudflare HTTPS Tunnel (Remote Card Sync & Web Access)"
echo "  7. Update DuckDNS Dynamic DNS Record"
echo "  8. Stop Simulator Containers"
echo "  0. Exit"
echo ""
read -rp "Select an option [0-8]: " CHOICE

case "$CHOICE" in
    1) do_all ;;
    2) do_simulator ;;
    3) do_web ;;
    4) do_bot ;;
    5) do_sync ;;
    6) do_tunnel ;;
    7) do_duckdns ;;
    8) do_stop ;;
    0) exit 0 ;;
    *) echo -e "${RED}[-] Invalid selection.${NC}"; exit 1 ;;
esac
