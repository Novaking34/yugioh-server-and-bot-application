# 🎮 Yu-Gi-Oh! Player Client Distribution Package (`packages/client/`)

This package provides players and duelists with automated tools to install and synchronize custom cards, Lua effect scripts, and character/story decklists with their local **EDOPro / Project Ignis** or **YGOPro** game client, and connect to the live 24/7 duel server.

---

## 📁 Package Layout & Manifest

```bash
packages/client/
├── README.md              # Player setup guide & troubleshooting (this file)
├── config.json            # Standalone client connection manifest (live duel endpoints)
├── install_client.sh      # Linux / macOS 1-click terminal installer
├── install_client.bat     # Windows 1-click double-click installer
├── launch_client.sh       # Linux / macOS 1-click GUI launcher
├── launch_client.bat      # Windows 1-click GUI launcher
├── __main__.py            # Direct Python execution entrypoint (`python -m packages.client`)
└── src/                   # Core Python application source code
    ├── __init__.py        # Module initialization & public API exports
    ├── client_config.py   # Strongly-typed configuration dataclass & resolution engine
    ├── sync_client.py     # Synchronizer engine, path detector & remote updater
    ├── client_app.py      # Player Expansion Manager desktop GUI application
    └── README.md          # Internal architecture & developer documentation
```

---

## ⚡ 1. One-Click Installation

### Windows

1. Double-click **`install_client.bat`**.
2. The installer will auto-detect your EDOPro installation (e.g., `C:\Project Ignis\EDOPro`) and copy:
   - Compiled card database: `custom_cards.cdb` ➔ `EDOPro/expansions/`
   - Lua effect scripts: `c<id>.lua` ➔ `EDOPro/expansions/scripts/`
   - Pre-made story decks: `*.ydk` ➔ `EDOPro/deck/`
3. Double-click **`launch_client.bat`** to open the Player Expansion Manager GUI.

### Linux / macOS / Steam Deck

```bash
cd packages/client

# Make scripts executable (if needed)
chmod +x install_client.sh launch_client.sh

# Run 1-click installer
./install_client.sh

# Launch desktop GUI control panel
./launch_client.sh
```

If your EDOPro folder is in a custom or non-standard path, specify it directly:

```bash
./install_client.sh --path /custom/path/to/EDOPro
```

---

## 🔄 2. Synchronizing Cards Over the Internet (HTTPS)

You can update your card pool over HTTPS at any time without re-downloading a new release archive:

```bash
# Sync from official custom domain:
python3 src/sync_client.py --server https://thelandofkustomazi.com

# Or sync from DuckDNS dynamic DNS fallback:
python3 src/sync_client.py --server http://thelandofkustomazi.duckdns.org:8000
```

---

## ⚔️ 3. Connecting to the Live Server

1. Open your **EDOPro** or **YGOPro** game client.
2. Select **Multiplayer -> Duel Online**.
3. Choose **Direct Connect** (or IP connection) and enter:
   - **Primary Host:** `thelandofkustomazi.com`
   - **Duel Port:** `7911`
   - **Fallback Host:** `thelandofkustomazi.duckdns.org`
4. Enter any room name to host a new duel, or leave the room name blank to auto-join an available match.

---

## ⚙️ Configuration Architecture

All endpoints and ports used by this package are resolved from [`config.json`](file:///home/professorseanex/yugioh-server/packages/client/config.json) via [`packages.client.src.client_config`](file:///home/professorseanex/yugioh-server/packages/client/src/client_config.py).

The manifest is an authoritative standalone file bundled directly into release archives, eliminating fragile OS symlinks. Server deployment tools (`./manage.sh package` and `./manage.sh sync`) automatically verify and synchronize `packages/client/config.json` directly from `.env` / `config.settings`, ensuring 100% parity with zero drift.
