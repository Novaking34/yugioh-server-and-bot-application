# 🌌 Yu-Gi-Oh! Custom Card, Story & Simulator Platform

A unified systems engineering repository hosting **3 distinct applications in 1 server codebase**, built around custom Yu-Gi-Oh! card design, automated compilation pipelines, and bi-directional real-time gameplay.

---

## 🏛️ The Three Unified Applications

The platform hosts three autonomous domain applications that interoperate through a shared functional core, SQLite authoritative storage, and binary compiled derivatives:

1. **🎮 Live Duel Simulator (`ocgcore`)**:
   - Automated rule-enforcement simulation engine running in a Docker container.
   - Exposes raw TCP game client connectivity on port `7911` (EDOPro, YGOPro, Omega).
   - Exposes HTTP room management interface on port `7922`.
2. **🖥️ Web Catalog Dashboard & REST API (`FastAPI`)**:
   - High-speed ASGI web service running on `http://localhost:8000`.
   - Full-text search over card text, stats, lore backstories, and archetypes.
   - REST API endpoints for card registration, deck querying, and duelist statistics.
3. **🤖 Modular Discord Story & Duel Bot (`discord.py`)**:
   - Interactive Discord bot powered by modular Cogs (`cardpool`, `deckbuilding`, `duel_engine`, `lore`).
   - In-chat duel engine with private hand inspection, LP state machine, and dice rolls.
   - Story mode sagas, character deck loaders, and real-time autocomplete search.

*Also includes:*

- **Platform Manager Desktop Application**: Native Python GUI control panel ([`production/main/app.py`](file:///home/professorseanex/yugioh-server/production/main/app.py)).
- **Player Client Distribution Package**: 1-click player installation suite ([`packages/client/`](file:///home/professorseanex/yugioh-server/packages/client/)).

---

## 📚 Architectural Doctrine & Engineering Documentation

The repository follows a **Systems Engineering & Data-Oriented Design (DOD)** paradigm based on the **"Functional Core, Imperative Shell"** pattern and **Autonomous Domain Silos**.

Comprehensive architecture, roadmap, and state documentation is housed in the [`docs/`](file:///home/professorseanex/yugioh-server/docs/) directory:

- 📖 [**`docs/README.md`**](file:///home/professorseanex/yugioh-server/docs/README.md): Architecture Suite Overview & Index.
- 🏛️ [**`docs/ARCHITECTURE_PHILOSOPHY.md`**](file:///home/professorseanex/yugioh-server/docs/ARCHITECTURE_PHILOSOPHY.md): Engineering doctrine, Functional Core / Imperative Shell, C-style 4-block compilation units, autonomous domain silos, and the bi-directional closed loop.
- 💾 [**`docs/DATA_ARCHITECTURE.md`**](file:///home/professorseanex/yugioh-server/docs/DATA_ARCHITECTURE.md): Authoritative 6-tier storage hierarchy, DDL schemas, and ingestion pipelines.
- ⚙️ [**`docs/CONFIGURATION_SYSTEM.md`**](file:///home/professorseanex/yugioh-server/docs/CONFIGURATION_SYSTEM.md): 5-tier configuration precedence, dataclass schemas, logging sinks, and telemetry.
- 📋 [**`docs/ACTION_PLAN.md`**](file:///home/professorseanex/yugioh-server/docs/ACTION_PLAN.md): 6-phase master execution roadmap from root consolidation to automated deployment.
- 📊 [**`docs/REPOSITORY_STATE_TRACKER.md`**](file:///home/professorseanex/yugioh-server/docs/REPOSITORY_STATE_TRACKER.md): Live audit matrix, file verification ledger, and health status.

---

## ⚡ Master CLI Controller (`./manage.sh`)

All platform operations, service lifecycles, compilers, and test suites are managed via the Master CLI Controller ([`manage.sh`](file:///home/professorseanex/yugioh-server/manage.sh) / [`manage.py`](file:///home/professorseanex/yugioh-server/manage.py)):

```bash
cd /home/professorseanex/yugioh-server

# View live status of containers, databases, ports, and expansions
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

# Synchronize code, database, and bot services to Oracle Cloud VM
./manage.sh sync-vm "Deployment message"

# Run platform diagnostics and failpoint auditor
./manage.sh diagnose

# Inspect multi-target platform logs (stats, tail, query)
./manage.sh logs stats

# Manage master card tracker & Google Sheets synchronization
./manage.sh tracker verify

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

```text
                     ┌─────────────────────────────┐
                     │   Duelingbook Card Design   │
                     │  (Artwork, Stats & Text)    │
                     └──────────────┬──────────────┘
                                    │  Export JSON / Sheet CSV
                                    ▼
                     ┌─────────────────────────────┐
                     │ tools/duelingbook_importer  │
                     │ tools/tracker_sync          │
                     └──────────────┬──────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│ data/authoritative/ygo_story  │             │   data/expansions/ (Custom)   │
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
   - **Host:** `localhost` (or server IP: `147.224.147.30`)
   - **Port:** `7911`
4. Enter any room name or leave blank for auto-matching.

### Sharing Custom Card Expansions (For Players & Friends)

All files needed for other players to duel on this server are organized in the [`packages/client/`](file:///home/professorseanex/yugioh-server/packages/client/) installation package:

- **Windows:** Double-click [`packages/client/install_client.bat`](file:///home/professorseanex/yugioh-server/packages/client/install_client.bat)
- **Linux / macOS:** Run [`./packages/client/install_client.sh`](file:///home/professorseanex/yugioh-server/packages/client/install_client.sh)
- **Player GUI:** Run [`launch_client.bat`](file:///home/professorseanex/yugioh-server/packages/client/launch_client.bat) or [`./launch_client.sh`](file:///home/professorseanex/yugioh-server/packages/client/launch_client.sh)

To generate standalone distributable zip and tarball archives for players and servers:

```bash
./manage.sh package
```

Distributable archives are output to [`dist/`](file:///home/professorseanex/yugioh-server/dist/):

- `dist/ygo-client-package.zip`: Standalone zip archive for players (includes custom cards, scripts, decks, and installers).
- `dist/ygo-server-package.tar.gz`: Standalone tarball for server hosts (includes Docker manifests, systemd services, and cloud scripts).

See [`packages/README.md`](file:///home/professorseanex/yugioh-server/packages/README.md) and [`development/docs/PACKAGING_AND_DISTRIBUTION.md`](file:///home/professorseanex/yugioh-server/development/docs/PACKAGING_AND_DISTRIBUTION.md) for full instructions.

---

## 🌐 2. Duelingbook Integration & Card Pipeline

Duelingbook is the primary design workshop for card artwork, text, and manual testing.

### Workflow

1. **Design on Duelingbook:** Create your custom card with artwork, stats, and effects.
2. **Export or Save JSON / CSV:** Export card details from Duelingbook or master Google Sheet tracker.
3. **Import:**

   ```bash
   ./manage.sh import cards.json
   # or synchronize from master Google Sheets tracker:
   ./manage.sh tracker import
   ```

4. **Automatic Synchronization:**
   - The card is registered in [`data/authoritative/content.db`](file:///home/professorseanex/yugioh-server/data/authoritative/content.db) with its Duelingbook URL and artwork thumbnail.
   - The simulator `.cdb` binary database is compiled into [`data/expansions/custom_cards.cdb`](file:///home/professorseanex/yugioh-server/data/expansions/custom_cards.cdb).
   - A full Lua effect script (`c<id>.lua`) is generated in [`data/expansions/scripts/`](file:///home/professorseanex/yugioh-server/data/expansions/scripts/).
   - High-resolution artwork is cached in [`data/expansions/pics/`](file:///home/professorseanex/yugioh-server/data/expansions/pics/).
   - The card is immediately searchable in the Discord bot and Web Dashboard!

---

## 🤖 3. Modular Discord Story & Duel Bot

The Discord bot is organized modularly using discord.py Cogs located in [`production/main/discord_bot/cogs/`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/cogs/):

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

Every root code file adheres to the strict **C-Style 4-Block Compilation Unit Structure** (`BLOCK 1: METADATA`, `BLOCK 2: OPENING`, `BLOCK 3: BODY`, `BLOCK 4: CLOSING`).

```text
/home/professorseanex/yugioh-server/
├── .env                               # [4-Block] Environment secrets & credentials (local/ignored)
├── .env.example                       # [4-Block] Documented environment secrets template
├── .gitignore                         # [4-Block] Git exclusion rules for artifacts & secrets
├── README.md                          # Master platform documentation & topology guide
├── requirements.txt                   # [4-Block] Platform Python runtime & test dependencies
├── pyproject.toml                     # [4-Block] Modern PEP 517/518 build metadata & pytest config
├── setup.py                           # [4-Block] Setuptools build & installation specification
├── manage.sh                          # [4-Block] Master CLI host bootstrap & virtualenv manager (Linux/macOS)
├── manage.bat                         # [4-Block] Master CLI wrapper (Windows)
├── manage.py                          # [4-Block] Master Python controller & orchestration engine
├── docker-compose.yml                 # [4-Block] Live Duel Simulator container manifest (Port 7911 / 7922)
├── config/                            # Global Configuration & Shared Primitives
│   ├── __init__.py                    # [4-Block] Master export hub for settings, paths, rules, logging & debugger
│   ├── paths.py                       # [4-Block] Centralized canonical directory & file paths
│   ├── settings.py                    # [4-Block] Strongly-typed dataclass settings (10 domains)
│   ├── game_rules.py                  # [4-Block] Authoritative Master Rule 5 bitmasks & rules
│   ├── bot/                           # Discord bot example configurations
│   ├── client/                        # Canonical client configuration manifest
│   ├── debugger/                      # Centralized execution tracing & 14-table diagnostic auditor
│   ├── dns/                           # BIND DNS zone configurations
│   └── logging/                       # Structured JSON & console logging subsystem
├── data/                              # Unified Platform Data & Assets Subsystem
│   ├── authoritative/                 # Canonical SQLite database (content.db) & schema_content.sql
│   ├── trackers/                      # Master CSV/TSV Google Sheets card trackers
│   ├── artwork/                       # Raw high-resolution card artwork (raw/)
│   ├── expansions/                    # Compiled custom_cards.cdb, Lua scripts, & artwork pics/
│   ├── decks/                         # Pre-made character story decks (.ydk)
│   └── simulator/                     # Simulator JSON configs (config/) & replay telemetry (replays/)
├── docs/                              # Master Architectural & Engineering Suite
│   ├── README.md                      # Documentation index & guide
│   ├── ARCHITECTURE_PHILOSOPHY.md     # Systems engineering doctrine (Functional Core, Silos)
│   ├── DATA_ARCHITECTURE.md           # Authoritative 6-tier storage hierarchy & schemas
│   ├── CONFIGURATION_SYSTEM.md        # 5-tier configuration precedence & telemetry
│   ├── ACTION_PLAN.md                 # 6-phase implementation roadmap
│   └── REPOSITORY_STATE_TRACKER.md    # Live audit matrix & component state tracker
├── logs/                              # Operational service logs (bot, web, simulator, audits)
├── packages/                          # Standalone Distribution & Deployment Packages
│   ├── README.md                      # Packages Overview & Distribution Guide
│   ├── server/                        # Server & Host 24/7 Installation Package
│   │   ├── README.md                  # Server deployment & operations guide
│   │   ├── deploy_oracle_cloud.sh     # Turnkey installer for Oracle Cloud / Ubuntu VM
│   │   ├── setup_cloudflare_tunnel.sh # Cloudflare Tunnel installer
│   │   ├── update_duckdns.sh          # DuckDNS dynamic DNS updater
│   │   ├── thelandofkustomazi.com.zone # BIND DNS zone file
│   │   ├── docker-compose.yml         # Container orchestration manifest
│   │   ├── scripts/                   # Operator automation (sync_oracle_vm.sh)
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
│   ├── ygo-server-package.tar.gz      # Pre-packaged deployment for servers (.tar.gz)
│   └── SHA256SUMS.txt                 # Checksums for release verification
├── production/
│   ├── main/                          # Host Server Services
│   │   ├── app.py                     # Native desktop GUI platform manager
│   │   ├── discord_bot/               # Modular Discord bot (bot.py, cogs/, services/)
│   │   ├── gui/                       # Encapsulated Desktop GUI and setup wizards
│   │   └── web/                       # FastAPI dashboard & expansion sync API
│   └── shared/                        # Client distribution symlinks
├── development/                       # Development Tools, Compilers & Tests
│   ├── docs/                          # Specialized developer documentation
│   ├── tests/                         # Pytest comprehensive unit test suite (112 tests)
│   └── tools/                         # CDB compiler, Lua generator, importer, diagnostics
└── venv/                              # Isolated Python 3 virtual environment
```

---

## 🧪 6. Testing & Quality Assurance

Run the comprehensive unit test suite:

```bash
./manage.sh test
```

Validate all generated Lua effect scripts:

```bash
./manage.sh validate-lua
```

Run platform diagnostics and failpoint auditor:

```bash
./manage.sh diagnose
```
