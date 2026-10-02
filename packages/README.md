# 📦 Yu-Gi-Oh! Platform Installation & Distribution Packages

This directory contains standalone, self-contained installation packages for deploying the platform host server and distributing the client expansions to players.

---

## 📂 Packages Overview

```bash
packages/
├── README.md                      # Packaging system documentation (this file)
├── server/                        # Server & Host 24/7 Installation Package
│   ├── README.md                  # Comprehensive server deployment & operations guide
│   ├── deploy_oracle_cloud.sh     # Automated turn-key installer for Oracle Cloud / Ubuntu VM
│   ├── setup_cloudflare_tunnel.sh # Cloudflare Tunnel setup & management
│   ├── update_duckdns.sh          # DuckDNS dynamic DNS auto-updater
│   ├── thelandofkustomazi.com.zone # BIND DNS zone file for Cloudflare DNS import
│   ├── docker-compose.yml         # Container orchestration manifest for duel engine
│   └── systemd/                   # 24/7 background systemd services
│       ├── install_services.sh    # Automated systemd service installer
│       ├── ygo-simulator.service  # Duel engine container service
│       ├── ygo-web.service        # FastAPI web catalog & REST API
│       ├── ygo-bot.service        # The Great Kasutamaiza Discord bot
│       └── ygo-tunnel.service     # Cloudflare Tunnel daemon
│
└── client/                        # Player & Client Distribution Package
    ├── README.md                  # Player setup & connection guide
    ├── install_client.sh          # Linux / macOS one-click installer
    ├── install_client.bat         # Windows one-click installer
    ├── launch_client.sh           # Linux / macOS launcher for Player GUI
    ├── launch_client.bat          # Windows launcher for Player GUI
    ├── sync_client.py             # EDOPro card database & expansion synchronizer
    ├── client_app.py              # Native desktop player control panel (Tkinter)
    └── config.json                # Live server connection endpoints manifest
```

---

## 🚀 Quick Start for Administrators (Server Package)

To deploy the entire server stack (Docker duel simulator, Web card catalog, Discord bot, DuckDNS updater, and Cloudflare Tunnel) on any Ubuntu/Debian server or Oracle Cloud Free Tier instance:

```bash
cd packages/server
sudo ./deploy_oracle_cloud.sh
```

For full setup instructions, firewall rules, and custom domain setup, see [`packages/server/README.md`](file:///home/professorseanex/yugioh-server/packages/server/README.md).

---

## 🎮 Quick Start for Players (Client Package)

To duel on this server using **EDOPro / Project Ignis** or **YGOPro**:

### Windows

1. Double-click `install_client.bat` to automatically install the custom card database (`.cdb`), Lua effect scripts, and character decks.
2. Double-click `launch_client.bat` to open the Player Control Panel.

### Linux / macOS

```bash
cd packages/client
./install_client.sh
./launch_client.sh
```

For full details and direct IP connect settings, see [`packages/client/README.md`](file:///home/professorseanex/yugioh-server/packages/client/README.md).

---

## 📦 Building Distributable Release Archives

The master controller can bundle these packages into clean release archives in `dist/`:

```bash
# From repository root:
./manage.sh package
```

This generates:

1. `dist/ygo-client-package.zip`: Pre-packaged with the latest compiled `custom_cards.cdb`, Lua effect scripts, decklists, and one-click installers for distribution to players.
2. `dist/ygo-server-package.tar.gz`: Pre-packaged host server deployment package with all scripts, systemd units, Docker manifests, and DNS zone configurations.
