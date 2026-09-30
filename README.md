# 🌌 Yu-Gi-Oh Custom Card, Story & Simulator Platform

A unified environment for designing, cataloging, storybuilding, and dueling with custom Yu-Gi-Oh cards hosted on **Duelingbook**, synchronized with a **Discord story bot** and a **live automated duel simulator**.

---

## ⚡ Quick Start (`./manage.sh`)

Use the master CLI script to control all platform services:

```bash
cd /home/professorseanex/yugioh-server

# View live status of containers, card count, and expansions
./manage.sh status

# Start / stop the live duel simulator (port 7911 / 7922)
./manage.sh start
./manage.sh stop

# Start the Web Catalog Dashboard (runs at http://localhost:8000)
./manage.sh web

# Start the Discord Bot
./manage.sh bot

# Re-synchronize cards from Story DB to simulator CDB & Lua scripts
./manage.sh sync

# Import custom cards from a Duelingbook JSON export
./manage.sh import /path/to/duelingbook_cards.json

# Export character story decks to .ydk format (for EDOPro / Duelingbook)
./manage.sh export-decks
```

---

## 🎮 1. Live Duel Simulator (YGOPro / EDOPro / Omega)

The server runs an automated rule-enforcement duel engine container (`ocgcore`) exposing:
- **Game Client TCP Port:** `localhost:7911` (or your LAN IP: `192.168.1.107:7911`)
- **Web Room Manager:** `http://localhost:7922`

### Connecting from EDOPro / YGOPro:
1. Open your EDOPro / YGOPro client.
2. Go to **Multiplayer / Duel Online**.
3. Select **Direct Connect / IP Connection**:
   - **Host:** `localhost` (or your machine's IP for friends on your network / VPN)
   - **Port:** `7911`
4. Enter any room name or leave blank for auto-matching.

### Custom Card Expansions:
- Custom cards are automatically compiled into:
  `server-data/expansions/custom_cards.cdb`
- Custom Lua effect scripts reside in:
  `server-data/expansions/scripts/c<id>.lua`
- To share custom cards with other players, simply copy `custom_cards.cdb` and the `scripts/` folder to their client's `expansions/` directory!

---

## 🌐 2. Duelingbook Integration & Card Pipeline

Duelingbook is the primary design workshop for card artwork, text, and manual testing.

### Workflow:
1. **Design on Duelingbook:** Create your custom card with artwork, stats, and effects.
2. **Export or Define JSON:** Save your card details or export from Duelingbook.
3. **Import:**
   ```bash
   ./manage.sh import cards.json
   ```
4. **Automatic Synchronization:**
   - The card is added to `story_database/ygo_story.db` with its Duelingbook URL and image.
   - The simulator `.cdb` database is updated.
   - A starter Lua effect script (`c<id>.lua`) is generated in `server-data/expansions/scripts/`.
   - The card is instantly searchable in the Discord bot and Web Dashboard!

---

## 🤖 3. Discord Story & Lore Bot (`ygo-story-bot`)

The Discord bot brings your custom card lore, worldbuilding sagas, and character decks into your Discord community.

### Available Slash Commands:
- `/card <name>`: Displays a rich card embed with card frame color, Duelingbook artwork thumbnail, full stats/effect, and in-universe story lore.
- `/lore <query>`: Explores saga chronicles, faction histories, and duelist dossiers.
- `/deck <name>`: Displays character deck profiles and card breakdowns.
- `/stats`: Shows registered custom cards, factions, characters, and duel simulator status.

### Setting up the Discord Bot Token:
1. Create a Discord Bot application at the [Discord Developer Portal](https://discord.com/developers/applications).
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

A modern responsive web dashboard is running locally at:
👉 **`http://localhost:8000`**

- Search custom cards by name, effect keywords, or lore backstory with real-time filtering.
- Direct links to Duelingbook card views.
- REST API available at `http://localhost:8000/api/cards` and `http://localhost:8000/api/lore`.
- Managed automatically in background via PM2 (`pm2 status`).

---

## 🗂️ 5. Project Directory Structure

```
/home/professorseanex/yugioh-server/
├── README.md                          # Platform Documentation
├── manage.sh                          # Master CLI Controller
├── docker-compose.yml                 # Live Duel Simulator configuration
├── server-data/                       # Live Duel Simulator state
│   ├── config/                        # Server port & rules config
│   ├── expansions/                    # Custom cards & Lua scripts
│   │   ├── custom_cards.cdb           # Compiled SQLite simulator database
│   │   └── scripts/                   # Lua effect scripts (c<id>.lua)
│   ├── decks/                         # Exported character .ydk decks
│   └── replays/                       # Saved duel replays (.yrp)
├── story_database/
│   ├── schema.sql                     # Full relational database schema
│   ├── ygo_story.db                   # Main SQLite database
│   ├── seed_story_data.py             # Sample story, lore, & card seeder
│   └── api_server.py                  # FastAPI web catalog & dashboard
├── tools/
│   ├── duelingbook_importer.py        # Duelingbook card parser & importer
│   ├── cdb_builder.py                 # YGOPro/EDOPro .cdb generator
│   ├── lua_generator.py               # Lua effect scaffold generator
│   └── export_deck.py                 # .ydk deck exporter
├── discord_bot/
│   ├── bot.py                         # Discord bot with slash commands
│   └── config.example.json            # Configuration template
└── venv/                              # Isolated Python environment
```
