#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Custom Expansions - Player Client Installer
# =============================================================================
# Run this script to install custom cards, scripts, and decks into your local
# EDOPro / Project Ignis or YGOPro game client.
#
# Usage:
#   ./install_client.sh
#   ./install_client.sh --path /path/to/EDOPro
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/sync_client.py" "$@"
elif command -v python >/dev/null 2>&1; then
    python "$SCRIPT_DIR/sync_client.py" "$@"
else
    echo "[-] Error: Python 3 is required to run the installer."
    exit 1
fi
