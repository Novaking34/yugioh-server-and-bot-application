# ⚙️ Master Configuration & Telemetry Specification

This document serves as the authoritative architectural blueprint for the centralized **Configuration Subsystem** (`config/`) and its unified pairing with **Logging** and **Debugging**.

It details configuration precedence, typed dataclass schemas, environment variable bindings, structured logging contracts, and the automated diagnostic debugger.

---

## 🏛️ 1. Architectural Philosophy: Why Centralize & Promote Configs?

In a multi-application platform consisting of a **Live Duel Simulator** (Docker), a **Modular Discord Bot** (asyncio), a **FastAPI Web Catalog** (ASGI), and **Standalone Client Packages**, decentralized configuration leads directly to:

* **Configuration Drift**: Different applications using different ports, timeouts, or rules.
* **Brittle Deployments**: Secrets and URLs hardcoded in scattered application scripts.
* **Silent Failures**: Missing fallback values that cause unhandled crashes during production runtime.

### The Promotion Doctrine

Any constant, setting, port, credential, timeout, or diagnostic rule that affects more than one subsystem or defines system-wide behavior is **promoted** into the global [`config/`](file:///home/professorseanex/yugioh-server/config/) package.

---

## 🪜 2. Configuration Precedence & Resolution Hierarchy

Configurations resolve through a strict 5-tier precedence hierarchy, ensuring predictability from local developer laptops to 24/7 cloud deployments:

```text
┌────────────────────────────────────────────────────────┐
│ 1. Operating System Environment Variables (Highest)   │
│    (e.g. export LOG_LEVEL=DEBUG, DISCORD_BOT_TOKEN)    │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Local Environment Secrets File (.env)              │
│    (Loaded automatically by python-dotenv)             │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Strongly-Typed Settings Engine (config.settings)    │
│    (Dataclasses validating types, parsing ints/bools)  │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. Domain JSON Overrides (e.g. packages/client/config.json
│    or production/main/discord_bot/config.json)         │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ 5. Safe Embedded Production Defaults (Lowest)         │
│    (e.g. port=7911, log_level="INFO", host="0.0.0.0")  │
└────────────────────────────────────────────────────────┘
```

---

## 📁 3. Configuration Subsystem Directory Layout

```bash
config/
├── __init__.py                    # [4-Block] Master hub re-exporting paths, settings, and logging
├── paths.py                       # [4-Block] Canonical filesystem directory & file path bindings
├── settings.py                    # [4-Block] Strongly-typed configuration dataclasses & singleton
├── game_rules.py                  # [4-Block] Promoted global card bitmasks & deck legality limits
├── logging/                       # Structured multi-target logging subsystem
│   ├── __init__.py                # Exports get_logger and audit_operation
│   ├── logger.py                  # [4-Block] ANSI terminal + rotating JSON formatters
│   ├── log_tool.py                # [4-Block] CLI log query, tail, stats, and cleaner
│   └── README.md                  # Logging subsystem operations guide
└── debugger/                      # Centralized diagnostic assertion & debugging subsystem
    ├── __init__.py                # Debugger hooks & failpoint detection exports
    ├── diagnostics.py             # [4-Block] System health rules & automated integrity audits
    ├── tracer.py                  # [4-Block] Correlation IDs, execution timers, & slow-query traps
    └── README.md                  # Debugging workflows & diagnostic failpoint guide

*(Note: Discord Bot runtime configurations reside in production/main/discord_bot/, Player Client manifests in packages/client/, Server DNS zone infrastructure in packages/server/dns/, and simulator runtime configs in data/simulator/config/).*
```

---

## 📋 4. Configuration Dataclass Specifications

All platform settings are declared as typed, frozen dataclasses inside [`config/settings.py`](file:///home/professorseanex/yugioh-server/config/settings.py):

| Dataclass | Responsibilities | Key Attributes & Defaults |
| :--- | :--- | :--- |
| `PlatformConfig` | Runtime mode & base paths | `environment="production"`, `log_level="INFO"`, `debug=False`, `base_dir` |
| `NetworkConfig` | Public hostnames & HTTP | `public_domain="thelandofkustomazi.com"`, `web_port=8000`, `cors_origins="*"` |
| `SimulatorConfig` | Live ocgcore container | `host="thelandofkustomazi.com"`, `port=7911`, `room_port=7922`, `docker_image` |
| `DiscordConfig` | Discord bot identity | `bot_token`, `guild_id`, `client_id`, `command_prefix="!"` |
| `CloudflareConfig` | Zero Trust edge tunnel | `tunnel_token`, `tunnel_id`, `tunnel_name="ygo-server-tunnel"` |
| `DuckDNSConfig` | Dynamic DNS updater | `domain="thelandofkustomazi"`, `token` |
| `StorageConfig` | Data paths | `db_path`, `cdb_path`, `scripts_dir`, `pics_dir`, `decks_dir`, `trackers_dir` |
| `DatabaseConfig` | SQLite engine pragmas | `busy_timeout=5000`, `wal_mode=True`, `foreign_keys=True`, `pool_size=5` |
| `DebugConfig` | Debugger assertions | `slow_query_ms=50`, `capture_locals=True`, `auto_audit_on_error=True` |
| `PipelineConfig` | Card ingestion & caching | `duelingbook_api_endpoint`, `card_art_cache_dir`, `auto_sync_interval_minutes=15` |
| `LoggingConfig` | Multi-sink logging & audit | `level="INFO"`, `format="text"`, `combined_log_path`, `errors_log_path`, `audit_log_path`, `backup_count=5` |

---

## 📊 5. Structured Logging Architecture (`config/logging/`)

The logging engine provides high-performance, non-blocking, multi-destination telemetry:

```text
                          ┌────────────────────────┐
                          │   LOGGING EVENT CALL   │
                          │   logger.info(msg)     │
                          └───────────┬────────────┘
                                      │
           ┌──────────────────┬───────┴──────────┬──────────────────┐
           ▼                  ▼                  ▼                  ▼
┌─────────────────────┐┌──────────────┐┌─────────────────────┐┌──────────────┐
│ ANSI Console Stream ││ Service Sink ││ Combined Timeline   ││ Error Sink   │
│   (stdout / TTY)    ││(logs/<s.log) ││ (logs/combined.log) ││(logs/errors) │
└─────────────────────┘└──────────────┘└─────────────────────┘└──────────────┘
                               │
                               ▼
               ┌────────────────────────────────┐
               │ Operational Audit Ledger       │
               │        (logs/audit.jsonl)      │
               └────────────────────────────────┘
```

### Destination Log Sinks

* `logs/combined.log`: Chronological ledger of all platform events (15 MB max, 5 backups).
* `logs/<service>.log`: Subsystem-isolated streams (`web.log`, `bot.log`, `simulator.log`, `tools.log`).
* `logs/errors.log`: High-severity filter capturing `WARNING`, `ERROR`, and `CRITICAL` records across all services.
* `logs/audit.jsonl`: Append-only structured JSONL audit ledger tracking operational mutations and durations.
* Terminal Console (`stdout`): Colorized ANSI stream with automatic trace ID badges.

---

## 🔍 6. Pairing the Debugger with the Logger

Debugging in a distributed multi-service architecture cannot rely solely on interactive breakpoints. The debugger pairs directly with the logger to provide **Continuous Diagnostic Telemetry**:

```text
                       ┌───────────────────────────────┐
                       │   with audit_operation(...)   │
                       └───────────────┬───────────────┘
                                       │
                      ┌────────────────┴────────────────┐
                      ▼                                 ▼
             [SUCCESSFUL PATH]                  [EXCEPTION PATH]
                      │                                 │
             Logs duration (ms)                 1. Traps exception with locals
             Records success telemetry          2. Logs ERROR with Incident UUID
                                                3. Emits diagnostic failpoint
                                                4. Writes crash snapshot JSON
```

### Key Debugger Capabilities

1. **Correlation IDs (`trace_id`)**: Every request, slash command, or compile batch receives a UUID. All log events and debug traces inherit this ID.
2. **Slow-Query Detection**: Database operations taking longer than `DebugConfig.slow_query_ms` (50ms) automatically log `WARNING` events with the SQL statement and execution plan.
3. **Automated Diagnostic Probes**: When an error occurs, the debugger invokes [`PlatformDiagnostics`](file:///home/professorseanex/yugioh-server/development/tools/debug_diagnostics.py) to audit DB integrity, missing Lua scripts, and artwork availability, writing a diagnostic snapshot into `logs/debug_snapshots/`.
