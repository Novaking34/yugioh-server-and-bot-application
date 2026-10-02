# 🎮 Yu-Gi-Oh! Player & Client Distribution Package

This package allows players to synchronize custom cards, Lua effect scripts, and character decklists directly with their local **EDOPro / Project Ignis** or **YGOPro** game client, and connect to the live 24/7 duel server.

---

## 📦 Package Contents

| File | Description |
| --- | --- |
| [`install_client.bat`](file:///home/professorseanex/yugioh-server/packages/client/install_client.bat) | Windows 1-click installer: installs CDB, scripts, and decks into EDOPro |
| [`install_client.sh`](file:///home/professorseanex/yugioh-server/packages/client/install_client.sh) | Linux / macOS 1-click installer |
| [`launch_client.bat`](file:///home/professorseanex/yugioh-server/packages/client/launch_client.bat) | Windows launcher for the Player Control Panel GUI |
| [`launch_client.sh`](file:///home/professorseanex/yugioh-server/packages/client/launch_client.sh) | Linux / macOS launcher for the Player Control Panel GUI |
| [`sync_client.py`](file:///home/professorseanex/yugioh-server/packages/client/sync_client.py) | Python cross-platform card synchronizer (supports local and remote HTTPS sync) |
| [`client_app.py`](file:///home/professorseanex/yugioh-server/packages/client/client_app.py) | Player Desktop GUI Manager with 1-click update, deck installer & direct connect |
| [`config.json`](file:///home/professorseanex/yugioh-server/packages/client/config.json) | Connection manifest containing official server host and port settings |

---

## ⚡ 1. One-Click Installation

### Windows

1. Double-click **`install_client.bat`**.
2. The installer will auto-detect your EDOPro installation (e.g., `C:\Project Ignis\EDOPro`) and copy:
   - Compiled card database: `custom_cards.cdb` -> `EDOPro/expansions/`
   - Lua effect scripts: `c<id>.lua` -> `EDOPro/expansions/scripts/`
   - Pre-made story decks: `*.ydk` -> `EDOPro/deck/`
3. Double-click **`launch_client.bat`** to open the Player Control Panel GUI.

### Linux / macOS

```bash
cd packages/client
./install_client.sh
./launch_client.sh
```

If your EDOPro folder is in a custom path, specify it directly:

```bash
./install_client.sh --path /custom/path/to/EDOPro
```

---

## 🔄 2. Synchronizing Cards from Remote Server

You can update your card pool over the internet without downloading a new zip package:

```bash
# Sync from official custom domain:
python3 sync_client.py --server https://thelandofkustomazi.com

# Or sync from DuckDNS fallback:
python3 sync_client.py --server http://thelandofkustomazi.duckdns.org:8000
```

---

## ⚔️ 3. Connecting to the Live Server

1. Open your **EDOPro** or **YGOPro** client.
2. Select **Multiplayer / Duel Online**.
3. Choose **Direct Connect** (or IP connection) and enter:
   - **Host:** `thelandofkustomazi.com` (or `play.thelandofkustomazi.com` / `thelandofkustomazi.duckdns.org`)
   - **Port:** `7911`
4. Enter any room name to host a room, or leave blank to auto-join an available duel.
