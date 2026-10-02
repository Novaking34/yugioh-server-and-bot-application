# 💻 Client Source Architecture (`packages/client/src/`)

This directory contains the Python modules that power the client-side tooling for players.

---

## 📁 File Manifest

| File | Purpose |
| --- | --- |
| [`__init__.py`](file:///home/professorseanex/yugioh-server/packages/client/src/__init__.py) | Package initialization and public API exports |
| [`sync_client.py`](file:///home/professorseanex/yugioh-server/packages/client/src/sync_client.py) | CLI synchronizer engine, directory detector & remote updater |
| [`client_app.py`](file:///home/professorseanex/yugioh-server/packages/client/src/client_app.py) | Player Expansion Manager desktop GUI application |

---

## ⚙️ Module Responsibilities

### 1. `sync_client.py` — Synchronization Engine

- **Directory Detection**: Implements `find_game_directory()` to scan standard filesystem locations across Windows, Linux, macOS, Wine, Flatpak, and Steam Deck.
- **Config Manifest Resolution**: Implements `resolve_config_manifest()` to load connection parameters and server URLs from `config.json` without hardcoding hostnames.
- **Offline Bundle Install**: Implements `install_to_client()` to copy `custom_cards.cdb`, `scripts/*.lua`, and `decks/*.ydk` directly into the detected game folder.
- **Online HTTPS Sync**: Implements `sync_from_remote()` to query `/api/shared/manifest`, download the latest CDB, unzip Lua scripts, and pull decklists.

### 2. `client_app.py` — Desktop GUI

- **Visual Presentation**: Dark-mode Tkinter GUI with custom ttk styling.
- **Threaded Execution**: Non-blocking network sync and file copying using daemon worker threads to keep the UI fluid.
- **Quick-Start Wizard**: 3-step dialog (`PlayerSetupWizardDialog`) guiding players through game directory selection, installation, and multiplayer connection.
