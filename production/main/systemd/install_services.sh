#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Platform - 24/7 Systemd Service Installer
# =============================================================================
# Installs background services so the simulator container, discord bot,
# and web dashboard start automatically on system boot and restart on crashes.
#
# Usage:
#   sudo ./install_services.sh
# =============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
    echo "[-] Error: Please run as root (use sudo ./install_services.sh)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
CURRENT_USER="${SUDO_USER:-$USER}"

echo "[*] Installing Yu-Gi-Oh! 24/7 Systemd Services for user: $CURRENT_USER..."

# Update user paths dynamically in service files
for sfile in ygo-simulator.service ygo-bot.service ygo-web.service; do
    sed -e "s|/home/professorseanex/yugioh-server|$BASE_DIR|g" \
        -e "s|User=professorseanex|User=$CURRENT_USER|g" \
        "$SCRIPT_DIR/$sfile" > "/etc/systemd/system/$sfile"
    echo "  [+] Installed /etc/systemd/system/$sfile"
done

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable ygo-simulator.service
systemctl enable ygo-bot.service
systemctl enable ygo-web.service

echo ""
echo "====================================================================="
echo "🎉 SUCCESS: All 3 platform services are enabled for 24/7 operation!"
echo "====================================================================="
echo "To start services now:"
echo "  sudo systemctl start ygo-simulator"
echo "  sudo systemctl start ygo-web"
echo "  sudo systemctl start ygo-bot"
echo ""
echo "To check live service status:"
echo "  sudo systemctl status ygo-bot"
echo "  sudo systemctl status ygo-simulator"
echo "  sudo systemctl status ygo-web"
echo "====================================================================="
