#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - Cloudflare Zero Trust Tunnel Setup & Manager
# =============================================================================
# Connects the local FastAPI Web Card Catalog & REST API (Port 8000)
# to Cloudflare's global edge network via an encrypted tunnel.
#
# Operational Modes:
# 1. Quick Tunnel (Zero config, free https://*.trycloudflare.com, no account needed):
#    Useful for local staging, development, and immediate testing.
# 2. Named Tunnel (Custom domain via Cloudflare Zero Trust Tunnel Token):
#    Production 24/7 tunnel mapped to https://thelandofkustomazi.com.
#
# Usage:
#   ./setup_cloudflare_tunnel.sh            # Auto-detects token from .env
#   ./setup_cloudflare_tunnel.sh --quick    # Starts instant ephemeral quick tunnel
#   ./setup_cloudflare_tunnel.sh --token <TOKEN> # Starts named tunnel with token
# =============================================================================

set -e

# Visual formatting constants
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

ENV_FILE="$BASE_DIR/.env"
CLIENT_CONFIG="$BASE_DIR/config/client/config.json"
if [ ! -f "$CLIENT_CONFIG" ]; then
    CLIENT_CONFIG="$BASE_DIR/production/shared/config.json"
fi

echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BOLD}${BLUE}  🌐 Yu-Gi-Oh! Cloudflare Tunnel Secure Connector                   ${NC}"
echo -e "${BOLD}${BLUE}=====================================================================${NC}"

# =============================================================================
# Helper: Ensure cloudflared CLI is installed
# =============================================================================
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

# =============================================================================
# Argument Parsing
# =============================================================================
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

# =============================================================================
# Resolve Token from Environment if Mode is Auto
# =============================================================================
ENV_TOKEN=""
if [ -f "$ENV_FILE" ]; then
    ENV_TOKEN=$(grep -E '^CLOUDFLARE_TUNNEL_TOKEN=' "$ENV_FILE" | cut -d '=' -f 2- | tr -d '"' | tr -d "'")
fi

if [ "$MODE" = "token" ] && [ -n "$CLI_TOKEN" ]; then
    ACTIVE_TOKEN="$CLI_TOKEN"
elif [ "$MODE" = "auto" ] && [ -n "$ENV_TOKEN" ] && [ "$ENV_TOKEN" != "your_cloudflare_tunnel_token_here" ]; then
    ACTIVE_TOKEN="$ENV_TOKEN"
    MODE="token"
else
    MODE="quick"
fi

# =============================================================================
# Execution: Named Tunnel vs Quick Tunnel
# =============================================================================
if [ "$MODE" = "token" ]; then
    echo -e "${BLUE}[*] Starting Cloudflare Named Tunnel using configured token...${NC}"
    echo -e "    Public Domain : https://thelandofkustomazi.com"
    echo -e "    Local Target  : http://localhost:8000 (FastAPI Web Catalog)"
    echo ""
    echo -e "${YELLOW}[!] Tunnel running in foreground. Press Ctrl+C to stop.${NC}"
    echo -e "    (For 24/7 background operation, use: sudo systemctl start cloudflared)${NC}"
    echo ""
    exec cloudflared tunnel --no-autoupdate run --token "$ACTIVE_TOKEN"
else
    echo -e "${BLUE}[*] Starting Cloudflare Quick Tunnel (Free, zero-config)...${NC}"
    echo -e "    Target : http://localhost:8000"
    echo ""

    LOG_FILE="/tmp/cloudflared_quick.log"
    rm -f "$LOG_FILE"

    cloudflared tunnel --url http://localhost:8000 > "$LOG_FILE" 2>&1 &
    CF_PID=$!

    cleanup() {
        echo ""
        echo -e "${YELLOW}[*] Shutting down Cloudflare tunnel (PID: $CF_PID)...${NC}"
        kill "$CF_PID" 2>/dev/null || true
        exit 0
    }
    trap cleanup SIGINT SIGTERM EXIT

    echo -e "${BLUE}[*] Waiting for tunnel connection and public HTTPS URL...${NC}"
    URL=""
    for i in {1..30}; do
        if [ -f "$LOG_FILE" ]; then
            URL=$(grep -o 'https://[-a-zA-Z0-9\.]*\.trycloudflare\.com' "$LOG_FILE" | head -n 1 || true)
            if [ -n "$URL" ]; then
                break
            fi
        fi
        sleep 1
    done

    if [ -z "$URL" ]; then
        echo -e "${RED}[-] Timeout: Failed to obtain tunnel URL within 30 seconds.${NC}"
        echo -e "    Inspect log output:"
        cat "$LOG_FILE"
        exit 1
    fi

    echo ""
    echo -e "${BOLD}${GREEN}=====================================================================${NC}"
    echo -e "${BOLD}${GREEN}  🎉 CLOUDFLARE HTTPS TUNNEL IS LIVE!                                ${NC}"
    echo -e "${BOLD}${GREEN}=====================================================================${NC}"
    echo -e "  Public HTTPS URL: ${BOLD}${GREEN}${URL}${NC}"
    echo -e "  Local Service   : http://localhost:8000"
    echo ""

    if [ -f "$CLIENT_CONFIG" ]; then
        echo -e "${BLUE}[*] Updating $CLIENT_CONFIG with public HTTPS URL...${NC}"
        python3 - <<EOF
import json, os

config_path = "$CLIENT_CONFIG"
if os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["web_catalog_url"] = "$URL"
        data["expansions_update_url"] = "$URL/api/expansions/download"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("  [+] Updated client connection manifest with tunnel URL.")
    except Exception as e:
        print(f"  [-] Failed to update manifest: {e}")
EOF
    fi

    echo ""
    echo -e "${YELLOW}[!] Keep this terminal open. Tunnel will close when stopped.${NC}"
    echo -e "    Press Ctrl+C to terminate."
    wait "$CF_PID"
fi
