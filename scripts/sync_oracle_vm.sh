#!/usr/bin/env bash
# =============================================================================
# Yu-Gi-Oh! Server & Bot - Oracle Cloud VM Synchronization Script
# =============================================================================
# Automates deployment to the Oracle Cloud VM:
# 1. Verifies local repository state and commits if message provided.
# 2. Pushes local changes to origin master on GitHub.
# 3. Connects via SSH to Oracle VM (147.224.147.30) using oracle_key.pem.
# 4. Pulls latest master branch on the remote server.
# 5. Runs './manage.sh sync' on remote (compiles CDB, builds Lua scripts).
# 6. Restarts production services: ygo-bot.service & ygo-web.service.
# 7. Verifies and displays systemd service health.
# =============================================================================

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# ANSI Terminal Styling
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BOLD="\033[1m"
NC="\033[0m"

# Configuration (defaults can be overridden via environment)
ORACLE_HOST="${ORACLE_VM_HOST:-147.224.147.30}"
ORACLE_USER="${ORACLE_VM_USER:-ubuntu}"
SSH_KEY="${ORACLE_SSH_KEY:-$HOME/.ssh/oracle_key.pem}"
REMOTE_DIR="/home/ubuntu/yugioh-server"

echo -e "${BOLD}${BLUE}=====================================================================${NC}"
echo -e "${BOLD}${BLUE}  🌌 Oracle Cloud VM Automated Synchronization Gateway              ${NC}"
echo -e "${BOLD}${BLUE}  Target: ${ORACLE_USER}@${ORACLE_HOST} (${REMOTE_DIR})               ${NC}"
echo -e "${BOLD}${BLUE}=====================================================================${NC}"

# 1. Verify SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}[!] SSH Private Key not found at: ${SSH_KEY}${NC}"
    echo -e "    Please specify valid key path via ORACLE_SSH_KEY env var."
    exit 1
fi

# Ensure correct permissions on SSH key
chmod 600 "$SSH_KEY" 2>/dev/null || true

# 2. Check Git Status & Push
echo -e "\n${BLUE}[1/4] Checking Local Git Status & GitHub Origin...${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    COMMIT_MSG="$*"
    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="Auto-sync: update bot services and deck legality $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    echo -e "${YELLOW}[*] Staging and committing local changes: '${COMMIT_MSG}'...${NC}"
    git add -A
    git commit -m "$COMMIT_MSG"
fi

# Push to origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}[*] Pushing branch '${CURRENT_BRANCH}' to origin...${NC}"
git push origin "$CURRENT_BRANCH"
echo -e "${GREEN}[+] Local changes successfully pushed to origin/${CURRENT_BRANCH}.${NC}"

# 3. Remote Synchronization on Oracle VM
echo -e "\n${BLUE}[2/4] Connecting to Oracle Cloud VM (${ORACLE_HOST})...${NC}"

SSH_CMD="ssh -i \"$SSH_KEY\" -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \"${ORACLE_USER}@${ORACLE_HOST}\""

eval $SSH_CMD << 'EOF'
set -e
GREEN="\033[0;32m"
BLUE="\033[0;34m"
NC="\033[0m"

echo -e "${BLUE}[3/4] Pulling latest repository code on Oracle VM...${NC}"
cd /home/ubuntu/yugioh-server

# Handle any transient local DB changes on server cleanly
git stash 2>/dev/null || true
git fetch origin master
git checkout master
git pull origin master

# Run sync on server to regenerate CDB and Lua effect scripts
echo -e "${BLUE}[*] Regenerating CDB card database and Lua scripts on VM...${NC}"
if [ -f "./manage.sh" ]; then
    ./manage.sh sync || true
fi

# Restart systemd services
echo -e "\n${BLUE}[4/4] Restarting ygo-bot.service and ygo-web.service...${NC}"
sudo systemctl restart ygo-bot.service
sudo systemctl restart ygo-web.service
sleep 2

# Verify status
echo -e "\n${GREEN}=== LIVE SERVICE STATUS ON ORACLE VM ===${NC}"
BOT_STATUS=$(sudo systemctl is-active ygo-bot.service || echo "failed")
WEB_STATUS=$(sudo systemctl is-active ygo-web.service || echo "failed")

echo -e " • ygo-bot.service: [${BOT_STATUS}]"
echo -e " • ygo-web.service: [${WEB_STATUS}]"

if [ "$BOT_STATUS" = "active" ] && [ "$WEB_STATUS" = "active" ]; then
    echo -e "${GREEN}✨ All services are active and running live on Oracle Cloud!${NC}"
else
    echo -e "\033[1;31m[!] Warning: One or more services failed to activate! Recent logs:${NC}"
    sudo journalctl -u ygo-bot.service -n 20 --no-pager
    exit 1
fi
EOF

echo -e "\n${BOLD}${GREEN}=====================================================================${NC}"
echo -e "${BOLD}${GREEN}  ✅ Oracle Cloud VM Synchronization Complete!                      ${NC}"
echo -e "${BOLD}${GREEN}=====================================================================${NC}"
