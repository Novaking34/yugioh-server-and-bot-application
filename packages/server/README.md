# 🖥️ Yu-Gi-Oh! Server & Host 24/7 Installation Package (`packages/server/`)

This package contains all automated deployment scripts, container orchestration files, Cloudflare Zero Trust Tunnel scripts, DuckDNS auto-updaters, and systemd 24/7 background service definitions required to deploy, run, and maintain the live Yu-Gi-Oh! custom card, story, and duel simulator platform on any Linux host.

---

## 📁 Package Layout & Manifest

```bash
packages/server/
├── README.md                      # Host server deployment guide (this file)
├── deploy_oracle_cloud.sh         # Turn-key 1-click installer for Ubuntu / Oracle Cloud
├── docker-compose.yml             # Symlink to project root docker-compose.yml
├── thelandofkustomazi.com.zone    # Symlink to config/dns/thelandofkustomazi.com.zone
├── setup_cloudflare_tunnel.sh     # Convenience symlink to scripts/setup_cloudflare_tunnel.sh
├── update_duckdns.sh              # Convenience symlink to scripts/update_duckdns.sh
├── scripts/                       # Networking & dynamic DNS automation scripts
│   ├── setup_cloudflare_tunnel.sh # Cloudflare Tunnel manager (Quick & Named tunnels)
│   ├── update_duckdns.sh          # DuckDNS dynamic DNS IPv4 auto-updater
│   └── README.md                  # Scripts documentation and CLI flags guide
└── systemd/                       # 24/7 background service daemons & auto-start
    ├── install_services.sh        # Systemd daemon registration & activation script
    ├── ygo-simulator.service      # Live duel engine container unit (TCP 7911/7922)
    ├── ygo-web.service            # FastAPI Web Catalog & REST API unit (Port 8000)
    ├── ygo-bot.service            # The Great Kasutamaiza Discord bot unit
    ├── ygo-tunnel.service         # Optional cloudflared Quick Tunnel unit
    └── README.md                  # Systemd documentation & operational commands
```

---

## 🚀 1. Turn-Key Deployment (Oracle Cloud / Ubuntu Linux)

To deploy on a fresh Ubuntu 22.04 / 24.04 server (such as Oracle Cloud Free Tier `VM.Standard.E2.1.Micro` or `VM.Standard.A1.Flex`):

```bash
cd packages/server
sudo ./deploy_oracle_cloud.sh
```

### What this script automates

1. **System Dependencies:** Installs Python 3, venv, Docker, git, curl, jq, sqlite3, iptables, netfilter-persistent.
2. **Firewall & Port Rules:** Opens incoming TCP ports `7911` (EDOPro Duel Engine), `7922` (Web Room Manager), and `8000` (FastAPI Web Portal & Card API).
3. **Card Pool Initialization:** Compiles the custom card database (`custom_cards.cdb`) and generates Lua scripts.
4. **Simulator Docker Container:** Launches the `professorseanex/ygoserver:latest` container with automatic restart policies.
5. **Systemd 24/7 Services:** Installs and enables `ygo-simulator.service`, `ygo-web.service`, and `ygo-bot.service`.

---

## 🌐 2. Domain & DNS Configuration

### A. Dynamic DNS (`thelandofkustomazi.duckdns.org`)

The script [`packages/server/scripts/update_duckdns.sh`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.sh) keeps your DuckDNS subdomain pointing to your server's current public IP.

Add it to cron to run every 5 minutes:

```bash
crontab -e
# Add line:
*/5 * * * * /home/ubuntu/yugioh-server/packages/server/scripts/update_duckdns.sh >/dev/null 2>&1
```

### B. Custom Domain (`thelandofkustomazi.com`)

The DNS zone configuration is centralized at [`config/dns/thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/config/dns/thelandofkustomazi.com.zone).

To import into Cloudflare DNS:

1. Open Cloudflare Dashboard ➔ `thelandofkustomazi.com` ➔ **DNS** ➔ **Records**.
2. Click **Advanced -> Import and Export** ➔ **Import**.
3. Select [`thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/packages/server/thelandofkustomazi.com.zone).
4. Verify:
   - `@` and `www` CNAME point to your Cloudflare Tunnel with **Proxied (Orange Cloud)**.
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
sudo cloudflared service install <YOUR_CLOUDFLARE_TUNNEL_TOKEN>
```

---

## ⚙️ 4. 24/7 Background Systemd Daemons

To register and enable all platform background services manually:

```bash
cd packages/server/systemd
sudo ./install_services.sh
```

Inspect service health:

```bash
sudo systemctl status ygo-simulator ygo-web ygo-bot cloudflared --no-pager
```
