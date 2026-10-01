#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Custom Server, Story Platform & Simulator Master CLI & Installer
# =============================================================================
# Master shell controller and automated installer for the platform.
# - Sets up Python 3 virtual environment and dependencies
# - Verifies Docker & container runtime
# - Hands off command execution to Python Master Controller (manage.py)
# =============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

VENV_DIR="$BASE_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip"

# Color constants
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
NC="\033[0m" # No Color

ensure_environment() {
    # 1. Verify Python 3
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}[-] Error: python3 is not installed or not in PATH.${NC}"
        echo "    Install with: sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip"
        exit 1
    fi

    # 2. Check / Create Virtual Environment
    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "${BLUE}[*] Creating Python virtual environment in $VENV_DIR...${NC}"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}[+] Virtual environment created successfully.${NC}"
        
        if [ -f "$BASE_DIR/requirements.txt" ]; then
            echo -e "${BLUE}[*] Installing dependencies from requirements.txt...${NC}"
            "$VENV_PIP" install --upgrade pip
            "$VENV_PIP" install -r "$BASE_DIR/requirements.txt"
            echo -e "${GREEN}[+] Dependencies installed successfully.${NC}"
        fi
    fi
}

# If no arguments provided or explicitly called with install/setup
if [ $# -eq 0 ]; then
    ensure_environment
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" status
elif [ "$1" = "install" ] || [ "$1" = "setup" ]; then
    echo -e "${BOLD}${BLUE}=== 🌌 Yu-Gi-Oh! Platform Automated Installer ===${NC}"
    ensure_environment
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}[+] Docker is installed: $(docker --version)${NC}"
    else
        echo -e "${YELLOW}[!] Docker not found. Live Duel Simulator container will require Docker.${NC}"
    fi

    # Check luac
    if command -v luac >/dev/null 2>&1; then
        echo -e "${GREEN}[+] luac compiler is available for Lua syntax checks.${NC}"
    else
        echo -e "${YELLOW}[!] luac compiler not found. (Optional: sudo apt-get install lua5.3)${NC}"
    fi

    # Run Python initialization logic
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" install
else
    ensure_environment
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" "$@"
fi
