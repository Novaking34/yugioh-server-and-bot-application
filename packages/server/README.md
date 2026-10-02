# 🖥️ Yu-Gi-Oh! Server & Host 24/7 Installation Package

This package contains all automated deployment scripts, container orchestration files, Cloudflare Tunnel configurations, DuckDNS auto-updaters, and systemd 24/7 service unit files needed to host the full platform.

---

## 📦 Package Contents

| File / Directory | Description |
| --- | --- |
| [`deploy_oracle_cloud.sh`](file:///home/professorseanex/yugioh-server/packages/server/deploy_oracle_cloud.sh) | Turn-key deployment script for Oracle Cloud (OCI) Free Tier / Ubuntu Linux |
| [`setup_cloudflare_tunnel.sh`](file:///home/professorseanex/yugioh-server/packages/server/setup_cloudflare_tunnel.sh) | Automated Cloudflare Tunnel installer (supports Quick & Named tunnels) |
| [`update_duckdns.sh`](file:///home/professorseanex/yugioh-server/packages/server/update_duckdns.sh) | Dynamic DNS sync script for `thelandofkustomazi.duckdns.org` |
| [`thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/packages/server/thelandofkustomazi.com.zone) | Standard BIND DNS zone file for Cloudflare DNS zone import |
| [`docker-compose.yml`](file:///home/professorseanex/yugioh-server/packages/server/docker-compose.yml) | Docker Compose manifest running the `ocgcore` duel engine |
| [`systemd/`](file:///home/professorseanex/yugioh-server/packages/server/systemd/) | Background service definitions for 24/7 continuous operation |
| [`systemd/install_services.sh`](file:///home/professorseanex/yugioh-server/packages/server/systemd/install_services.sh) | Automated installer for systemd background service daemons |

---

## 🚀 1. Turn-Key Deployment (Oracle Cloud / Ubuntu Linux)

To deploy on any fresh Ubuntu 22.04 / 24.04 server (including Oracle Cloud Free Tier `VM.Standard.E2.1.Micro` or `VM.Standard.A1.Flex`):

```bash
cd packages/server
sudo ./deploy_oracle_cloud.sh
```

### What this script automates

1. **System Dependencies:** Installs Python 3, venv, Docker, git, curl, iptables, netfilter-persistent.
2. **Firewall & Port Rules:** Opens incoming TCP ports `7911` (EDOPro Duel Engine), `7922` (Web Room Manager), and `8000` (FastAPI Web Portal & Card API).
3. **Card Pool Initialization:** Compiles the custom card database (`custom_cards.cdb`) and generates Lua scripts.
4. **Simulator Docker Container:** Launches the `professorseanex/ygoserver:latest` container with automatic restart policies.
5. **Systemd 24/7 Services:** Installs and enables `ygo-simulator.service`, `ygo-web.service`, and `ygo-bot.service`.

---

## 🌐 2. Domain & DNS Configuration

### A. Dynamic DNS (`thelandofkustomazi.duckdns.org`)

The script [`update_duckdns.sh`](file:///home/professorseanex/yugioh-server/packages/server/update_duckdns.sh) keeps your DuckDNS subdomain pointing to your server's current public IP.
Add it to cron to run every 5 minutes:

```bash
crontab -e
# Add line:
*/5 * * * * /home/professorseanex/yugioh-server/packages/server/update_duckdns.sh >/dev/null 2>&1
```

### B. Custom Domain (`thelandofkustomazi.com`)

Import [`thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/packages/server/thelandofkustomazi.com.zone) into Cloudflare DNS:

1. Open Cloudflare Dashboard -> `thelandofkustomazi.com` -> **DNS** -> **Records**.
2. Click **Import and Export** -> **Import DNS Records**.
3. Select `thelandofkustomazi.com.zone`.
4. Verify:
   - `@` and `www` CNAME point to your Cloudflare Tunnel (`cfargotunnel.com`) with **Proxied (Orange Cloud)**.
   - `play` and `sim` A records point to `147.224.147.30` with **DNS-Only (Grey Cloud)** for raw TCP duel connections.

---

## 🔒 3. Cloudflare Named Tunnel Setup

To route web traffic through Cloudflare's edge network:

```bash
cd packages/server
./setup_cloudflare_tunnel.sh --token <YOUR_CLOUDFLARE_TUNNEL_TOKEN>
```

Or install as a permanent system service:

```bash
sudo cloudflared service install <YOUR_TOKEN>
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## ⚙️ 4. Managing 24/7 Services

```bash
# Check service status
sudo systemctl status ygo-simulator ygo-web ygo-bot cloudflared

# Restart services
sudo systemctl restart ygo-simulator ygo-web ygo-bot

# View live service logs
sudo journalctl -u ygo-bot -f
sudo journalctl -u ygo-web -f
```
