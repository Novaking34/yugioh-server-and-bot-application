#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - Oracle Cloud 24/7 Server Automated Deployment Script
# =============================================================================
# Turn-key deployment script for Oracle Cloud Infrastructure (OCI) Free Tier
# (Ubuntu 22.04 / 24.04 LTS on Ampere A1 ARM64 or AMD x86_64).
#
# Automates:
# 1. System packages & build prerequisites (Python 3, Docker, Git, Firewall)
# 2. Oracle VM internal firewall & iptables opening for:
#    - TCP 7911 (Duel Simulator Engine / EDOPro protocol)
#    - TCP 7922 (Room Manager / WebSocket)
#    - TCP 8000 (Web Card Catalog & Expansion Sync API)
# 3. Python virtual environment & dependencies installation
# 4. Custom card database initialization & card compilation
# 5. Live simulator container configuration & startup
# 6. 24/7 Systemd background service daemon setup & auto-start on boot
#
# Usage:
#   chmod +x deploy_oracle_cloud.sh
#   sudo ./deploy_oracle_cloud.sh
# =============================================================================

set -e

# Visual styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BOLD}${BLUE}  🌌 Yu-Gi-Oh! Platform - Oracle Cloud 24/7 Deployment Wizard        ${NC}"
echo -e "${BOLD}${BLUE}=====================================================================${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[-] Error: This script must be run as root (use: sudo ./deploy_oracle_cloud.sh)${NC}"
    exit 1
fi

REAL_USER="${SUDO_USER:-$USER}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo -e "${BLUE}[*] Deploying for host user: ${GREEN}$REAL_USER${NC}"
echo -e "${BLUE}[*] Repository base path:    ${GREEN}$BASE_DIR${NC}"

# Detect Architecture (x86_64 vs aarch64/arm64)
ARCH="$(uname -m)"
echo -e "${BLUE}[*] Detected architecture:   ${GREEN}$ARCH${NC}"

# -----------------------------------------------------------------------------
# STEP 1: Package Updates & Dependencies
# -----------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${BLUE}[1/6] Installing system packages and runtime dependencies...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    jq \
    sqlite3 \
    iptables \
    iptables-persistent \
    netfilter-persistent \
    ca-certificates

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${BLUE}[*] Docker not found. Installing Docker engine...${NC}"
    apt-get install -y docker.io docker-compose-v2
    systemctl enable docker
    systemctl start docker
    usermod -aG docker "$REAL_USER" || true
    echo -e "${GREEN}[+] Docker installed and started.${NC}"
else
    echo -e "${GREEN}[+] Docker already installed: $(docker --version)${NC}"
fi

# -----------------------------------------------------------------------------
# STEP 2: Configure Oracle Cloud Firewall & iptables
# -----------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${BLUE}[2/6] Configuring Oracle Cloud OS Firewall rules...${NC}"
# Oracle Cloud Ubuntu images drop non-port-22 incoming traffic by default in iptables INPUT chain.
# We explicitly allow ports 7911, 7922, and 8000.
PORTS=(22 7911 7922 8000)

for PORT in "${PORTS[@]}"; do
    if ! iptables -C INPUT -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null; then
        echo -e "${BLUE}[*] Opening TCP Port $PORT in iptables...${NC}"
        iptables -I INPUT 1 -p tcp --dport "$PORT" -j ACCEPT
    else
        echo -e "${GREEN}[+] TCP Port $PORT already permitted in iptables.${NC}"
    fi
done

# Persist iptables rules across reboots
netfilter-persistent save || true

# Also configure UFW if enabled
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
    echo -e "${BLUE}[*] UFW firewall active. Adding firewall rules...${NC}"
    ufw allow 22/tcp
    ufw allow 7911/tcp
    ufw allow 7922/tcp
    ufw allow 8000/tcp
    ufw reload
fi
echo -e "${GREEN}[+] OS firewall configured for Duel Port 7911, Room Port 7922, and Web Port 8000.${NC}"

# -----------------------------------------------------------------------------
# STEP 3: Setup Python Virtual Environment & Project Dependencies
# -----------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${BLUE}[3/6] Setting up Python virtual environment...${NC}"
VENV_DIR="$BASE_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}[*] Creating venv at $VENV_DIR...${NC}"
    sudo -u "$REAL_USER" python3 -m venv "$VENV_DIR"
fi

echo -e "${BLUE}[*] Installing/updating requirements...${NC}"
sudo -u "$REAL_USER" "$VENV_DIR/bin/pip" install --upgrade pip
if [ -f "$BASE_DIR/requirements.txt" ]; then
    sudo -u "$REAL_USER" "$VENV_DIR/bin/pip" install -r "$BASE_DIR/requirements.txt"
fi
echo -e "${GREEN}[+] Python virtual environment ready.${NC}"

# -----------------------------------------------------------------------------
# STEP 4: Database & Card Expansion Initialization
# -----------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${BLUE}[4/6] Initializing Database & Card Expansion CDB...${NC}"
sudo -u "$REAL_USER" "$VENV_DIR/bin/python3" "$BASE_DIR/manage.py" install
echo -e "${GREEN}[+] Custom card catalog and expansions compiled.${NC}"

# -----------------------------------------------------------------------------
# STEP 5: Install and Enable Systemd 24/7 Services
# -----------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${BLUE}[5/6] Registering 24/7 Systemd Services...${NC}"
SYSTEMD_DIR="$BASE_DIR/production/main/systemd"

for SERVICE in ygo-simulator.service ygo-web.service ygo-bot.service; do
    if [ -f "$SYSTEMD_DIR/$SERVICE" ]; then
        sed -e "s|/home/professorseanex/yugioh-server|$BASE_DIR|g" \
            -e "s|User=professorseanex|User=$REAL_USER|g" \
            "$SYSTEMD_DIR/$SERVICE" > "/etc/systemd/system/$SERVICE"
        echo -e "${GREEN}[+] Installed /etc/systemd/system/$SERVICE${NC}"
    fi
done

systemctl daemon-reload
systemctl enable ygo-simulator.service
systemctl enable ygo-web.service
systemctl enable ygo-bot.service

# Start the Web and Simulator services
systemctl restart ygo-web.service
systemctl restart ygo-simulator.service

# Check if bot token is configured before starting bot service
if grep -q 'DISCORD_BOT_TOKEN="MTU' "$BASE_DIR/.env" 2>/dev/null || grep -q 'DISCORD_BOT_TOKEN="[a-zA-Z0-9]' "$BASE_DIR/.env" 2>/dev/null; then
    echo -e "${BLUE}[*] Valid Discord Bot token detected. Starting ygo-bot.service...${NC}"
    systemctl restart ygo-bot.service
    echo -e "${GREEN}[+] Discord Bot service started.${NC}"
else
    echo -e "${YELLOW}[!] Note: Discord Bot token not yet configured in $BASE_DIR/.env.${NC}"
    echo -e "    Edit $BASE_DIR/.env, add your token, then run: sudo systemctl start ygo-bot"
fi

# -----------------------------------------------------------------------------
# STEP 6: Public IP Detection & Verification Summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${BLUE}[6/6] Verifying server status & endpoints...${NC}"
PUBLIC_IP="$(curl -s -4 https://ifconfig.me || curl -s -4 https://api.ipify.org || echo "YOUR_SERVER_PUBLIC_IP")"

echo ""
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
echo -e "${BOLD}${GREEN}  🎉 ORACLE CLOUD 24/7 DEPLOYMENT COMPLETE!                          ${NC}"
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
echo -e "Public Server IP:       ${BOLD}${YELLOW}$PUBLIC_IP${NC}"
echo -e "Live Duel Simulator:    ${BOLD}${YELLOW}$PUBLIC_IP:7911${NC} (Raw TCP - EDOPro Client)"
echo -e "Room Manager API:       ${BOLD}${YELLOW}$PUBLIC_IP:7922${NC}"
echo -e "Web Card Catalog & API: ${BOLD}${YELLOW}http://$PUBLIC_IP:8000${NC}"
echo ""
echo -e "${BOLD}OCI Cloud Security List Reminder:${NC}"
echo -e "In your Oracle Cloud Console -> Virtual Cloud Networks -> Security Lists:"
echo -e "Make sure you added Ingress Rules for:"
echo -e "  - ${YELLOW}TCP Port 7911${NC} (Source: 0.0.0.0/0) -> Live Duels"
echo -e "  - ${YELLOW}TCP Port 7922${NC} (Source: 0.0.0.0/0) -> Room Manager"
echo -e "  - ${YELLOW}TCP Port 8000${NC} (Source: 0.0.0.0/0) -> Web Catalog / Sync"
echo ""
echo -e "${BOLD}Service Management Commands:${NC}"
echo -e "  Check status:   ${BLUE}sudo systemctl status ygo-simulator ygo-web ygo-bot${NC}"
echo -e "  Restart all:    ${BLUE}sudo systemctl restart ygo-simulator ygo-web ygo-bot${NC}"
echo -e "  View bot logs:  ${BLUE}sudo journalctl -u ygo-bot -f${NC}"
echo -e "  View web logs:  ${BLUE}sudo journalctl -u ygo-web -f${NC}"
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
