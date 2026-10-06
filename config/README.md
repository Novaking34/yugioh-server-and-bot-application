# ⚙️ Centralized Configuration & Invariants Subsystem (`config/`)

The `config/` directory serves as the **authoritative single source of truth** for platform runtime configurations, global game invariants, strongly-typed dataclass settings, structured logging engines, distributed execution tracing, system diagnostics, and network manifests across the entire Yu-Gi-Oh! custom card, story, and duel platform.

Every Python module in this subsystem strictly adheres to the standard **C-Style 4-Block Compilation Unit Architecture** (`BLOCK 1: METADATA`, `BLOCK 2: OPENING`, `BLOCK 3: BODY`, `BLOCK 4: CLOSING`).

For comprehensive architectural specifications, refer to:

- [Platform Data Architecture (`docs/DATA_ARCHITECTURE.md`)](file:///home/professorseanex/yugioh-server/docs/DATA_ARCHITECTURE.md)
- [Centralized Configuration System (`docs/CONFIGURATION_SYSTEM.md`)](file:///home/professorseanex/yugioh-server/docs/CONFIGURATION_SYSTEM.md)

---

## 📁 Directory Structure & File Manifest

```bash
config/
├── __init__.py            # Master export hub (unified import surface for all platform tiers)
├── paths.py               # Canonical filesystem paths & idempotent directory creator
├── settings.py            # Strongly-typed dataclass settings & global singleton (11 domains)
├── game_rules.py          # Authoritative Master Rule 5 invariants, bitmasks & passcode partitions
├── README.md              # Subsystem documentation (this file)
├── debugger/              # Centralized diagnostic auditor & execution tracing
│   ├── __init__.py        # Re-exports tracing, diagnostics, and run_diagnostics orchestrator
│   ├── tracer.py          # ContextVar correlation IDs, trace_span latency timers, slow query traps
│   ├── diagnostics.py     # Authoritative 14-table DB audit, bitmask checks, CDB parity, Lua validator
│   └── README.md          # Debugger subsystem documentation & developer reference
└── logging/               # Multi-sink structured JSON logging engine
    ├── __init__.py        # Re-exports get_logger, audit_operation, log_diagnostic_snapshot
    ├── logger.py          # Rotating file, audit file & console logging with trace_id correlation
    ├── log_tool.py        # CLI management utility (tail, stats, audit, query)
    └── README.md          # Logging subsystem documentation & usage examples

*(Note: Discord Bot runtime configurations are colocated under [`production/main/discord_bot/`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/), Player Client manifests under [`packages/client/`](file:///home/professorseanex/yugioh-server/packages/client/), Server DNS zone infrastructure under [`packages/server/dns/`](file:///home/professorseanex/yugioh-server/packages/server/dns/), and simulator runtime configurations under [`data/simulator/config/`](file:///home/professorseanex/yugioh-server/data/simulator/config/) alongside operational data stores).*
```

---

## 🏛️ Configuration Architecture & Resolution Hierarchy

All platform subsystems resolve their settings through a strictly-ordered 5-tier precedence hierarchy:

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
│    e.g., packages/client/config.json, data/simulator/config │
└──────────────────────────────┬──────────────────────────────┘
                               │ (falls back to)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Unified Data Directory Configuration (data/)             │
│    e.g., data/authoritative/content.db                      │
└──────────────────────────────┬──────────────────────────────┘
                               │ (falls back to)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Strongly-Typed Dataclass Defaults (Lowest Priority)      │
│    e.g., dataclass defaults defined in config.settings       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Core Module Reference

### 1. [`config.game_rules`](file:///home/professorseanex/yugioh-server/config/game_rules.py) — Authoritative Game Invariants

Centralizes all Master Rule 5 bitmasks and rules promoted from legacy tool scripts:

- **Passcode Partitions**: Official card range (`1–49999999`) and custom expansion partition (`50000000–99999999`).
- **Composite Types (`datas.type`)**: `TYPE_MONSTER`, `TYPE_SPELL`, `TYPE_TRAP`, `TYPE_NORMAL`, `TYPE_EFFECT`, `TYPE_FUSION`, `TYPE_RITUAL`, `TYPE_SYNCHRO`, `TYPE_XYZ`, `TYPE_PENDULUM`, `TYPE_LINK`, `TYPE_TUNER`, etc.
- **Elemental Attributes (`datas.attribute`)**: Mutually exclusive single-bit powers of 2 (`ATTRIBUTE_EARTH` through `ATTRIBUTE_DIVINE`).
- **Monster Races (`datas.race`)**: All 26 canonical types (`RACE_WARRIOR` through `RACE_ILLUSION`).
- **Link Arrow Compass (`datas.def`)**: 8-point compass octal bitmasks (`0o001` through `0o400`, bounded by `0o757`).
- **Tournament Deck Boundaries**: Minimum Main Deck (40), Maximum Main Deck (60), Extra Deck limit (15), Side Deck limit (15), Max Copies per Card (3).
- **Field Zones**: Canonical identifiers for all duel zones (`ZONE_MAIN_DECK`, `ZONE_EXTRA_DECK`, `ZONE_HAND`, `ZONE_FIELD_SPELL`, `ZONE_GRAVEYARD`, `ZONE_BANISHMENT`, `ZONE_EXTRA_MONSTER`, `ZONE_PENDULUM`, `ZONE_MAIN_MONSTER`, `ZONE_SPELL_TRAP`).

---

### 2. [`config.settings`](file:///home/professorseanex/yugioh-server/config/settings.py) — Strongly-Typed Dataclass Settings

Provides frozen dataclasses mapped across 10 functional domains of the platform:

| Dataclass | Domain | Key Attributes |
| :--- | :--- | :--- |
| [`PlatformConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Environment & Core Modes | `environment`, `log_level`, `debug`, `is_production`, `is_development` |
| [`NetworkConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Domain Names & Ports | `public_domain`, `public_fallback_domain`, `web_port` (8000), `cors_origins` |
| [`SimulatorConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | ocgcore Duel Container | `host`, `port` (7911), `room_port` (7922), `docker_image`, `direct_connect_address` |
| [`DiscordConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | The Great Kasutamaiza Bot | `bot_token`, `guild_id`, `command_prefix`, `is_configured` |
| [`CloudflareConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Zero Trust Edge Tunnel | `tunnel_token`, `tunnel_id`, `tunnel_name`, `is_configured` |
| [`DuckDNSConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Dynamic DNS Failover | `domain`, `token`, `full_domain`, `is_configured` |
| [`StorageConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Canonical File Locations | `data_dir`, `authoritative_dir`, `db_path`, `cdb_path`, `scripts_dir`, `decks_dir`, `pics_dir` |
| [`PipelineConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Ingestion & Sync Pipelines | `duelingbook_api_endpoint`, `card_art_cache_dir`, `sync_interval` |
| [`DatabaseConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | SQLite Engine Tuning | `wal_mode`, `busy_timeout_ms` (5000), `foreign_keys`, `cache_size` |
| [`DebugConfig`](file:///home/professorseanex/yugioh-server/config/settings.py) | Debugger & Telemetry | `slow_query_ms` (50.0), `capture_locals`, `snapshot_retention_days` |

---

### 3. [`config.paths`](file:///home/professorseanex/yugioh-server/config/paths.py) — Canonical Filesystem Path Authority

Eliminates fragile relative paths (`../../..`) by computing all absolute paths from the project root (`BASE_DIR`):

| Constant | Path Target | Description |
| :--- | :--- | :--- |
| `BASE_DIR` | `/home/professorseanex/yugioh-server` | Root of the repository |
| `CONFIG_DIR` | `config/` | Root configuration directory |
| `DATA_DIR` | `data/` | Root unified storage hierarchy |
| `AUTHORITATIVE_DATA_DIR` | `data/authoritative/` | Single source of truth master store |
| `STORY_DB_PATH` | `data/authoritative/content.db` | Primary SQLite lore & card database |
| `CONTENT_DB_PATH` | `data/authoritative/content.db` | Authoritative content database (cards, lore, story) |
| `TELEMETRY_DB_PATH` | `data/telemetry/telemetry.db` | Dynamic player telemetry & rating database |
| `SCHEMA_PATH` | `data/authoritative/schema.sql` | Authoritative SQLite schema definition |
| `SEED_SCRIPT_PATH` | `data/authoritative/seed_databases.py` | Deterministic database seeding script |
| `TRACKERS_DIR` | `data/trackers/` | Master card spreadsheets (CSV/TSV) |
| `ARTWORK_DIR` | `data/artwork/` | Raw master card artwork repository |
| `EXPANSIONS_DIR` | `data/expansions/` | Simulator expansion outputs |
| `CDB_OUTPUT_PATH` | `data/expansions/custom_cards.cdb` | Compiled SQLite CDB card database |
| `SCRIPTS_DIR` | `data/expansions/scripts/` | Directory containing all Lua card scripts (`c*.lua`) |
| `DECKS_DIR` | `data/decks/` | Directory for canonical `.ydk` deck files |
| `DIST_DIR` | `dist/` | Standalone release bundles (`.zip`, `.tar.gz`, checksums) |
| `LOGS_DIR` | `logs/` | Runtime logs and crash snapshots |

---

### 4. [`config.logging`](file:///home/professorseanex/yugioh-server/config/logging/) — Structured JSON Logging Engine

- **Multi-Sink Logging**: Simultaneously outputs human-readable ANSI colored terminal messages, structured JSON records to `logs/<service>.log` with rotating file handlers, and tamper-evident records to `logs/audit.log`.
- **Correlation ID Tracking**: Automatically binds log records to the active `trace_id` established by `config.debugger.tracer`.
- **CLI Log Inspection (`manage.py logs`)**:

  ```bash
  ./manage.sh logs stats          # Display file sizes and line counts
  ./manage.sh logs tail bot       # Tail live discord bot log entries
  ./manage.sh logs audit          # Review security and sensitive operations
  ./manage.sh logs query ERROR    # Search logs for error-level events
  ```

---

### 5. [`config.debugger`](file:///home/professorseanex/yugioh-server/config/debugger/) — Diagnostics & Execution Tracing

- **Context-Local Trace IDs**: Propagates asynchronous execution IDs across coroutines and threads.
- **Latency Spans (`trace_span`)**: Measures block execution durations with configurable warning budgets.
- **Slow Query Detection (`measure_slow_query`)**: Traps queries taking longer than `DEBUG_SLOW_QUERY_MS` (50.0 ms).
- **14-Table Relational Schema Audit**: Checks `PRAGMA integrity_check`, verifies foreign key constraints, FTS5 index counts, and confirms all 14 database tables exist.
- **Card Bitmask & Geometry Checks**: Audits passcodes, octal link compass masks, Pendulum scales, and attributes.
- **Crash Snapshots (`take_debug_snapshot`)**: Captures diagnostic state to `logs/debug_snapshots/snapshot_<id>.json`.
- **CLI Diagnostics**:

  ```bash
  ./manage.sh diagnose
  ```

---

## 🔒 Security Best Practices

1. **Never commit `.env`**: Secret tokens, webhook URLs, and passwords must remain in `.env` (which is excluded in `.gitignore`).
2. **Use `.env.example` as a template**: When adding new configuration keys, document them in `.env.example` with sanitized placeholder values.
3. **Always use `settings.as_sanitized_dict()` when logging**: Never print the raw `settings` object or `os.environ` to console or logs, as this could expose tokens.
