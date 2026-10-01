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

### Sharing Custom Card Expansions

- Custom cards are automatically compiled into:
  `server-data/expansions/custom_cards.cdb`
- Custom Lua effect scripts reside in:
  `server-data/expansions/scripts/c<id>.lua`
- To share custom cards with other players, simply copy `custom_cards.cdb` and the `scripts/` folder to their client's `expansions/` directory!

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
   - The card is registered in `story_database/ygo_story.db` with its Duelingbook URL and artwork thumbnail.
   - The simulator `.cdb` binary database is compiled.
   - A full Lua effect script (`c<id>.lua`) is generated in `server-data/expansions/scripts/`.
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

```bash
/home/professorseanex/yugioh-server/
├── README.md                          # Platform Documentation & Guide
├── manage.sh                          # Master CLI Controller
├── docker-compose.yml                 # Live Duel Simulator Container
├── server-data/                       # Live Duel Simulator State
│   ├── config/                        # Simulator port & rules configuration
│   ├── expansions/                    # Custom cards & Lua effect scripts
│   │   ├── custom_cards.cdb           # Compiled SQLite simulator database
│   │   └── scripts/                   # Lua effect scripts (c<id>.lua)
│   ├── decks/                         # Exported character .ydk decks
│   └── replays/                       # Saved duel replays (.yrp)
├── story_database/
│   ├── schema.sql                     # Full relational schema + FTS5 index
│   ├── ygo_story.db                   # Main SQLite database
│   ├── database.py                    # Database connection helpers & session manager
│   ├── models.py                      # Pydantic v2 schemas for API validation
│   ├── seed_story_data.py             # Sample story, lore, & card seeder
│   ├── api_server.py                  # FastAPI REST API
│   └── templates/
│       └── index.html                 # Web dashboard frontend template
├── tools/
│   ├── constants.py                   # Centralized YGOPro bitmasks & mappings
│   ├── cdb_builder.py                 # YGOPro/EDOPro .cdb SQLite compiler
│   ├── lua_generator.py               # Modular ocgcore Lua effect generator
│   ├── duelingbook_importer.py        # Duelingbook card parser & pipeline sync
│   └── export_deck.py                 # Standard .ydk deck exporter
├── discord_bot/
│   ├── bot.py                         # Modular Discord bot runner
│   ├── config.py                      # Bot configuration & credential resolution
│   ├── utils.py                       # Card frame color palettes & embed builders
│   └── cogs/
│       ├── cardpool.py                # Card search & autocomplete
│       ├── deckbuilding.py            # Personal player deckbuilder
│       ├── duel_engine.py             # Interactive duel state machine & buttons
│       └── lore.py                    # Sagas, factions, dossiers & stats
├── tests/                             # Comprehensive Unit Test Suite
│   ├── test_constants.py              # Bitmask and flag tests
│   ├── test_cdb_builder.py            # CDB parsing and binary encoding tests
│   ├── test_lua_generator.py          # Procedure and effect parsing tests
│   ├── test_duelingbook_importer.py   # Passcode and Duelingbook mapping tests
│   └── test_api_server.py             # FastAPI REST endpoint tests
└── venv/                              # Isolated Python 3 virtual environment
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
