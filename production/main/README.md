# 🚀 Host Server Production Main (`production/main/`)

The `production/main/` directory contains the host-side server runtime, services, administrative interfaces, and logging infrastructure that power the live Yu-Gi-Oh! story platform.

---

## 📁 Architectural Manifest

| Component / Subdirectory | Classification | Primary Responsibility |
| :--- | :--- | :--- |
| [`logger.py`](file:///home/professorseanex/yugioh-server/production/main/logger.py) | Logging Forwarder | Backward-compatible re-export from centralized [`config.logging`](file:///home/professorseanex/yugioh-server/config/logging/) |
| [`app.py`](file:///home/professorseanex/yugioh-server/production/main/app.py) | Entry Point | Fast launcher delegating to [`gui.app`](file:///home/professorseanex/yugioh-server/production/main/gui/app.py) |
| [`setup_wizard.py`](file:///home/professorseanex/yugioh-server/production/main/setup_wizard.py) | Entry Point | Fast launcher delegating to [`gui.setup_wizard`](file:///home/professorseanex/yugioh-server/production/main/gui/setup_wizard.py) |
| [`gui/`](file:///home/professorseanex/yugioh-server/production/main/gui/) | GUI Subsystem | Encapsulated Desktop Platform Manager, Setup Wizard, and UI assets |
| [`web/`](file:///home/professorseanex/yugioh-server/production/main/web/) | Web Service | FastAPI card catalog, deck viewer, lore portal, and expansion sync API (Port 8000) |
| [`discord_bot/`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/) | Bot Service | The Great Kasutamaiza modular Discord duel engine and card lookup bot |
| [`simulator/`](file:///home/professorseanex/yugioh-server/production/main/simulator/) | Duel Engine | Docker Compose configuration and container orchestration for live duels (Port 7911 / 7922) |
| [`assets/`](file:///home/professorseanex/yugioh-server/production/main/assets/) | Media Assets | Platform application icons, logos, and UI imagery (mirrored in `gui/assets/`) |

---

## 📜 Production Logging Architecture (`logger.py`)

All host services route events through the centralized logging subsystem:

```python
from production.main.logger import get_logger, audit_operation

logger = get_logger("catalog_service", service="WEB")
logger.info("Serving card catalog request")

with audit_operation("Rebuild CDB", service="SIMULATOR"):
    # Code executed inside is automatically timed and errors are captured
    build_cdb()
```

### Log File Destinations

* **Service Logs**: `logs/<service>.log` (e.g. `logs/web.log`, `logs/bot.log`, `logs/simulator.log`).
* **Combined Log**: `logs/combined.log` (unified timeline of all platform activity).
* **Automatic Rotation**: Files rotate at 10 MB with up to 5 historical backups (`.log.1`, `.log.2`), preventing VPS disk exhaustion.

### Environment Variable Flags

* `LOG_LEVEL`: Minimum severity to log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default: `INFO`.
* `LOG_FORMAT`: Format style (`text` with ANSI colors or `json` for automated observability pipelines).

---

## 🖥️ Administrative Desktop GUI (`app.py`)

A desktop application designed for local administration, testing, and simulator control:

* **Container Lifecycle**: One-click Start, Stop, and Restart of the live duel container.
* **Web Catalog Launcher**: Launches FastAPI and opens browser to `http://localhost:8000`.
* **Expansion Compiler**: Rebuilds binary `.cdb` and re-generates Lua effect scripts.
* **Diagnostic Audit**: Runs system failpoint assertions and displays real-time health status.
* **Log Monitor**: Streams live server logs with multi-threaded non-blocking updates.

---

## 🔗 Compatibility Symlinks

For backward compatibility with deployment scripts and automation, the following symlinks are maintained at `production/main/`:

* `deploy_oracle_cloud.sh` -> points to `packages/server/deploy_oracle_cloud.sh`
* `setup_cloudflare_tunnel.sh` -> points to `packages/server/scripts/setup_cloudflare_tunnel.sh`
* `update_duckdns.sh` -> points to `packages/server/scripts/update_duckdns.sh`
* `systemd` -> points to `packages/server/systemd/`
