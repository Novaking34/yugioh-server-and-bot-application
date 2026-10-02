# 📦 Yu-Gi-Oh! Platform Installation & Distribution Packages

This directory contains standalone, self-contained packages for deploying the platform host server and distributing client expansions to players.

---

## 📂 Packages Overview

```bash
packages/
├── README.md                          # Packaging subsystem documentation (this file)
├── server/                            # Server & Host 24/7 Installation Package
│   ├── README.md                      # Comprehensive server deployment & operations guide
│   ├── deploy_oracle_cloud.sh         # Automated turn-key installer for Oracle Cloud / Ubuntu VM
│   ├── docker-compose.yml             # Container orchestration manifest (symlink to root)
│   ├── start_server.bat               # Windows server host launcher & service controller
│   ├── start_server.sh                # Linux/macOS local server host launcher & controller
│   ├── scripts/                       # Dedicated networking & DNS automation scripts
│   │   ├── setup_cloudflare_tunnel.sh # Cloudflare Tunnel manager (Linux/macOS)
│   │   ├── setup_cloudflare_tunnel.bat# Cloudflare Tunnel manager (Windows Batch)
│   │   ├── setup_cloudflare_tunnel.ps1# Cloudflare Tunnel manager (Windows PowerShell)
│   │   ├── update_duckdns.sh          # DuckDNS dynamic DNS auto-updater (Linux/macOS)
│   │   ├── update_duckdns.bat         # DuckDNS dynamic DNS auto-updater (Windows Batch)
│   │   ├── update_duckdns.ps1         # DuckDNS dynamic DNS auto-updater (Windows PowerShell)
│   │   └── README.md                  # Scripts documentation and CLI flags guide
│   └── systemd/                       # 24/7 background systemd services (Linux)
│       ├── install_services.sh        # Automated systemd service installer
│       ├── ygo-simulator.service      # Duel engine container unit (TCP 7911/7922)
│       ├── ygo-web.service            # FastAPI web catalog & REST API (Port 8000)
│       ├── ygo-bot.service            # The Great Kasutamaiza Discord bot unit
│       ├── ygo-tunnel.service         # Cloudflare Tunnel daemon unit
│       └── README.md                  # Systemd service documentation & operations
│
└── client/                            # Player & Client Distribution Package
    ├── README.md                      # Player setup & connection guide
    ├── config.json                    # Symlink to config/client/config.json
    ├── install_client.sh              # Linux / macOS one-click installer
    ├── install_client.bat             # Windows one-click installer
    ├── launch_client.sh               # Linux / macOS launcher for Player GUI
    ├── launch_client.bat              # Windows launcher for Player GUI
    ├── __main__.py                    # Direct Python package execution (`python -m packages.client`)
    └── src/                           # Client Python application source code
        ├── __init__.py                # Package exports & initialization
        ├── sync_client.py             # EDOPro card database & expansion synchronizer
        ├── client_app.py              # Native desktop player control panel (Tkinter)
        └── README.md                  # Internal source architecture documentation
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

### Linux / macOS / Steam Deck

```bash
cd packages/client
./install_client.sh
./launch_client.sh
```

For full details and direct IP connect settings, see [`packages/client/README.md`](file:///home/professorseanex/yugioh-server/packages/client/README.md).

---

## 📦 Building Distributable Release Archives

The master controller bundles these packages into clean release archives in `dist/`:

```bash
./manage.sh package
```

This generates:

1. `dist/ygo-client-package.zip`: Pre-packaged with the latest compiled `custom_cards.cdb`, Lua effect scripts, decklists, and one-click installers for distribution to players.
2. `dist/ygo-server-package.tar.gz`: Pre-packaged host server deployment package with all scripts, systemd units, Docker manifests, and DNS zone configurations.
3. `dist/SHA256SUMS.txt`: Cryptographic SHA-256 verification digests.
