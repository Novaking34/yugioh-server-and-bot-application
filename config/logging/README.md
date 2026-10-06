# 📝 Centralized Platform Logging Subsystem (`config/logging/`)

The `config/logging/` package serves as the **authoritative multi-sink observability and telemetry engine** for the entire Yu-Gi-Oh! custom card, story, and duel simulator platform.

Every module within this subsystem strictly adheres to the standard **C-Style 4-Block Compilation Unit Architecture** (`BLOCK 1: METADATA`, `BLOCK 2: OPENING`, `BLOCK 3: BODY`, `BLOCK 4: CLOSING`).

---

## 🏛️ Multi-Sink Architecture

The logging engine writes concurrently to 5 distinct operational sinks to satisfy developer ergonomics, machine observability, and tamper-evident audit requirements:

```text
┌─────────────────────────────────────────────────────────────┐
│                      Logger Ingestion                       │
│    get_logger(name, service="WEB"|"BOT"|"SIMULATOR"|...)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
     │  Console    │    │  Combined   │    │  Service    │
     │  (stdout)   │    │combined.log │    │<service>.log│
     │ Color + TID │    │ 15MB 5 baks │    │ 10MB 5 baks │
     └─────────────┘    └─────────────┘    └─────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     ┌─────────────┐                       ┌─────────────┐
     │  Error Sink │                       │ Audit Ledger│
     │ errors.log  │                       │ audit.jsonl │
     │ WARN/ERR/CRI│                       │ Append-Only │
     └─────────────┘                       └─────────────┘
```

| Log Destination | Target File / Stream | Contents & Filtering | Rotation / Retention |
| :--- | :--- | :--- | :--- |
| **Interactive Console** | Standard Output (`stdout`) | Colorized ANSI stream with timestamp, severity, service, trace ID, and logger name. Auto-disables colors on non-TTY pipes. | Real-time stream |
| **Combined Timeline** | `logs/combined.log` | Chronological unified record of platform events across all services without ANSI escape codes. | 15 MB max, 5 backups |
| **Service Streams** | `logs/<service>.log` | Scoped stream for a specific subsystem (e.g. `web.log`, `bot.log`, `simulator.log`, `cdb.log`). | 10 MB max, 5 backups |
| **High-Severity Error Sink** | `logs/errors.log` | Filtered sink capturing only `WARNING`, `ERROR`, and `CRITICAL` records with full stack traces. | 10 MB max, 5 backups |
| **Operational Audit Ledger** | `logs/audit.jsonl` | Immutable structured single-line JSON records written by `audit_operation` tracking mutations, execution timing, and failures. | Append-only ledger |

---

## 🔗 Distributed Trace ID Correlation

The logging engine seamlessly integrates with `config.debugger` via `ContextEnrichmentFilter`. When any log statement is executed (`logger.info(...)`):

1. The filter queries `config.debugger.tracer.get_current_trace_id()`.
2. The active task-local or thread-local `trace_id` (e.g., `trc-a1b2c3d4e5f6`) is automatically attached to the `LogRecord`.
3. In terminal output, the trace ID is highlighted in blue:

   ```text
   2026-10-05 17:15:00 INFO    [BOT] [trc-a1b2c3d4e5f6] discord_bot: Connected to gateway
   ```

4. In JSON mode (`LOG_FORMAT=json`), `"trace_id": "trc-a1b2c3d4e5f6"` is included in the output schema.

---

## 🚀 Usage Examples

### 1. Standard Logger Factory

```python
from config.logging import get_logger

logger = get_logger("catalog_service", service="WEB")
logger.info("Handling card search request")
logger.warning("Query execution took 62ms (threshold: 50ms)")
logger.error("Failed to parse card definition", exc_info=True)
```

### 2. Operational Audit Context Manager

```python
from config.logging import audit_operation

# Automatically logs initiation, measures elapsed time, reports failures,
# and appends an immutable event to logs/audit.jsonl:
with audit_operation("Sync Expansions", service="SIMULATOR") as log:
    build_cdb()
```

### 3. Diagnostic Snapshot Hook

```python
from config.logging import log_diagnostic_snapshot
from config.debugger import PlatformDiagnostics

diag = PlatformDiagnostics()
result = diag.audit_card_bitmasks()
log_diagnostic_snapshot(result, service="DIAG")
```

---

## ⚙️ Configuration & Environment Variables

| Variable | Default | Allowed Values | Description |
| :--- | :--- | :--- | :--- |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | Minimum log severity to emit. |
| `LOG_FORMAT` | `text` | `text`, `json` | Output format: `text` with ANSI colors, or `json` for cloud telemetry. |

---

## 🛠️ Log Management CLI Tool (`log_tool.py`)

A built-in management utility provides inspection, querying, and storage hygiene:

```bash
# View storage statistics, line counts, and error counts across all log files:
python3 -m config.logging.log_tool stats

# Tail the most recent lines of a service log or the combined stream:
python3 -m config.logging.log_tool tail --service web -n 50
python3 -m config.logging.log_tool tail --service errors -n 30
python3 -m config.logging.log_tool tail --service audit -n 20

# Query logs filtering by severity level, service, or keyword:
python3 -m config.logging.log_tool query --level ERROR --limit 25
python3 -m config.logging.log_tool query --keyword "passcode" --service cdb

# Inspect the structured audit ledger:
python3 -m config.logging.log_tool audit --status FAILED
python3 -m config.logging.log_tool audit --operation "Sync Expansions"

# Safely truncate all log files to reclaim disk space:
python3 -m config.logging.log_tool clean --confirm
```
