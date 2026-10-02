# 🌌 Yu-Gi-Oh! Server, Discord Bot & 24/7 Cloudflare / Oracle Setup Guide

Complete, step-by-step production deployment guide to bring **The Great Kasutamaiza** Discord bot online, deploy a 24/7 persistent host on **Oracle Cloud Infrastructure (OCI Free Tier)**, and configure **Cloudflare Tunnel & DNS** for global card synchronization.

---

## Table of Contents

1. [Discord Bot Activation & Invite](#1-discord-bot-activation--invite)
2. [Oracle Cloud (OCI Free Tier) 24/7 Hosting](#2-oracle-cloud-oci-free-tier-247-hosting)
3. [Cloudflare Tunnel & DNS Configuration](#3-cloudflare-tunnel--dns-configuration)
4. [Client & Remote Player Connection](#4-client--remote-player-connection)
5. [24/7 Operations & Maintenance Cheat-Sheet](#5-247-operations--maintenance-cheat-sheet)

---

## 1. Discord Bot Activation & Invite

### Bot Identity

- **Bot Name**: The Great Kasutamaiza
- **Application ID**: `1555176044536012880`
- **Configured Guild ID**: `1551494268575817778`

### Step 1.1: Privileged Gateway Intents (Recommended)

Modern Discord bots require explicit intent permissions to read chat prefixes:

1. Visit the [Discord Developer Portal](https://discord.com/developers/applications/1555176044536012880/bot).
2. Click **"Bot"** in the left sidebar.
3. Scroll down to **"Privileged Gateway Intents"**.
4. Enable:
   - ✅ **Message Content Intent** (required for prefix commands like `!card`)
   - ✅ **Server Members Intent** (required for `/duel_role` assignment)
5. Click **"Save Changes"**.

> **Note**: Our bot features automatic intent fallback. Even if Privileged Intents are disabled, the bot automatically boots in Standard Intent mode with all 21 slash commands (`/card`, `/duel`, `/mydeck`, `/lore`, `/admin`, etc.) 100% active.

### Step 1.2: One-Click Invite Link

To authorize the bot into your Discord server with all necessary permissions (Slash Commands, Manage Roles, Manage Messages, Embeds, Attachments):

👉 **[Click Here to Invite The Great Kasutamaiza](https://discord.com/oauth2/authorize?client_id=1555176044536012880&permissions=277025778752&scope=bot%20applications.commands)**

Direct URL:

```text
https://discord.com/oauth2/authorize?client_id=1555176044536012880&permissions=277025778752&scope=bot%20applications.commands
```

### Step 1.3: Starting the Bot

- **Local Interactive Run**:

  ```bash
  ./manage.sh bot
  ```

- **24/7 Systemd Background Service**:

  ```bash
  sudo systemctl start ygo-bot
  sudo systemctl status ygo-bot
  ```

---

## 2. Oracle Cloud (OCI Free Tier) 24/7 Hosting

Oracle Cloud provides an **"Always Free"** tier that is permanently free ($0/month, no expiration).

### Recommended Free Tier Specs

- **Shape**: `VM.Standard.A1.Flex` (Ampere Arm)
- **CPUs**: 4 OCPUs (or 2 OCPUs)
- **RAM**: 24 GB RAM (or 12 GB RAM)
- **Storage**: 50 GB to 200 GB NVMe Boot Volume
- **OS**: Ubuntu 24.04 or 22.04 LTS (Minimal or Standard)

---

### Step 2.1: Open Ports in Oracle Cloud Web Console (VCN Security Lists)

Oracle Cloud Virtual Cloud Networks block all incoming traffic except SSH (port 22) by default. You must add Ingress Rules in the web console:

1. Log into your [Oracle Cloud Console](https://cloud.oracle.com/).
2. Navigate to: **Networking** ➔ **Virtual Cloud Networks (VCN)**.
3. Select your VCN ➔ Click **Security Lists** (e.g. `Default Security List for...`).
4. Click **"Add Ingress Rules"** and add these three rules:

| Source CIDR | IP Protocol | Destination Port Range | Description |
| :--- | :--- | :--- | :--- |
| `0.0.0.0/0` | TCP | `7911` | YGOPro/EDOPro Live Duel Simulator |
| `0.0.0.0/0` | TCP | `7922` | Duel Room Manager API & WebSocket |
| `0.0.0.0/0` | TCP | `8000` | Web Card Catalog & Expansion Sync |

---

### Step 2.2: Automated Turn-Key Deployment Script

Once your Oracle Cloud VM is booted and you SSH into it (`ssh ubuntu@<YOUR_VM_IP>`):

```bash
# 1. Clone your repository
git clone https://github.com/Novaking34/yugioh-server-and-bot-application.git yugioh-server
cd yugioh-server

# 2. Configure your Discord Token and Environment
cp production/main/discord_bot/config.example.json production/main/discord_bot/config.json
cat << 'EOF' > .env
DISCORD_BOT_TOKEN="your_discord_bot_token_here"
DISCORD_GUILD_ID="1551494268575817778"
SIMULATOR_HOST="localhost"
SIMULATOR_PORT="7911"
WEB_PORT="8000"
EOF

# 3. Run the automated deployment script
chmod +x packages/server/deploy_oracle_cloud.sh
sudo ./packages/server/deploy_oracle_cloud.sh
```

### What `deploy_oracle_cloud.sh` does automatically

1. Installs Docker, Python 3 venv, Git, and system libraries.
2. Unblocks Oracle Linux `iptables` and UFW for ports `7911`, `7922`, and `8000`.
3. Compiles `custom_cards.cdb` and generates Lua effect scripts.
4. Spawns the Docker duel engine container.
5. Registers and starts all 3 systemd services (`ygo-simulator`, `ygo-web`, `ygo-bot`) to run 24/7 on boot.

---

## 3. Cloudflare Tunnel & DNS Configuration

### Understanding Duel Traffic vs Web Traffic

- **Port 7911 (Duel Engine)**: EDOPro / Project Ignis connects via **raw TCP socket protocol**. Standard Cloudflare CDN (Orange Cloud) only proxies HTTP/HTTPS.
- **Port 8000 (Web Catalog & Expansion Sync)**: Full HTTP REST API and web UI. This **can and should** be proxied through Cloudflare for free SSL/TLS, DDoS mitigation, and global edge caching!

---

### Option A: Cloudflare Quick Tunnel (Free, No Account / Domain Needed)

You can expose the Web Catalog & Card Sync Manifest to a public HTTPS URL instantly:

```bash
./manage.sh tunnel
# Or directly:
./production/main/setup_cloudflare_tunnel.sh --quick
```

**Output:**

```text
=====================================================================
  🎉 CLOUDFLARE QUICK TUNNEL IS ACTIVE!
=====================================================================
Public HTTPS URL:        https://mystic-dragon-realm.trycloudflare.com
Web Card Catalog:        https://mystic-dragon-realm.trycloudflare.com/
Card Manifest Sync API:  https://mystic-dragon-realm.trycloudflare.com/api/manifest
=====================================================================
```

*The script automatically updates `production/shared/config.json` with this URL so player clients download custom cards over HTTPS.*

---

### Option B: Named Cloudflare Tunnel (Your Custom Domain)

If you own a domain on Cloudflare (e.g. `yourdomain.com`):

1. Go to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2. Navigate to **Networks** ➔ **Tunnels** ➔ **Create a Tunnel**.
3. Choose **Cloudflared** ➔ Name it (e.g. `ygo-server`).
4. Copy your Tunnel Token (`eyJh...`).
5. Add it to your `.env` file:

   ```bash
   CLOUDFLARE_TUNNEL_TOKEN="your_token_here"
   ```

6. In the Cloudflare Dashboard **Public Hostname** tab:
   - Subdomain: `cards` (or `catalog`)
   - Domain: `yourdomain.com`
   - Service Type: `HTTP`
   - URL: `localhost:8000`
7. Run the tunnel:

   ```bash
   ./manage.sh tunnel
   ```

---

### Option C: DNS A-Record for Duel Server (Port 7911)

To allow players to type `duel.yourdomain.com:7911` into EDOPro:

1. In the Cloudflare Dashboard ➔ Click your domain ➔ **DNS** ➔ **Records**.
2. Click **"Add Record"**:
   - **Type**: `A`
   - **Name**: `duel`
   - **IPv4 Address**: `<YOUR_ORACLE_PUBLIC_IP>`
   - **Proxy Status**: ⚠️ **DNS Only (Grey Cloud)** *(Crucial: must be Grey Cloud so raw TCP 7911 is passed directly)*.
   - **TTL**: Auto.

---

## 4. Client & Remote Player Connection

When other players want to duel on your server:

1. **Distribute the Player Client Folder**:
   Share the `production/shared/` folder (or ZIP archive) with your players.
2. **One-Click Card Sync**:
   - **Windows**: Double-click `launch_client.bat` or `install_client.bat`.
   - **Mac/Linux**: Run `./launch_client.sh`.
   - The sync client automatically connects to your Cloudflare HTTPS URL, downloads `custom_cards.cdb`, Lua scripts, and sample decks directly into their EDOPro/YGOPro `expansions/` folder!
3. **Connecting in EDOPro**:
   - Host / IP: `duel.yourdomain.com` (or your Oracle Public IP)
   - Port: `7911`
   - Join room or type room code!

---

## 5. 24/7 Operations & Maintenance Cheat-Sheet

| Action | Command |
| :--- | :--- |
| **Check Platform Status** | `./manage.sh status` |
| **View Discord Bot Live Logs** | `sudo journalctl -u ygo-bot -f` |
| **Restart Discord Bot** | `sudo systemctl restart ygo-bot` |
| **View Web Catalog Logs** | `sudo journalctl -u ygo-web -f` |
| **Restart Simulator Container** | `./manage.sh restart` or `sudo systemctl restart ygo-simulator` |
| **Recompile CDB & Lua live** | In Discord: `/admin sync_cards` (or `./manage.sh sync`) |
| **Launch Cloudflare Tunnel** | `./manage.sh tunnel` |
| **Run Full Test Suite** | `./manage.sh test` |
