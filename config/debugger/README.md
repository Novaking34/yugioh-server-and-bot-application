# 🛠️ Platform Debugger & Telemetry Diagnostics Subsystem

The **Centralized Debugger Subsystem** ([`config/debugger/`](file:///home/professorseanex/yugioh-server/config/debugger/)) provides deep platform observability, execution tracing, slow SQL query detection, automated post-mortem crash snapshots, and comprehensive 14-table database integrity auditing across the Yu-Gi-Oh! platform.

It is tightly coupled with the [Structured Logging Engine](file:///home/professorseanex/yugioh-server/config/logging/) to bind every log record, error, and database operation to an asynchronous correlation ID (`trace_id`).

---

## 🏗️ Architecture & Component Overview

```bash
config/debugger/
├── __init__.py         # Re-exports tracing, diagnostics, and run_diagnostics orchestrator
├── tracer.py           # ContextVar correlation IDs, trace_span latency timers, slow query traps
├── diagnostics.py      # Authoritative 14-table DB audit, bitmask checks, CDB parity, Lua validator
└── README.md           # Subsystem documentation and developer reference
```

### 1. Execution Tracing ([`tracer.py`](file:///home/professorseanex/yugioh-server/config/debugger/tracer.py))

- **Asynchronous Correlation IDs**: Uses Python `contextvars.ContextVar` to propagate a unique 8-character hex or UUID across asynchronous coroutines, discord tasks, and thread workers.
- **Latency Spans (`trace_span`)**: Context manager that measures block execution latency, automatically emitting structured debug/info logs with elapsed milliseconds.
- **Slow Query Interceptor (`measure_slow_query`)**: Asserts database query durations against `DEBUG_SLOW_QUERY_MS` (default: 50.0 ms), logging actionable warnings when queries exceed the budget.

### 2. Comprehensive Diagnostics ([`diagnostics.py`](file:///home/professorseanex/yugioh-server/config/debugger/diagnostics.py))

- **Two-Tier Relational Schema Audit**: Asserts SQLite `PRAGMA integrity_check` across both stores, validates foreign key relationships, checks FTS5 full-text index synchronization, and verifies all 17 active tables:
  11 content tables (`custom_cards`, `factions`, `characters`, `decks`, `deck_cards`, `cards_fts`, `lore_arcs`, `worldbuilding_elements`, `story_chapters`, `story_stages`, `duel_logs`) in `content.db` and 6 telemetry tables (`player_ratings`, `duel_matches`, `card_usage_stats`, `player_decks`, `player_saved_decks`, `player_story_progress`) in `telemetry.db`.
- **Card Metadata & Bitmask Assertions**: Validates 8-digit custom passcode ranges (`50000000–59999999`), Link compass octal bitmasks (`0o757`), Pendulum scales (`0–13`), single-bit power-of-2 attributes, and ATK/DEF statistics.
- **Binary CDB Parity**: Compares SQLite story database records 1:1 against `custom_cards.cdb` (`datas` and `texts` tables).
- **Lua Script Syntax & ocgcore Validation**: Verifies mandatory `local s, id = GetID()` headers, `initial_effect` declarations, and runs `luac -p` bytecode verification.
- **Story Deck Validation**: Asserts `.ydk` file formats, `#main` / `!side` section headers, and non-empty valid passcodes.
- **Card Artwork Availability**: Verifies that every custom card has a corresponding high-resolution JPEG in `pics/` exceeding minimum byte thresholds.
- **Post-Mortem Crash Snapshots (`take_debug_snapshot`)**: When unhandled exceptions occur, captures the full platform diagnostic state and active local variables into `logs/debug_snapshots/snapshot_<incident_id>.json`.

---

## 🚀 Usage & Developer Workflows

### 1. Running Platform Diagnostics via CLI

Execute the master diagnostic suite across all 6 audit domains:

```bash
./manage.sh diagnose
```

Or directly using the Python compilation unit:

```bash
python3 config/debugger/diagnostics.py
```

### 2. Tracing Asynchronous Operations & Function Spans

```python
from config.debugger import trace_span, set_trace_id

# Establish a trace boundary for a Discord interaction or HTTP request
set_trace_id("req_abc123")

with trace_span("Card Search Query", service="SEARCH", warn_threshold_ms=100.0):
    results = search_cards_by_name("Starforged")
```

### 3. Monitoring Slow Database Queries

```python
import time
from config.debugger import measure_slow_query

start_time = time.perf_counter()
cursor.execute("SELECT * FROM custom_cards WHERE effect_text LIKE '%banish%'")
duration_ms = (time.perf_counter() - start_time) * 1000.0

measure_slow_query(sql_statement, duration_ms, threshold=50.0, service="SQLITE")
```

### 4. Taking Automated Crash Snapshots

```python
from config.debugger import take_debug_snapshot

try:
    process_complex_card_sync()
except Exception as ex:
    snapshot_path = take_debug_snapshot("ERR_CARD_SYNC_001", context={"exception": str(ex)})
    logger.critical(f"Fatal error occurred! Diagnostic snapshot saved: {snapshot_path}")
```

---

## ⚙️ Configuration & Environment Settings

The debugger is configured through [`config/settings.py`](file:///home/professorseanex/yugioh-server/config/settings.py) via `DebugConfig`:

| Environment Variable | Dataclass Field | Default | Description |
| ---------------------- | ----------------- | --------- | ------------- |
| `DEBUG_SLOW_QUERY_MS` | `settings.debug.slow_query_ms` | `50.0` | Maximum allowed query execution time in milliseconds before triggering a slow-query warning. |
| `DEBUG_CAPTURE_LOCALS` | `settings.debug.capture_locals` | `True` | Whether to inspect and record local frame variables during crash snapshot generation. |
| `DEBUG_SNAPSHOT_RETENTION_DAYS` | `settings.debug.snapshot_retention_days` | `7` | Retention window for persisted incident snapshots in `logs/debug_snapshots/`. |

---

## 📋 Audit Suites Reference Table

| Audit Domain | Method | Target Entity | Pass Criteria |
| -------------- | -------- | --------------- | --------------- |
| **Database** | `audit_database()` | `data/authoritative/content.db` & `data/telemetry/telemetry.db` | `PRAGMA integrity_check = ok`, all 17 tables present across two tiers, FTS5 in parity. |
| **Card Bitmasks** | `audit_card_bitmasks()` | `custom_cards` table | Passcodes in range, Link arrows subset of `0o757`, Pendulum scales in `0–13`. |
| **CDB Parity** | `audit_cdb_parity()` | `data/expansions/custom_cards.cdb` | Row counts match `custom_cards`, `datas` and `texts` tables identical in count. |
| **Lua Scripts** | `audit_lua_scripts()` | `data/expansions/scripts/` | `local s, id = GetID()` present, `initial_effect` present, passes `luac -p`. |
| **Story Decks** | `audit_decks()` | `data/decks/` | Valid `#main` and `!side` headers, positive numeric passcodes. |
| **Artwork** | `audit_card_artwork()` | `data/expansions/pics/` | Image files present for all cards, file size > 1,000 bytes. |
