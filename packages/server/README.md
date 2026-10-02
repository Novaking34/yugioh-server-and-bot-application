# 🖥️ Yu-Gi-Oh! Server & Host Platform Package (`packages/server/`)

This package contains all automated deployment scripts, container orchestration files, Cloudflare Zero Trust Tunnel scripts, DuckDNS dynamic DNS auto-updaters, local service launchers, and systemd 24/7 background service definitions required to deploy, run, and maintain the live Yu-Gi-Oh! custom card, story, and duel simulator platform on Linux, Oracle Cloud, and Windows host environments.

---

## 📁 Package Layout & Manifest

```bash
packages/server/
├── README.md                      # Host server deployment guide (this file)
├── deploy_oracle_cloud.sh         # Turn-key 1-click installer for Ubuntu / Oracle Cloud VPS
├── docker-compose.yml             # Container orchestration manifest (symlink to root)
├── start_server.bat               # Windows server host launcher & service controller
├── start_server.sh                # Linux/macOS local server host launcher & controller
├── scripts/                       # Networking & dynamic DNS automation scripts
│   ├── setup_cloudflare_tunnel.sh # Cloudflare Tunnel manager (Linux/macOS)
│   ├── setup_cloudflare_tunnel.bat# Cloudflare Tunnel manager (Windows Batch)
│   ├── setup_cloudflare_tunnel.ps1# Cloudflare Tunnel manager (Windows PowerShell)
│   ├── update_duckdns.sh          # DuckDNS dynamic DNS IPv4 updater (Linux/macOS)
│   ├── update_duckdns.bat         # DuckDNS dynamic DNS IPv4 updater (Windows Batch)
│   ├── update_duckdns.ps1         # DuckDNS dynamic DNS IPv4 updater (Windows PowerShell)
│   └── README.md                  # Scripts documentation and CLI flags guide
└── systemd/                       # 24/7 background service daemons & auto-start (Linux)
    ├── install_services.sh        # Systemd daemon registration & activation script
    ├── ygo-simulator.service      # Live duel engine container unit (TCP 7911/7922)
    ├── ygo-web.service            # FastAPI Web Catalog & REST API unit (Port 8000)
    ├── ygo-bot.service            # The Great Kasutamaiza Discord bot unit
    ├── ygo-tunnel.service         # Optional cloudflared Quick Tunnel unit
    └── README.md                  # Systemd documentation & operational commands
```

> [!NOTE]
> DNS zone configurations are centralized in [`config/dns/thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/config/dns/thelandofkustomazi.com.zone) per the repository architecture standards.

---

## 🪟 1. Running on Windows (`start_server.bat`)

For Windows host machines (development workstations or Windows dedicated servers):

### Interactive Management Menu

Double-click [`start_server.bat`](file:///home/professorseanex/yugioh-server/packages/server/start_server.bat) or run from PowerShell / Command Prompt:

```cmd
cd packages\server
start_server.bat
```

This presents an interactive menu to:

1. **Start Full Stack**: Launches ocgcore Docker container, FastAPI Web server, and Discord bot in separate managed windows.
2. **Start Live Duel Simulator**: Runs `docker compose up -d` for raw TCP duel ports `7911` & `7922`.
3. **Start Web Catalog & API**: Runs `uvicorn` on `http://localhost:8000`.
4. **Start Discord Bot**: Runs `The Great Kasutamaiza` story & duel bot.
5. **Synchronize Cards**: Compiles `custom_cards.cdb` and regenerates Lua scripts.
6. **Start Cloudflare Tunnel**: Runs [`scripts/setup_cloudflare_tunnel.bat`](file:///home/professorseanex/yugioh-server/packages/server/scripts/setup_cloudflare_tunnel.bat).
7. **Update DuckDNS**: Runs [`scripts/update_duckdns.bat`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.bat).
8. **Stop Containers**: Shuts down Docker Compose containers.

### Direct CLI Commands

```cmd
start_server.bat all         # Start all services
start_server.bat web         # Start Web Catalog
start_server.bat bot         # Start Discord Bot
start_server.bat simulator   # Start Docker Simulator
start_server.bat sync        # Compile CDB & Lua scripts
start_server.bat stop        # Stop containers
```

---

## 🚀 2. Turn-Key Linux / Cloud Deployment (`deploy_oracle_cloud.sh`)

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

## 🐧 3. Local Unix / Linux Launcher (`start_server.sh`)

If running locally on Linux or macOS without systemd daemons:

```bash
cd packages/server
./start_server.sh
# Or pass directly:
./start_server.sh all
./start_server.sh web
./start_server.sh bot
./start_server.sh stop
```

---

## 🌐 4. Domain & DNS Configuration

### A. Dynamic DNS (`thelandofkustomazi.duckdns.org`)

The scripts in `packages/server/scripts/` keep your DuckDNS subdomain synchronized with your host's public IP:

* **Linux / Cron (runs every 5 min):**

  ```bash
  crontab -e
  # Add:
  */5 * * * * /home/ubuntu/yugioh-server/packages/server/scripts/update_duckdns.sh >/dev/null 2>&1
  ```

* **Windows / Task Scheduler:**

  ```cmd
  schtasks /create /tn "DuckDNS_AutoUpdate" /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\path\to\packages\server\scripts\update_duckdns.ps1" /sc minute /mo 5 /f
  ```

### B. Custom Domain (`thelandofkustomazi.com`)

The DNS zone configuration is centralized at [`config/dns/thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/config/dns/thelandofkustomazi.com.zone).

To import into Cloudflare DNS:

1. Open Cloudflare Dashboard ➔ `thelandofkustomazi.com` ➔ **DNS** ➔ **Records**.
2. Click **Advanced -> Import and Export** ➔ **Import**.
3. Select [`config/dns/thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/config/dns/thelandofkustomazi.com.zone).
4. Verify:
   * `@` and `www` CNAME point to your Cloudflare Tunnel with **Proxied (Orange Cloud)**.
   * `play` and `sim` A records point to `147.224.147.30` with **DNS-Only (Grey Cloud)** for raw TCP duel connections.

---

## 🔒 5. Cloudflare Named Tunnel Setup

To route web traffic through Cloudflare's edge network:

* **Linux:**

  ```bash
  cd packages/server/scripts
  ./setup_cloudflare_tunnel.sh --token <YOUR_CLOUDFLARE_TUNNEL_TOKEN>
  ```

* **Windows:**

  ```cmd
  cd packages\server\scripts
  setup_cloudflare_tunnel.bat --token <YOUR_CLOUDFLARE_TUNNEL_TOKEN>
  ```

---

## ⚙️ 6. 24/7 Background Systemd Daemons (Linux VPS)

To register and enable all platform background services manually:

```bash
cd packages/server/systemd
sudo ./install_services.sh
```

Inspect service health:

```bash
sudo systemctl status ygo-simulator ygo-web ygo-bot cloudflared --no-pager
```
