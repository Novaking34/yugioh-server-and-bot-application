#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Custom Expansions - Player Client 1-Click Installer (Linux / macOS)
# =============================================================================
# Installs custom card database (CDB), Lua scripts, and pre-made decks directly
# into your local EDOPro / Project Ignis or YGOPro game client directory.
#
# Usage:
#   ./install_client.sh
#   ./install_client.sh --path /custom/path/to/EDOPro
#   ./install_client.sh --server https://thelandofkustomazi.com
# =============================================================================

set -e

# Resolve canonical script directory (supporting symlinked execution)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/src/sync_client.py"

if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "[-] Error: Installer engine not found at $SYNC_SCRIPT"
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SYNC_SCRIPT" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$SYNC_SCRIPT" "$@"
else
    echo "[-] Error: Python 3 is required to run the installer."
    echo "    Please install Python 3 using your system package manager."
    exit 1
fi
