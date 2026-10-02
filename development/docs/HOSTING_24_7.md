# 🌐 24/7 Persistent Hosting & Cloud Deployment Guide

This guide outlines practical options for hosting the **Yu-Gi-Oh! Live Duel Simulator, Discord Bot, and Web Catalog 24/7**, ensuring the platform remains online even when your personal computer is turned off.

---

## 🏗️ Platform Server-Client Architecture

```bash
                    ┌──────────────────────────────────────────────┐
                    │            24/7 CLOUD HOST / VPS            │
                    │                                              │
                    │  ┌────────────────────────────────────────┐  │
                    │  │ Docker: ocgcore Duel Engine (Port 7911)│  │
                    │  └───────────────────▲────────────────────┘  │
                    │                      │ TCP Connect           │
                    │  ┌───────────────────┴────────────────────┐  │
                    │  │ Discord Bot & Web API (Port 8000)      │  │
                    │  └────────────────────────────────────────┘  │
                    └──────────────────────┬───────────────────────┘
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
┌──────────────────────────┐                               ┌──────────────────────────┐
│   Discord Community      │                               │     Remote Players       │
│ - Slash Commands (/)     │                               │ - EDOPro Client (7911)   │
│ - In-Chat Duels & Decks  │                               │ - 1-Click Sync from HTTP │
└──────────────────────────┘                               └──────────────────────────┘
```

---

## 🏆 Option 1: Oracle Cloud Free Tier (Recommended — $0/Month Forever)

Oracle Cloud Infrastructure (OCI) offers an **Always Free** tier that includes:

- **Compute:** 4 ARM Ampere CPU cores, 24 GB RAM (or split into smaller VMs).
- **Storage:** 200 GB NVMe block volume.
- **IP:** 1 Free Static Public IPv4 address.
- **Bandwidth:** 10 TB/month free outbound transfer.

### Step-by-Step Oracle Cloud Deployment

1. **Create an Oracle Cloud Account:**
   - Sign up at [cloud.oracle.com](https://cloud.oracle.com).
2. **Launch an Always-Free Instance:**
   - Image: **Ubuntu 24.04 LTS** (or 22.04 LTS).
   - Shape: `VM.Standard.A1.Flex` (Assign 2 to 4 OCPUs, 12 to 24 GB RAM).
   - Add your SSH public key and click **Create**.
3. **Open Ingress Firewall Rules in OCI Console:**
   - Go to: **Networking -> Virtual Cloud Networks -> Default Security List -> Add Ingress Rules**:
     - `0.0.0.0/0` -> TCP Port `7911` (EDOPro Duel Engine)
     - `0.0.0.0/0` -> TCP Port `7922` (Simulator Web Room Manager)
     - `0.0.0.0/0` -> TCP Port `8000` (FastAPI Web Catalog Dashboard)
4. **Open Host IPTables Firewall:**
   SSH into your Oracle instance and run:

   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 7911 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 7922 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
   sudo netfilter-persistent save 2>/dev/null || sudo iptables-save | sudo tee /etc/iptables/rules.v4
   ```

5. **Clone Repository & Run Turn-Key Server Deployment Package:**

   ```bash
   git clone <YOUR_GIT_REPO_URL> yugioh-server
   cd yugioh-server/packages/server
   sudo ./deploy_oracle_cloud.sh
   ```

   *This script automatically configures iptables, installs Docker and system packages, initializes the database, compiles custom cards, starts the container, and registers all 24/7 systemd background services.*

6. **Configure Discord Bot Token in `.env`:**

   ```bash
   nano /home/ubuntu/yugioh-server/.env
   # Add:
   DISCORD_BOT_TOKEN="your_token_here"
   DISCORD_GUILD_ID="your_guild_id_here"
   sudo systemctl restart ygo-bot
   ```

7. **Check Live Status:**

   ```bash
   ./manage.sh status
   sudo systemctl status ygo-bot
   ```

---

## 💰 Option 2: Low-Cost VPS Hosting ($3 – $5/Month)

If you prefer standard x86 servers with instant 1-click provisioning:

| Provider | Price | Specs | Best For |
| --- | --- | --- | --- |
| **Hetzner Cloud** | €3.79 / mo | 2 vCPU, 4GB RAM, 40GB NVMe | Best European / US ping |
| **Contabo** | $4.50 / mo | 4 vCPU, 6GB RAM, 100GB NVMe | Huge specs for low price |
| **DigitalOcean** | $4.00 / mo | 1 vCPU, 512MB-1GB RAM | Droplets & easy snapshots |
| **AWS Lightsail** | $3.50 / mo | 1 vCPU, 1GB RAM, 40GB SSD | AWS infrastructure |

### Setup on Any Linux VPS

Simply run:

```bash
sudo apt-get update && sudo apt-get install -y git docker.io docker-compose-v2 python3 python3-venv python3-pip
git clone <YOUR_REPO_URL> yugioh-server
cd yugioh-server
./manage.sh install
sudo ./packages/server/systemd/install_services.sh
```

---

## 🏠 Option 3: Dedicated Home Server / Mini PC / Raspberry Pi 4/5

If you have an old laptop, desktop, or Raspberry Pi running at home:

1. **Advantages:** Zero monthly recurring cost, full physical ownership.
2. **Prevent Sleep Mode on Laptops (Ubuntu/Debian):**

   ```bash
   sudo nano /etc/systemd/logind.conf
   # Set:
   HandleLidSwitch=ignore
   HandleLidSwitchExternalPower=ignore
   # Apply:
   sudo systemctl restart systemd-logind
   ```

3. **Port Forwarding on Your Home Router:**
   - Forward external port `7911` (TCP) -> Home PC internal IP: `7911`
   - Forward external port `8000` (TCP) -> Home PC internal IP: `8000`
4. **Dynamic DNS (DuckDNS / No-IP):**
   - If your ISP changes your home IP, use a free dynamic DNS service like [DuckDNS](https://www.duckdns.org) so players always connect to `yourname.duckdns.org:7911`.

---

## ☁️ Option 4: Cloudflare Tunnels (Zero Port Forwarding for Web & API)

To securely expose the Web Catalog & REST API without exposing your home IP:

1. Install `cloudflared`:

   ```bash
   sudo apt install cloudflared
   ```

2. Authenticate and create a tunnel to port 8000:

   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

3. Cloudflare gives you a free HTTPS domain (e.g. `https://yugioh-custom.trycloudflare.com`) that routes traffic directly to your web catalog and client sync manifest!

---

## 🛠️ Managing 24/7 Services with Systemd

Once services are installed via `sudo ./packages/server/systemd/install_services.sh`:

| Action | Command |
| --- | --- |
| Check Bot Status | `sudo systemctl status ygo-bot` |
| View Live Bot Logs | `sudo journalctl -u ygo-bot -f` |
| Restart Discord Bot | `sudo systemctl restart ygo-bot` |
| Check Simulator Container | `sudo systemctl status ygo-simulator` |
| View Web Catalog Logs | `sudo journalctl -u ygo-web -f` |
| Stop All Services | `sudo systemctl stop ygo-bot ygo-simulator ygo-web` |

All services are configured with `Restart=always` and `RestartSec=5`, meaning if the Discord bot or web service encounters an unexpected crash or the host machine reboots, systemd automatically brings them back online within 5 seconds.
