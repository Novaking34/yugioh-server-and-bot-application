#!/usr/bin/env bash
# =============================================================================
# DuckDNS Dynamic DNS Auto-Updater
# =============================================================================
# Keeps thelandofkustomazi.duckdns.org updated with current public IP
# =============================================================================

BASE_DIR="$(dirname "$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")")"
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

if [ -z "$TOKEN" ]; then
    echo "[*] Notice: DUCKDNS_TOKEN not yet specified in .env. To enable automatic IP syncing, add DUCKDNS_TOKEN=\"your-token\" to .env."
    exit 0
fi

CURRENT_IP="$(curl -s -4 https://ifconfig.me || curl -s -4 https://api.ipify.org)"
RESPONSE="$(curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=${CURRENT_IP}")"

if [ "$RESPONSE" = "OK" ]; then
    echo "[+] DuckDNS successfully updated: ${DOMAIN}.duckdns.org -> ${CURRENT_IP}"
else
    echo "[-] DuckDNS update failed. Response: ${RESPONSE}"
fi
