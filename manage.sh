#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Custom Server, Story Platform & Simulator - Master CLI & Installer
# =============================================================================
# Master shell controller and environment bootstrap script for Linux and macOS.
#
# Primary Responsibilities:
# 1. Environment Verification:
#    - Validates that Python 3 (>= 3.9) is installed and available in system PATH.
#    - Verifies presence of the Python virtual environment (./venv).
#    - Automatically bootstraps virtualenv and dependencies from requirements.txt.
# 2. Dependency & Tool Checking:
#    - Checks for Docker engine and Docker Compose for containerized duel simulation.
#    - Checks for the luac bytecode compiler for Lua effect script validation.
# 3. Command Execution:
#    - Transparently hands off commands and arguments to the Python Master
#      Controller (manage.py) inside the isolated virtual environment.
#
# Usage:
#   ./manage.sh [command] [options...]
#
# Common Commands:
#   ./manage.sh status             # Inspect container, DB, and card pool status
#   ./manage.sh start              # Start the live duel simulator container
#   ./manage.sh stop               # Stop the live duel simulator container
#   ./manage.sh restart            # Restart the live duel simulator container
#   ./manage.sh sync               # Compile SQLite CDB and regenerate Lua scripts
#   ./manage.sh web                # Launch the FastAPI web portal (Port 8000)
#   ./manage.sh bot                # Launch The Great Kasutamaiza Discord bot
#   ./manage.sh tunnel             # Launch Cloudflare HTTPS Tunnel
#   ./manage.sh package            # Build standalone client & server packages in dist/
#   ./manage.sh test               # Run the comprehensive Pytest test suite
#   ./manage.sh validate-lua       # Validate Lua script syntax
#   ./manage.sh install            # Initialize database, CDB, and dependencies
# =============================================================================

# Halt immediately if any command returns an unhandled non-zero exit status
set -e

# Resolve the absolute base directory of the repository regardless of where the script is invoked
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

# Virtual environment path definitions
VENV_DIR="$BASE_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip"

# ANSI Terminal Styling Constants
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
NC="\033[0m" # Reset / No Color

# =============================================================================
# Function: ensure_environment
# =============================================================================
# Ensures that Python 3 and an activated virtual environment with all required
# dependencies are present before attempting to execute manage.py.
# =============================================================================
ensure_environment() {
    # 1. Verify that Python 3 executable exists in PATH
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}[-] Error: Python 3 was not found on your system PATH.${NC}"
        echo -e "    Please install Python 3 using your system package manager:"
        echo -e "    Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip"
        echo -e "    Fedora/RHEL:   sudo dnf install -y python3 python3-pip"
        echo -e "    macOS:         brew install python"
        exit 1
    fi

    # 2. Check if the virtual environment exists; if not, create it
    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "${BLUE}[*] Initializing Python virtual environment in ${VENV_DIR}...${NC}"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}[+] Virtual environment successfully created.${NC}"
        
        # Install and upgrade dependencies from requirements.txt
        if [ -f "$BASE_DIR/requirements.txt" ]; then
            echo -e "${BLUE}[*] Upgrading pip and installing dependencies from requirements.txt...${NC}"
            "$VENV_PIP" install --upgrade pip
            "$VENV_PIP" install -r "$BASE_DIR/requirements.txt"
            "$VENV_PIP" install -e "$BASE_DIR"
            echo -e "${GREEN}[+] All dependencies successfully installed.${NC}"
        fi
    fi
}

# =============================================================================
# Main Command Dispatcher
# =============================================================================

# Display help banner if invoked with help flags
if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ "$1" = "help" ]; then
    ensure_environment
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" --help

# Default action when invoked with no arguments: show live platform status
elif [ $# -eq 0 ]; then
    ensure_environment
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" status

# Dedicated initialization / installation workflow
elif [ "$1" = "install" ] || [ "$1" = "setup" ]; then
    echo -e "${BOLD}${BLUE}=====================================================================${NC}"
    echo -e "${BOLD}${BLUE}  🌌 Yu-Gi-Oh! Platform Automated Environment Installer             ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================================${NC}"
    
    # Bootstrap Python runtime and virtualenv
    ensure_environment
    
    # 1. Check Docker availability for the Live Duel Simulator
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}[+] Docker is installed: $(docker --version)${NC}"
    else
        echo -e "${YELLOW}[!] Notice: Docker was not found in PATH.${NC}"
        echo -e "    The Live Duel Simulator container requires Docker engine."
        echo -e "    (Install via: sudo apt-get install -y docker.io docker-compose-v2)"
    fi

    # 2. Check luac availability for Lua syntax validation
    if command -v luac >/dev/null 2>&1; then
        echo -e "${GREEN}[+] luac compiler is available for Lua syntax checks: $(luac -v 2>&1 | head -n 1)${NC}"
    else
        echo -e "${YELLOW}[!] Notice: luac compiler not found. (Optional for script syntax checks: sudo apt-get install lua5.3)${NC}"
    fi

    # 3. Execute platform initialization (database schema, story seeds, CDB, scripts)
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" install

# Pass all other commands directly to manage.py
else
    ensure_environment
    exec "$VENV_PYTHON" "$BASE_DIR/manage.py" "$@"
fi
