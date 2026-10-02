# 📦 Platform Packaging & Distribution Guide

This document explains the architecture of the **Installation Packages** and **Distribution System** for the Yu-Gi-Oh! Custom Card, Story & Simulator Platform.

---

## 🏛️ Architecture Overview

The platform separates installation and runtime into organized, modular packages:

```text
yugioh-server/
├── pyproject.toml              # Modern PEP 517/518 Python packaging metadata
├── setup.py                    # Setuptools build script for 'pip install -e .'
├── manage.sh / manage.py / .bat# Master controller & packaging engine
├── config/                     # Centralized Configuration Subsystem
│   ├── client/config.json      # Live server connection manifest
│   ├── dns/                    # BIND DNS zone file (thelandofkustomazi.com.zone)
│   ├── bot/                    # Discord bot settings & config.example.json
│   └── simulator/              # ocgcore room configs & chat filters
├── packages/                   # Root Installation Packages Directory
│   ├── README.md               # Packages overview & quick reference
│   ├── server/                 # Server & Host 24/7 Installation Package
│   │   ├── README.md           # Server deployment & operations guide
│   │   ├── deploy_oracle_cloud.sh # Turnkey installer for Oracle Cloud / Ubuntu VM
│   │   ├── docker-compose.yml  # Simulator container orchestration manifest (symlink)
│   │   ├── start_server.bat    # Windows server host manager
│   │   ├── start_server.sh     # Linux/macOS local server host manager
│   │   ├── scripts/            # Dedicated networking & DNS automation scripts
│   │   │   ├── setup_cloudflare_tunnel.sh / .bat / .ps1
│   │   │   └── update_duckdns.sh / .bat / .ps1
│   │   └── systemd/            # 24/7 background systemd units & installer
│   └── client/                 # Player & Client Distribution Package
│       ├── README.md           # Player setup & connection guide
│       ├── __main__.py         # Direct execution entrypoint
│       ├── config.json         # Symlink to config/client/config.json
│       ├── install_client.bat  # Windows 1-click installer
│       ├── install_client.sh   # Linux / macOS 1-click installer
│       ├── launch_client.bat   # Windows launcher for Player GUI
│       ├── launch_client.sh    # Linux / macOS launcher for Player GUI
│       └── src/                # Client source engine
│           ├── sync_client.py  # EDOPro card & script synchronizer
│           └── client_app.py   # Player Desktop GUI Control Panel
├── dist/                       # Output directory for generated release archives
│   ├── ygo-client-package.zip  # Ready-to-distribute player package
│   ├── ygo-server-package.tar.gz # Ready-to-deploy server package
│   └── SHA256SUMS.txt          # Verification checksums
└── production/                 # Active runtime services & card database
```

---

## 🚀 Building Release Packages (`./manage.sh package`)

The master controller can automatically bundle both packages into standalone, distributable release archives:

```bash
./manage.sh package
```

### Build Process

1. **Compilation Sync:** Re-compiles the SQLite card database (`custom_cards.cdb`) and regenerates all Lua effect scripts (`scripts/c<id>.lua`).
2. **Deck Export:** Exports all character decks into standard `.ydk` format.
3. **Player Client Package (`dist/ygo-client-package.zip`):**
   - Bundles all client installers and launchers (`install_client.*`, `launch_client.*`).
   - Bundles the client source engine (`src/sync_client.py` and `src/client_app.py`).
   - Bundles the latest compiled `expansions/custom_cards.cdb` and all `expansions/scripts/*.lua`.
   - Bundles all pre-made character decks in `decks/*.ydk`.
   - Bundles the live connection manifest `config.json` and player `README.md`.
4. **Host Server Package (`dist/ygo-server-package.tar.gz`):**
   - Bundles `deploy_oracle_cloud.sh`, `start_server.*`, and the `scripts/` directory (`setup_cloudflare_tunnel.*`, `update_duckdns.*`).
   - Bundles the Docker Compose stack `docker-compose.yml` (dereferenced).
   - Bundles all systemd service unit files and `install_services.sh`.

---

## 🎮 Player Distribution Workflow

When onboarding new players or sharing custom card expansions with friends:

1. **Option A: Distribute Zip Package (Recommended for Offline / New Players)**
   - Send `dist/ygo-client-package.zip`.
   - Player unzips the folder.
   - On Windows: Player double-clicks `install_client.bat`.
   - On Linux / Mac: Player runs `./install_client.sh`.
   - The installer automatically locates the player's EDOPro directory and copies all custom cards, scripts, and decks.

2. **Option B: Remote Live Sync (Over HTTPS)**
   - Players can update existing installations anytime without re-downloading a zip:

     ```bash
     python3 sync_client.py --server https://thelandofkustomazi.com
     ```

   - The script pulls the live manifest from `/api/shared/manifest`, downloads the latest `.cdb`, unpacks the latest Lua scripts zip, and fetches all active story decks.

---

## 🖥️ Server Administrator Workflow

When provisioning a new host or migrating servers:

1. **Option A: From Git Repository**

   ```bash
   git clone https://github.com/Novaking34/yugioh-server-and-bot-application.git yugioh-server
   cd yugioh-server/packages/server
   sudo ./deploy_oracle_cloud.sh
   ```

2. **Option B: From Tarball Package**

   ```bash
   tar -zxvf ygo-server-package.tar.gz
   cd ygo-server-package
   sudo ./deploy_oracle_cloud.sh
   ```

---

## 🐍 Python Package Installation (`pip`)

The repository includes both modern `pyproject.toml` (PEP 517/518/621) and standard `setup.py`:

```bash
# Editable install for development:
pip install -e .

# Install with development test dependencies:
pip install -e ".[dev]"

# CLI entry point:
ygo-manage status
ygo-manage package
```
