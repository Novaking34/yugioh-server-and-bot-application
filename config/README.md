# ⚙️ Configuration Subsystem (`config/`)

The `config/` directory serves as the **single source of truth** for all platform runtime configurations, canonical filesystem paths, service credentials, network manifests, and engine parameters across the entire Yu-Gi-Oh! custom card, story, and duel platform.

In alignment with scalable production architecture, only system-wide core modules reside directly in the root of `config/`. All subsystem-specific files are organized into dedicated subfolders (`bot/`, `client/`, `simulator/`).

---

## 📁 Directory Structure & File Manifest

```bash
config/
├── __init__.py            # Master export hub (facade for settings, paths, bot config)
├── paths.py               # Canonical filesystem paths & idempotent directory creator
├── settings.py            # Strongly-typed dataclass settings & global singleton
├── README.md              # Subsystem documentation (this file)
├── bot/                   # The Great Kasutamaiza Discord bot configuration
│   ├── __init__.py        # Dynamic credential resolution & BOT_CONFIG exporter
│   ├── config.example.json# Template override JSON for local testing
│   └── README.md          # Bot configuration documentation & schema guide
├── client/                # Game client connection & distribution manifests
│   ├── config.json        # Live server connection manifest & updater URLs
│   └── README.md          # Client manifest documentation & schema guide
├── dns/                   # Domain & DNS zone file configurations
│   ├── thelandofkustomazi.com.zone # BIND RFC 1035 zone file for Cloudflare/BIND9
│   └── README.md          # DNS routing & proxy status documentation
└── simulator/             # ocgcore live duel server configuration package
    ├── config.json        # Simulator room rules, ports, timers, and banlists
    ├── admin_user.json    # In-game moderator credentials & access levels
    ├── badwords.json      # Chat profanity censorship filter list
    ├── dialogues.json     # Automated duel announcements & system broadcasts
    ├── tips.json          # Duel loading screen and waiting room gameplay tips
    └── README.md          # Duel engine configuration documentation & schema guide
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
│ 3. Dedicated Subsystem Configuration Files                  │
│    e.g., config/client/config.json, config/simulator/*.json │
└──────────────────────────────┬──────────────────────────────┘
                               │ (falls back to)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Typed Code Defaults (Lowest Priority)                    │
│    e.g., dataclass defaults defined in config.settings       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Core Module Reference

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
| `CONFIG_DIR` | `config/` | Root configuration directory |
| `CLIENT_CONFIG_DIR` | `config/client/` | Client connection manifest directory |
| `CLIENT_CONFIG_PATH` | `config/client/config.json` | Master client connection manifest file |
| `BOT_CONFIG_DIR` | `config/bot/` | Discord bot configuration directory |
| `BOT_EXAMPLE_CONFIG_PATH` | `config/bot/config.example.json` | Bot local testing configuration template |
| `SIMULATOR_CONFIG_DIR` | `config/simulator/` | Duel simulator engine configuration directory |
| `STORY_DB_PATH` | `production/main/web/ygo_story.db` | Primary SQLite lore & card database |
| `CDB_OUTPUT_PATH` | `production/shared/expansions/custom_cards.cdb` | Compiled SQLite CDB card database |
| `SCRIPTS_DIR` | `production/shared/expansions/scripts/` | Directory containing all Lua card scripts (`c*.lua`) |
| `DECKS_DIR` | `production/shared/decks/` | Directory for canonical `.ydk` deck files |
| `DIST_DIR` | `dist/` | Standalone release bundles (`.zip`, `.tar.gz`, checksums) |

#### Utility Functions

- `ensure_directories()`: Idempotently creates all required directories on startup.
- `get_all_runtime_directories()`: Returns the list of all directory paths used across services.

---

### 3. `config.bot` — Discord Bot Configuration Engine

Located in [`config/bot/`](file:///home/professorseanex/yugioh-server/config/bot). Loads bot credentials, command prefixes, and target Guild IDs. It interfaces with `production/main/discord_bot/bot_config.py` via an automated backwards-compatibility bridge.

---

### 4. `config/client/` — Client Connection Manifest

Located in [`config/client/config.json`](file:///home/professorseanex/yugioh-server/config/client/config.json). Used by the client release packager (`./manage.sh package`) and desktop client launchers.

The files `production/shared/config.json` and `packages/client/config.json` are symlinked directly to `config/client/config.json` to guarantee zero drift between development and release distributions.

---

### 5. `config/simulator/` — Game Engine Configuration

The live ocgcore simulator container (`professorseanex/ygoserver:latest`) reads its configuration directly from this directory via host bind-mount (`config/simulator/` ➔ `/ygoserver/config`).

---

## 🔒 Security Best Practices

1. **Never commit `.env`**: Secret tokens, webhook URLs, and passwords must remain in `.env` (which is excluded in `.gitignore`).
2. **Use `.env.example` as a template**: When adding new configuration keys, document them in `.env.example` with sanitized placeholder values.
3. **Always use `settings.as_sanitized_dict()` when logging**: Never print the raw `settings` object or `os.environ` to console or logs, as this could expose tokens.
