#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - DuckDNS Dynamic DNS Auto-Updater
# =============================================================================
# Synchronizes the current public WAN IP of the host machine with DuckDNS
# (e.g. thelandofkustomazi.duckdns.org).
#
# Primary Purpose:
# Provides a reliable dynamic fallback hostname for live game client direct
# connections (Port 7911) in case the host VPS IP ever changes.
#
# Setup as Recurring Cron Job (Runs every 5 minutes):
#   crontab -e
#   */5 * * * * /home/ubuntu/yugioh-server/packages/server/scripts/update_duckdns.sh >/dev/null 2>&1
# =============================================================================

set -e

# Canonical directory resolution supporting execution through symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"

# Walk up to find project root (where .env resides)
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

ENV_FILE="$BASE_DIR/.env"

DOMAIN="thelandofkustomazi"
TOKEN=""

if [ -f "$ENV_FILE" ]; then
    ENV_DOMAIN=$(grep -E '^DUCKDNS_DOMAIN=' "$ENV_FILE" | cut -d '=' -f 2- | tr -d '"' | tr -d "'")
    if [ -n "$ENV_DOMAIN" ]; then
        DOMAIN="$ENV_DOMAIN"
    fi
    TOKEN=$(grep -E '^DUCKDNS_TOKEN=' "$ENV_FILE" | cut -d '=' -f 2- | tr -d '"' | tr -d "'")
fi

if [ -z "$TOKEN" ] || [ "$TOKEN" = "your_duckdns_token_here" ]; then
    echo "[*] Notice: DUCKDNS_TOKEN not yet specified in .env. To enable automatic IP syncing, set DUCKDNS_TOKEN in .env."
    exit 0
fi

# Detect public WAN IP with fallback provider
CURRENT_IP="$(curl -s -4 --max-time 5 https://ifconfig.me || curl -s -4 --max-time 5 https://api.ipify.org || true)"

if [ -z "$CURRENT_IP" ]; then
    echo "[-] Error: Failed to determine public IPv4 address from discovery endpoints."
    exit 1
fi

RESPONSE="$(curl -s --max-time 10 "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${CURRENT_IP}")"

if [ "$RESPONSE" = "OK" ]; then
    echo "[+] DuckDNS successfully updated: ${DOMAIN}.duckdns.org -> ${CURRENT_IP}"
else
    echo "[-] DuckDNS update failed. Response: ${RESPONSE}"
    exit 1
fi
