# 🌌 Yu-Gi-Oh! Custom Card, Story & Simulator Platform

A unified environment for designing, cataloging, storybuilding, and dueling with custom Yu-Gi-Oh! cards hosted on **Duelingbook**, synchronized with a **modular Discord story & duel bot** and a **live automated duel simulator**.

---

## ⚡ Master CLI Controller (`./manage.sh`)

Use the master CLI script to manage all platform services, run tests, and synchronize expansions:

```bash
cd /home/professorseanex/yugioh-server

# View live status of containers, card count, and expansions
./manage.sh status

# Launch the Desktop GUI Application (or double-click the Desktop icon)
./manage.sh app

# Start / stop / restart the live duel simulator (port 7911 / 7922)
./manage.sh start
./manage.sh stop
./manage.sh restart

# Launch the Web Catalog Dashboard (runs at http://localhost:8000)
./manage.sh web

# Launch the modular Discord Story & Duel Bot
./manage.sh bot

# Run the Pytest unit test suite
./manage.sh test

# Validate syntax of all generated Lua card scripts using luac
./manage.sh validate-lua

# Re-synchronize cards from Story DB to simulator CDB & Lua scripts
./manage.sh sync

# Import custom cards from a Duelingbook JSON export
./manage.sh import /path/to/duelingbook_cards.json

# Build standalone distribution packages in dist/ (.zip for client, .tar.gz for server)
./manage.sh package

# Launch Cloudflare HTTPS Tunnel for Web Catalog
./manage.sh tunnel

# Export character story decks or player custom decks to .ydk format
./manage.sh export-decks
./manage.sh export-player <discord_user_id>
```

---

## 🏗️ Platform Architecture & Data Pipeline

```bash
                     ┌─────────────────────────────┐
                     │   Duelingbook Card Design   │
                     │  (Artwork, Stats & Text)    │
                     └──────────────┬──────────────┘
                                    │  Export JSON
                                    ▼
                     ┌─────────────────────────────┐
                     │ tools/duelingbook_importer  │
                     └──────────────┬──────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│ story_database/ygo_story.db   │             │   Live Simulator Expansions   │
│ - custom_cards & cards_fts    │             │ - custom_cards.cdb (SQLite)   │
│ - factions & characters       │             │ - scripts/c<id>.lua (ocgcore) │
│ - decks & player_decks        │             └───────────────┬───────────────┘
└────────┬──────────────┬───────┘                             │
         │              │                                     │
         ▼              ▼                                     ▼
┌────────────────┐ ┌────────────────┐             ┌───────────────────────────┐
│ Web Dashboard  │ │  Discord Bot   │             │ ocgcore Simulator Engine  │
│ localhost:8000 │ │  Slash Commands│             │ TCP: 7911 | Web: 7922     │
└────────────────┘ └────────────────┘             └───────────────────────────┘
```

---

## 🎮 1. Live Duel Simulator (YGOPro / EDOPro / Omega)

The server runs an automated rule-enforcement duel engine container (`ocgcore`) exposing:

- **Game Client TCP Port:** `localhost:7911` (or your LAN IP: `192.168.1.107:7911`)
- **Web Room Manager:** `http://localhost:7922`

### Connecting from EDOPro / YGOPro

1. Open your EDOPro / YGOPro client.
2. Go to **Multiplayer / Duel Online**.
3. Select **Direct Connect / IP Connection**:
   - **Host:** `localhost` (or your local IP / VPN IP for friends)
   - **Port:** `7911`
4. Enter any room name or leave blank for auto-matching.

### Sharing Custom Card Expansions (For Players & Friends)

All files needed for other players to duel on this server are organized in the [`packages/client/`](file:///home/professorseanex/yugioh-server/packages/client/) installation package:

- **Windows:** Double-click `packages/client/install_client.bat`
- **Linux / macOS:** Run `./packages/client/install_client.sh`
- **Player GUI:** Run `launch_client.bat` or `./launch_client.sh`

To generate standalone distributable zip and tarball archives for players and servers:

```bash
./manage.sh package
```

Distributable archives are output to `dist/`:

- `dist/ygo-client-package.zip`: Standalone zip archive for players (includes custom cards, scripts, decks, and installers).
- `dist/ygo-server-package.tar.gz`: Standalone tarball for server hosts (includes Docker manifests, systemd services, and cloud scripts).

See [`packages/README.md`](file:///home/professorseanex/yugioh-server/packages/README.md) and [`development/docs/PACKAGING_AND_DISTRIBUTION.md`](file:///home/professorseanex/yugioh-server/development/docs/PACKAGING_AND_DISTRIBUTION.md) for full instructions.

---

## 🌐 2. Duelingbook Integration & Card Pipeline

Duelingbook is the primary design workshop for card artwork, text, and manual testing.

### Workflow

1. **Design on Duelingbook:** Create your custom card with artwork, stats, and effects.
2. **Export or Save JSON:** Export card details from Duelingbook.
3. **Import:**

   ```bash
   ./manage.sh import cards.json
   ```

4. **Automatic Synchronization:**
   - The card is registered in `production/main/web/ygo_story.db` with its Duelingbook URL and artwork thumbnail.
   - The simulator `.cdb` binary database is compiled into `production/shared/expansions/custom_cards.cdb`.
   - A full Lua effect script (`c<id>.lua`) is generated in `production/shared/expansions/scripts/`.
   - The card is immediately searchable in the Discord bot and Web Dashboard!

---

## 🤖 3. Modular Discord Story & Duel Bot

The Discord bot is organized modularly using discord.py Cogs:

| Cog Module | Commands | Description |
| --- | --- | --- |
| `cogs.cardpool` | `/card <name>`, `/recent_cards` | Rich card embeds with frame colors, Duelingbook artwork, and full-text search autocomplete |
| `cogs.deckbuilding` | `/deck_add`, `/deck_remove`, `/mydeck`, `/load_character_deck` | Personal deckbuilder using custom cards with character deck importing |
| `cogs.duel_engine` | `/duel @user` | Interactive in-chat duel with private hand inspection, LP tracking, dice rolling, and turn passing |
| `cogs.lore` | `/lore <query>`, `/deck <name>`, `/stats` | Lore sagas, faction playstyle breakdowns, duelist dossiers, and database statistics |

### Setting up the Discord Bot Token

1. Create a Discord application at the [Discord Developer Portal](https://discord.com/developers/applications).
2. Enable **Privileged Gateway Intents** (Message Content Intent).
3. Copy your Bot Token and set it in `/home/professorseanex/yugioh-server/.env`:

   ```bash
   DISCORD_BOT_TOKEN="your_token_here"
   ```

4. Launch the bot:

   ```bash
   ./manage.sh bot
   ```

---

## 🖥️ 4. Web Catalog Dashboard

A responsive web dashboard runs locally at:
👉 **`http://localhost:8000`**

- Real-time card search by name, effect keywords, or lore backstory.
- Filter by Card Type (Monster, Spell, Trap).
- Direct links to Duelingbook card views.
- REST API available at:
  - `GET /api/cards`: Search and filter custom cards
  - `GET /api/cards/{id}`: Detailed card statistics
  - `POST /api/cards`: Register new custom card
  - `GET /api/lore`: Narrative sagas, factions, and duel records
  - `GET /api/decks`: Character deck profiles

---

## 🗂️ 5. Project Directory Structure

```text
/home/professorseanex/yugioh-server/
├── .env                               # Environment secrets & credentials (local/ignored)
├── .gitignore                         # Git exclusion rules for artifacts & secrets
├── README.md                          # Master platform documentation & guide
├── requirements.txt                   # Platform Python dependencies
├── manage.sh                          # Master CLI controller & automated installer (Linux/macOS)
├── manage.bat                         # Master CLI controller wrapper (Windows)
├── manage.py                          # Master Python controller & orchestration engine
├── pyproject.toml                     # Modern PEP 517/518 Python packaging metadata
├── setup.py                           # Setuptools installation script (pip install -e .)
├── docker-compose.yml                 # Live Duel Simulator Container (Port 7911 / 7922)
├── config/
│   └── paths.py                       # Centralized Path Resolution Module
├── packages/                          # Standalone Installation Packages
│   ├── README.md                      # Packages Overview & Distribution Guide
│   ├── server/                        # Server & Host 24/7 Installation Package
│   │   ├── README.md                  # Server deployment & operations guide
│   │   ├── deploy_oracle_cloud.sh     # Turnkey installer for Oracle Cloud / Ubuntu VM
│   │   ├── setup_cloudflare_tunnel.sh # Cloudflare Tunnel installer
│   │   ├── update_duckdns.sh          # DuckDNS dynamic DNS updater
│   │   ├── thelandofkustomazi.com.zone # BIND DNS zone file
│   │   ├── docker-compose.yml         # Container orchestration manifest
│   │   └── systemd/                   # 24/7 background systemd units & installer
│   └── client/                        # Player & Client Distribution Package
│       ├── README.md                  # Player setup & connection guide
│       ├── install_client.bat         # Windows 1-click installer
│       ├── install_client.sh          # Linux / macOS 1-click installer
│       ├── launch_client.bat          # Windows launcher for Player GUI
│       ├── launch_client.sh           # Linux / macOS launcher for Player GUI
│       ├── sync_client.py             # EDOPro card & script synchronizer
│       ├── client_app.py              # Player Desktop GUI Control Panel
│       └── config.json                # Live server connection manifest
├── dist/                              # Standalone release packages (built via ./manage.sh package)
│   ├── ygo-client-package.zip         # Pre-packaged distribution for players (.zip)
│   └── ygo-server-package.tar.gz      # Pre-packaged deployment for servers (.tar.gz)
├── production/
│   ├── main/                          # Host Server Services (app.py, discord_bot/, simulator/, web/)
│   └── shared/                        # Client / Player Distribution (expansions/, decks/)
├── development/                       # Development Tools, Tests & Pipeline
│   ├── database/                      # Schema & Seeding Tools
│   ├── docs/                          # Architecture & Developer Documentation
│   ├── tests/                         # Pytest Unit Test Suite
│   └── tools/                         # Card Generation & Sync Tools
└── venv/                              # Isolated Python 3 Virtual Environment
```

---

## 🧪 6. Testing & Quality Assurance

Run the test suite at any time:

```bash
./manage.sh test
```

Validate all generated Lua effect scripts:

```bash
./manage.sh validate-lua
```
