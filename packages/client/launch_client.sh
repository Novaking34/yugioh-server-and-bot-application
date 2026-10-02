#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Player Client Desktop GUI Launcher (Linux / macOS)
# =============================================================================
# Launches the native desktop Expansion Manager and connection helper.
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
APP_SCRIPT="$SCRIPT_DIR/src/client_app.py"

if [ ! -f "$APP_SCRIPT" ]; then
    echo "[-] Error: Application not found at $APP_SCRIPT"
    exit 1
fi

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$APP_SCRIPT" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$APP_SCRIPT" "$@"
else
    echo "[-] Error: Python 3 is required to run the application."
    echo "    Please install Python 3 using your system package manager."
    exit 1
fi
