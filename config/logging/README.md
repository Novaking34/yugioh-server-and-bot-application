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
