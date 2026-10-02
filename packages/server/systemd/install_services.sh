#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - 24/7 Systemd Background Service Installer
# =============================================================================
# Configures and enables Linux systemd service daemons to ensure all platform
# components start automatically on machine boot and restart after crashes:
#
# Services Managed:
# 1. ygo-simulator.service : Live Duel Simulator Container (ocgcore, TCP 7911/7922)
# 2. ygo-web.service       : FastAPI Web Catalog Dashboard & REST API (Port 8000)
# 3. ygo-bot.service       : The Great Kasutamaiza Discord Bot (21+ slash commands)
# 4. ygo-tunnel.service    : Optional Cloudflare HTTPS Quick Tunnel daemon
#
# Usage:
#   sudo ./install_services.sh
#   sudo ./install_services.sh --with-tunnel
# =============================================================================

set -e

# Visual formatting constants
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[-] Error: Root privileges required. Please run: sudo ./install_services.sh${NC}"
    exit 1
fi

# Canonical directory resolution supporting execution through symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"

# Walk up to find project root (where .env or manage.sh resides)
SEARCH_DIR="$SCRIPT_DIR"
BASE_DIR=""
for i in 1 2 3 4; do
    if [ -f "$SEARCH_DIR/.env" ] || [ -f "$SEARCH_DIR/manage.sh" ]; then
        BASE_DIR="$SEARCH_DIR"
        break
    fi
    SEARCH_DIR="$(dirname "$SEARCH_DIR")"
done

if [ -z "$BASE_DIR" ]; then
    BASE_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
fi

CURRENT_USER="${SUDO_USER:-$USER}"

echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BOLD}${BLUE}  ⚙️ Yu-Gi-Oh! 24/7 Systemd Service Daemon Installer                 ${NC}"
echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BLUE}[*] Target execution user : ${GREEN}$CURRENT_USER${NC}"
echo -e "${BLUE}[*] Target base directory: ${GREEN}$BASE_DIR${NC}"
echo ""

# Base services installed by default
SERVICES=("ygo-simulator.service" "ygo-web.service" "ygo-bot.service")

# Include tunnel service if explicitly requested
if [ "$1" = "--with-tunnel" ]; then
    SERVICES+=("ygo-tunnel.service")
fi

# Install and customize each service unit file
for sfile in "${SERVICES[@]}"; do
    SRC_UNIT="$SCRIPT_DIR/$sfile"
    DEST_UNIT="/etc/systemd/system/$sfile"

    if [ -f "$SRC_UNIT" ]; then
        sed -e "s|/home/professorseanex/yugioh-server|$BASE_DIR|g" \
            -e "s|User=professorseanex|User=$CURRENT_USER|g" \
            "$SRC_UNIT" > "$DEST_UNIT"
        echo -e "  ${GREEN}[+] Installed ${DEST_UNIT}${NC}"
    else
        echo -e "  ${YELLOW}[!] Warning: Unit template not found: ${SRC_UNIT}${NC}"
    fi
done

# Reload systemd manager configuration
echo ""
echo -e "${BLUE}[*] Reloading systemd daemon...${NC}"
systemctl daemon-reload

# Enable installed services for automatic boot startup
for sfile in "${SERVICES[@]}"; do
    systemctl enable "$sfile"
    echo -e "  ${GREEN}[+] Enabled ${sfile} to auto-start on system boot.${NC}"
done

echo ""
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
echo -e "${BOLD}${GREEN}  🎉 SUCCESS: All platform services are registered and enabled!      ${NC}"
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
echo -e "Start services now:"
echo -e "  ${BLUE}sudo systemctl start ygo-simulator${NC}"
echo -e "  ${BLUE}sudo systemctl start ygo-web${NC}"
echo -e "  ${BLUE}sudo systemctl start ygo-bot${NC}"
echo ""
echo -e "Inspect live status & logs:"
echo -e "  ${BLUE}sudo systemctl status ygo-simulator ygo-web ygo-bot${NC}"
echo -e "  ${BLUE}journalctl -u ygo-bot -f${NC}"
echo -e "  ${BLUE}journalctl -u ygo-web -f${NC}"
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
