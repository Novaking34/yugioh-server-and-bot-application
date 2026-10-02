# ⚙️ Configuration Subsystem (`config/`)

The `config/` directory serves as the **single source of truth** for all platform runtime configurations, filesystem paths, service credentials, network manifests, and engine parameters across the entire Yu-Gi-Oh! custom card, story, and duel platform.

---

## 📁 Directory Structure & File Manifest

```bash
config/
├── __init__.py            # Master export hub (settings, paths, bot config)
├── paths.py               # Canonical filesystem paths & idempotent directory creator
├── settings.py            # Strongly-typed dataclass settings & global singleton
├── bot.py                 # Discord bot configuration & credential resolution engine
├── bot.example.json       # Template JSON file for bot token and guild overrides
├── client.json            # Canonical connection manifest for client distribution
├── README.md              # Comprehensive subsystem documentation (this file)
└── simulator/             # ocgcore live duel server configuration package
    ├── config.json        # Simulator room rules, ports, timers, and banlists
    ├── admin_user.json    # In-game moderator credentials & access levels
    ├── badwords.json      # Chat profanity censorship filter list
    ├── dialogues.json     # Automated duel announcements & system broadcasts
    └── tips.json          # Duel loading screen and waiting room gameplay tips
```

---

## 🏛️ Configuration Architecture & Resolution Hierarchy

All platform subsystems resolve their settings through a strictly-ordered 4-tier hierarchy:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Operating System Environment Variables (Highest Priority)│
│    e.g., export DISCORD_BOT_TOKEN="abc..."                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ (falls back to)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Root Environment File (.env via python-dotenv)           │
│    e.g., DISCORD_BOT_TOKEN=... in /home/.../yugioh-server/.env│
└──────────────────────────────┬──────────────────────────────┘
                               │ (falls back to)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Dedicated Configuration Files                            │
│    e.g., config/client.json, config/simulator/*.json        │
└──────────────────────────────┬──────────────────────────────┘
                               │ (falls back to)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Typed Code Defaults (Lowest Priority)                    │
│    e.g., dataclass defaults defined in config.settings       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Python Module Reference

### 1. `config.settings` — Strongly-Typed Platform Settings

Provides frozen dataclasses mapped to the 8 functional domains of the platform:

| Class | Description | Key Attributes |
| --- | --- | --- |
| [`PlatformConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L44-L60) | Environment mode and logging | `environment`, `log_level`, `is_production`, `is_development` |
| [`NetworkConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L62-L71) | Public DNS, domain, and web ports | `public_domain`, `public_fallback_domain`, `web_port`, `cors_origins` |
| [`SimulatorConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L73-L89) | ocgcore duel container and sockets | `host`, `port` (7911), `room_port` (7922), `docker_image`, `direct_connect_address` |
| [`DiscordConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L91-L103) | The Great Kasutamaiza Bot | `bot_token`, `guild_id`, `command_prefix`, `is_configured` |
| [`CloudflareConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L105-L116) | Zero Trust edge tunnel | `tunnel_token`, `tunnel_id`, `tunnel_name`, `is_configured` |
| [`DuckDNSConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L118-L133) | Dynamic DNS failover updater | `domain`, `token`, `full_domain`, `is_configured` |
| [`StorageConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L135-L143) | SQLite DB, CDB, and script paths | `db_path`, `cdb_path`, `scripts_dir`, `decks_dir` |
| [`PipelineConfig`](file:///home/professorseanex/yugioh-server/config/settings.py#L145-L152) | Card ingestion pipeline | `duelingbook_api_endpoint`, `card_art_cache_dir`, `sync_interval` |

#### Usage Example

```python
from config import settings

# Check runtime environment
if settings.platform.is_production:
    print(f"Connecting to live simulator at {settings.simulator.direct_connect_address}")

# Access public endpoints
print(f"Web Catalog: {settings.network.public_api_url}")

# Safe logging with secret redaction
import json
print(json.dumps(settings.as_sanitized_dict(), indent=2))
```

---

### 2. `config.paths` — Canonical Filesystem Path Authority

Eliminates fragile relative paths (`../../..`) by computing all absolute paths from the project root (`BASE_DIR`):

| Constant | Path Target | Description |
| --- | --- | --- |
| `BASE_DIR` | `/home/professorseanex/yugioh-server` | Root of the repository |
| `CONFIG_DIR` | `config/` | Configuration directory |
| `CLIENT_CONFIG_PATH` | `config/client.json` | Master client connection manifest |
| `SIMULATOR_CONFIG_DIR` | `config/simulator` | Duel simulator engine configuration directory |
| `STORY_DB_PATH` | `production/main/web/ygo_story.db` | Primary SQLite lore & card database |
| `CDB_OUTPUT_PATH` | `production/shared/expansions/custom_cards.cdb` | Compiled SQLite CDB card database |
| `SCRIPTS_DIR` | `production/shared/expansions/scripts` | Directory containing all Lua card scripts (`c*.lua`) |
| `DECKS_DIR` | `production/shared/decks` | Directory for canonical `.ydk` deck files |
| `DIST_DIR` | `dist/` | Standalone release bundles (`.zip`, `.tar.gz`, checksums) |

#### Utility Functions

- `ensure_directories()`: Idempotently creates all required directories on startup.
- `get_all_runtime_directories()`: Returns the list of all directory paths used across services.

---

### 3. `config.bot` — Discord Bot Configuration Engine

Loads bot credentials, command prefixes, and target Guild IDs. It seamlessly interfaces with `production/main/discord_bot/bot_config.py` via an automated backwards-compatibility bridge.

#### Resolution Priority

1. Environment variables (`DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, `DISCORD_COMMAND_PREFIX`)
2. Local JSON overrides (`config/bot.json` or `production/main/discord_bot/config.json`)
3. Hardcoded safe defaults

---

## 🎮 Game Engine Configuration (`config/simulator/`)

The live ocgcore simulator container (`professorseanex/ygoserver:latest`) reads its configuration directly from this directory via host bind-mount:

1. **`config.json`**:
   - `serverport`: TCP listen port for duel lobby discovery (`7911`).
   - `room_port`: TCP listen port for active duel match rooms (`7922`).
   - `max_users`: Maximum concurrent connected duelists.
   - `start_hand` / `draw_count` / `start_lp`: Standard duel rules (5 cards, 1 draw, 8000 LP).
   - `default_rule`: Master Rule set (Rule 5: Revision Master Rule 2020).
2. **`admin_user.json`**:
   - Admin usernames and authorization hashes for in-room `/op` administrative commands.
3. **`badwords.json`**:
   - Regex patterns and word lists filtered in global and room chat.
4. **`dialogues.json`**:
   - Automated server notifications, welcome messages, and match result announcements.
5. **`tips.json`**:
   - Gameplay tips and card ruling reminders displayed during duel loading screens.

---

## 🌐 Client Manifest (`config/client.json`)

Single source of truth used by the client release packager (`./manage.sh package`) and client launchers:

```json
{
  "server_name": "The Great Kasutamaiza Duel Server",
  "server_host": "thelandofkustomazi.com",
  "server_port": 7911,
  "room_port": 7922,
  "fallback_host": "thelandofkustomazi.duckdns.org",
  "web_catalog_url": "https://thelandofkustomazi.com",
  "expansions_update_url": "https://thelandofkustomazi.com/api/expansions/download"
}
```

The files `production/shared/config.json` and `packages/client/config.json` are symlinked directly to `config/client.json` to guarantee zero drift between development and release distributions.

---

## 🔒 Security Best Practices

1. **Never commit `.env`**: Secret tokens, webhook URLs, and passwords must remain in `.env` (which is excluded in `.gitignore`).
2. **Use `.env.example` as a template**: When adding new configuration keys, document them in `.env.example` with sanitized placeholder values.
3. **Always use `settings.as_sanitized_dict()` when logging**: Never print the raw `settings` object or `os.environ` to console or logs, as this could expose tokens.
