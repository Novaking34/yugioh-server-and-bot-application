#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - Cloudflare Tunnel Setup & Manager
# =============================================================================
# Connects the local Web Card Catalog & Card Sync Manifest (Port 8000)
# to Cloudflare's global edge network via encrypted HTTPS tunnel.
#
# Supports:
# 1. Quick Tunnel (Zero config, free https://*.trycloudflare.com, no account needed)
# 2. Named Tunnel (Custom domain via Cloudflare Zero Trust Tunnel Token)
#
# Usage:
#   ./setup_cloudflare_tunnel.sh
#   ./setup_cloudflare_tunnel.sh --quick
#   ./setup_cloudflare_tunnel.sh --token <YOUR_CLOUDFLARE_TOKEN>
# =============================================================================

set -e

# Visual formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_FILE="$BASE_DIR/.env"
SHARED_CONFIG="$BASE_DIR/production/shared/config.json"

echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BOLD}${BLUE}  🌐 Yu-Gi-Oh! Cloudflare Tunnel Secure Connector                   ${NC}"
echo -e "${BOLD}${BLUE}=====================================================================${NC}"

# 1. Ensure cloudflared is installed
ensure_cloudflared() {
    if command -v cloudflared >/dev/null 2>&1; then
        echo -e "${GREEN}[+] cloudflared is installed: $(cloudflared --version | head -n 1)${NC}"
        return 0
    fi

    echo -e "${BLUE}[*] cloudflared not found in PATH. Checking architecture...${NC}"
    ARCH="$(uname -m)"
    case "$ARCH" in
        x86_64)
            CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            ;;
        aarch64|arm64)
            CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            ;;
        armv7l)
            CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
            ;;
        *)
            echo -e "${RED}[-] Unsupported architecture: $ARCH. Please install cloudflared manually.${NC}"
            exit 1
            ;;
    esac

    echo -e "${BLUE}[*] Downloading cloudflared binary for $ARCH...${NC}"
    TMP_BIN="/tmp/cloudflared"
    curl -fsSL "$CLOUDFLARED_URL" -o "$TMP_BIN"
    chmod +x "$TMP_BIN"

    if [ "$EUID" -eq 0 ]; then
        mv "$TMP_BIN" /usr/local/bin/cloudflared
    elif sudo -n true 2>/dev/null; then
        sudo mv "$TMP_BIN" /usr/local/bin/cloudflared
    else
        mkdir -p "$BASE_DIR/venv/bin"
        mv "$TMP_BIN" "$BASE_DIR/venv/bin/cloudflared"
        export PATH="$BASE_DIR/venv/bin:$PATH"
    fi

    echo -e "${GREEN}[+] cloudflared successfully installed.${NC}"
}

# 2. Parse command arguments and .env
MODE="auto"
CLI_TOKEN=""

while [ $# -gt 0 ]; do
    case "$1" in
        --quick)
            MODE="quick"
            shift
            ;;
        --token)
            MODE="token"
            CLI_TOKEN="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

ensure_cloudflared

# Load variables from .env
TUNNEL_TOKEN=""
WEB_PORT="8000"

if [ -f "$ENV_FILE" ]; then
    TUNNEL_TOKEN="$(grep -E '^CLOUDFLARE_TUNNEL_TOKEN=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"' | tr -d "'")"
    ENV_PORT="$(grep -E '^WEB_PORT=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"' | tr -d "'")"
    if [ -n "$ENV_PORT" ]; then
        WEB_PORT="$ENV_PORT"
    fi
fi

if [ -n "$CLI_TOKEN" ]; then
    TUNNEL_TOKEN="$CLI_TOKEN"
    MODE="token"
fi

# Determine tunnel mode
if [ "$MODE" = "auto" ]; then
    if [ -n "$TUNNEL_TOKEN" ]; then
        MODE="token"
    else
        MODE="quick"
    fi
fi

TARGET_URL="http://localhost:$WEB_PORT"

# 3. Execution based on mode
if [ "$MODE" = "token" ]; then
    echo -e "${BLUE}[*] Starting Named Cloudflare Tunnel using configured Token...${NC}"
    echo -e "${BLUE}[*] Routing traffic to local service: ${GREEN}$TARGET_URL${NC}"
    exec cloudflared tunnel run --token "$TUNNEL_TOKEN"

elif [ "$MODE" = "quick" ]; then
    echo -e "${BLUE}[*] Launching Free Cloudflare Quick Tunnel (zero account required)...${NC}"
    echo -e "${BLUE}[*] Target local endpoint: ${GREEN}$TARGET_URL${NC}"
    echo -e "${YELLOW}[*] Creating instant public HTTPS proxy via trycloudflare.com...${NC}"
    echo ""

    LOGFILE="/tmp/cloudflared_quick.log"
    rm -f "$LOGFILE"

    # Start cloudflared in background and tail logs to capture trycloudflare URL
    cloudflared tunnel --url "$TARGET_URL" > "$LOGFILE" 2>&1 &
    CF_PID=$!

    trap "kill $CF_PID 2>/dev/null || true" EXIT INT TERM

    # Poll log for the generated URL (wait up to 20 seconds)
    TUNNEL_URL=""
    for i in {1..20}; do
        if [ -f "$LOGFILE" ]; then
            TUNNEL_URL="$(grep -o -E 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$LOGFILE" | head -n 1 || true)"
            if [ -n "$TUNNEL_URL" ]; then
                break
            fi
        fi
        sleep 1
    done

    if [ -n "$TUNNEL_URL" ]; then
        echo -e "${BOLD}${GREEN}=====================================================================${NC}"
        echo -e "${BOLD}${GREEN}  🎉 CLOUDFLARE QUICK TUNNEL IS ACTIVE!                             ${NC}"
        echo -e "${BOLD}${GREEN}=====================================================================${NC}"
        echo -e "Public HTTPS URL:        ${BOLD}${YELLOW}$TUNNEL_URL${NC}"
        echo -e "Web Card Catalog:        ${BOLD}${YELLOW}$TUNNEL_URL/${NC}"
        echo -e "Card Manifest Sync API:  ${BOLD}${YELLOW}$TUNNEL_URL/api/manifest${NC}"
        echo ""
        echo -e "${BLUE}[*] Updating production/shared/config.json with public HTTPS URL...${NC}"

        # Update player sync config if config.json exists
        if [ -f "$SHARED_CONFIG" ]; then
            python3 -c "
import json
try:
    with open('$SHARED_CONFIG', 'r') as f:
        data = json.load(f)
    data['server_url'] = '$TUNNEL_URL'
    with open('$SHARED_CONFIG', 'w') as f:
        json.dump(data, f, indent=4)
    print('  [+] Updated production/shared/config.json with tunnel URL.')
except Exception as e:
    print('  [-] Could not update shared config:', e)
" || true
        fi

        echo -e "${BOLD}${GREEN}=====================================================================${NC}"
        echo -e "${YELLOW}Remote players can now download custom cards and sync over HTTPS!${NC}"
        echo -e "Press [Ctrl+C] to stop the Cloudflare tunnel when finished."
        echo ""

        # Wait for the tunnel process
        wait $CF_PID
    else
        echo -e "${RED}[-] Failed to obtain trycloudflare.com URL within 20 seconds.${NC}"
        echo -e "Log output:"
        cat "$LOGFILE"
        exit 1
    fi
fi
