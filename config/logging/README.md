# 📝 Centralized Platform Logging Subsystem (`config/logging/`)

The `config/logging/` package provides a structured, thread-safe, and multi-destination logging architecture shared across all platform subsystems:

* **Production Host Services** (`production/main/`):
  * Web Catalog & REST API (`service="WEB"`)
  * Discord Story & Duel Bot (`service="BOT"`)
  * Live Duel Simulator Container (`service="SIMULATOR"`)
  * Desktop GUI Platform Manager (`service="GUI"`)
  * Host Server Setup Wizard (`service="WIZARD"`)
* **Development Pipeline** (`development/`):
  * SQLite CDB Compilers (`service="CDB"`)
  * Duelingbook Card Importers (`service="IMPORTER"`)
  * Lua Effect Script Generators (`service="LUA"`)
  * Diagnostic & Debugging Suite (`service="DIAG"`)
* **Distribution Packages** (`packages/`):
  * Standalone Client Expansion Sync (`service="CLIENT"`)
  * Host Server Deployment Scripts (`service="SERVER"`)

---

## 🚀 Quick Usage

### Standard Logger

```python
from config.logging import get_logger

logger = get_logger("my_component", service="WEB")
logger.info("Handling card search request")
logger.warning("Query took longer than expected")
logger.error("Failed to parse card definition", exc_info=True)
```

### Audit Operation Context Manager

```python
from config.logging import audit_operation

# Automatically logs start, end with elapsed time, and records unhandled exceptions:
with audit_operation("Compile Expansion CDB", service="CDB"):
    build_cdb()
```

### Logging Diagnostic Snapshots

```python
from config.logging import log_diagnostic_snapshot
from development.tools.debug_diagnostics import PlatformDiagnostics

diag = PlatformDiagnostics()
result = diag.audit_card_bitmasks()
log_diagnostic_snapshot(result, service="DIAG")
```

---

## 📁 Destination Files

All logs are written into the root `logs/` directory:

| Log File | Contents | Rotation Policy |
| :--- | :--- | :--- |
| `logs/combined.log` | Unified timeline of all subsystem activity across the platform | 15 MB max, 5 historical backups |
| `logs/<service>.log` | Service-specific stream (e.g. `web.log`, `bot.log`, `simulator.log`) | 10 MB max, 5 historical backups |
| Terminal Console (stdout) | Real-time ANSI colored output (auto-disabled on non-TTY) | Stream |

---

## ⚙️ Environment Variables

Configure logging behavior via `.env` or system environment:

* `LOG_LEVEL`: Minimum severity to log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default: `INFO`.
* `LOG_FORMAT`: Format style (`text` with ANSI colors or `json` for automated observability pipelines). Default: `text`.

---

## 🛠️ Log Management & Telemetry CLI Tool (`log_tool.py`)

A dedicated CLI management tool is included in `config/logging/log_tool.py`:

```bash
# View storage statistics, line counts, and error counts across all log files:
python3 -m config.logging.log_tool stats

# Tail the most recent lines of a service log:
python3 -m config.logging.log_tool tail --service web -n 50

# Query logs filtering by severity level, service, or keyword:
python3 -m config.logging.log_tool query --level ERROR --limit 25
python3 -m config.logging.log_tool query --keyword "passcode"

# Safely truncate all log files (free up disk space):
python3 -m config.logging.log_tool clean --confirm
```
