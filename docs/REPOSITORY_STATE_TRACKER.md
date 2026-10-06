# 📊 Living Repository State Tracker

This document is the **live, tactical ledger** of the repository's current state, component audit status, active technical debt, and progress through the [**`ACTION_PLAN.md`**](file:///home/professorseanex/yugioh-server/docs/ACTION_PLAN.md).

It is designed to be updated in real time as modifications are planned, executed, and validated.

---

## 📈 1. Real-Time Repository Health Snapshot

Last audited: October 5, 2026.

| Subsystem | Metric | Current Value | Target / Ideal | Health Status |
| :--- | :--- | :--- | :--- | :--- |
| **Live Simulator** | Docker Container | `ygo-simulator-server` (Up) | Running 24/7 | 🟢 Healthy |
| **Network Ports** | TCP 7911 (Duel) | Open / Listening | Open / Listening | 🟢 Healthy |
| | TCP 7922 (Room) | Open / Listening | Open / Listening | 🟢 Healthy |
| | TCP 8000 (Web) | Offline (Starts on demand) | Available on demand | 🟡 Idle |
| **Story Database** | `custom_cards` | 64 registered | 64+ Set 1 pool | 🟢 In Parity |
| | `factions` | 8 registered | 8 canonical | 🟢 In Parity |
| | `characters` | 3 registered | 3 canonical | 🟢 In Parity |
| | `decks` | 11 registered | 11 canonical | 🟢 In Parity |
| **Expansions** | `custom_cards.cdb` | 64 cards compiled | 64 cards | 🟢 In Parity |
| | Lua Scripts | 64 valid `c<id>.lua` | 64 valid scripts | 🟢 In Parity |
| | Artwork Cache | 64 `.jpg` images | 64 images | 🟢 In Parity |
| | Deck Files (`.ydk`) | 16 files on disk | 11 canonical decks | 🔴 **Duplicate Drift** |
| **Automated Tests** | Pytest Suite | 112 passed (in venv) | 100% passing | 🟢 Passing |
| **Diagnostics** | Auditor Check | 215 items audited | Full 14-table audit | 🟡 **Needs Table Scope** |

---

## 🔍 2. Component & Silo Audit Matrix

| Silo / Domain | Component | Current State | Target State | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Silo 1: Card Engine** | `constants.py` | Standalone bitmask constants in `development/tools/` | Extracted into shared `common/ygo_core` | `PENDING` |
| | Card Parser | Fragmented across CDB builder, Duelingbook importer, tracker sync | Unified pure parser in `common/ygo_core` | `PENDING` |
| **Silo 2: Compilation** | `cdb_builder.py` | Batch CLI script compiling all 64 cards | Exposes both batch CLI and single-card delta API | `PENDING` |
| | `lua_generator.py` | Batch CLI generating all 64 scripts | Exposes both batch CLI and on-demand generator | `PENDING` |
| | `export_deck.py` | Produces sanitized names with double spaces | Canonical exporter synced with `decks.json` | `PENDING` |
| **Silo 3: Match & ELO** | ELO Math | Mixed inside Discord `services/rating/` | Pure math functional core | `PENDING` |
| | Telemetry | Dual recording in `card_usage_stats` and `player_saved_decks` | Unified transactional telemetry repository | `PENDING` |
| **Silo 4: Application** | Discord Bot Services | Dual structure: `.py` files alongside subpackages | Pruned legacy `.py` files; subpackages only | `PENDING` |
| | Web REST API | Fast, but lacks automatic compilation trigger | Triggers CDB & Lua recompile on `POST /api/cards` | `PENDING` |
| | Diagnostics | Checks only 6 of 14 database tables | Audits all 14 database tables | `PENDING` |

---

## 📋 3. Active Task Execution Checklist

### Phase 1: Condensation & Redundancy Pruning

- [x] **1.1** Clean root directory: remove duplicate root tracker CSV, eliminate empty root `scripts/`, move `sync_oracle_vm.sh` to `packages/server/scripts/`, and formalize path configs. *(Completed)*
- [x] **1.2** Upgrade all root files (`setup.py`, `manage.py`, `manage.sh`, `manage.bat`, `.env`, `.env.example`, `.gitignore`, `pyproject.toml`, `requirements.txt`, `docker-compose.yml`) to strict C-style 4-block compilation unit structure. *(Completed)*
- [x] **1.3** Update root `README.md` to reflect the 3-application architecture, docs suite, canonical trackers, and 4-block structure. *(Completed)*
- [x] **1.4** Unify all platform data into single canonical `data/` subsystem (`authoritative/`, `trackers/`, `artwork/`, `expansions/`, `decks/`, `simulator/`) and re-anchor all affected code. *(Completed)*
- [x] **1.5** Author foundational architectural specifications: [`docs/DATA_ARCHITECTURE.md`](file:///home/professorseanex/yugioh-server/docs/DATA_ARCHITECTURE.md) (six-tier data hierarchy and ingestion pipelines) and [`docs/CONFIGURATION_SYSTEM.md`](file:///home/professorseanex/yugioh-server/docs/CONFIGURATION_SYSTEM.md) (configuration precedence, dataclass schemas, logging, and debugger pairing). *(Completed)*
- [ ] **1.6** Retire duplicate Discord bot service forwarders (`card.py`, `deck.py`, `duel.py`, `rating.py`, `story.py`, `utils.py`).
- [ ] **1.7** Deduplicate `.ydk` deck files in `data/decks/` and synchronize naming with `decks.json`.
- [ ] **1.8** Clean up symlinks in `production/shared/` and `production/main/`.

### Phase 2: Schema Realignment & Diagnostic Expansion

- [ ] **2.1** Add `player_saved_decks` table to `data/authoritative/schema.sql`.
- [x] **2.2** Expand `debug_diagnostics.py` and `config/debugger/diagnostics.py` to audit all 14 database tables. *(Completed)*
- [x] **2.3** Clean up stale URL fallbacks in `packages/client/config.json`. *(Completed)*

### Phase 3: Core Utility Extraction (`common/ygo_core`)

- [ ] **3.1** Build immutable `CardDataStruct` and pure bitmask encoders/decoders.
- [ ] **3.2** Refactor `cdb_builder`, `lua_generator`, `duelingbook_importer`, and `tracker_sync` to use `common/ygo_core`.

### Phase 4: Bi-Directional Pipeline & Repository Abstraction

- [ ] **4.1** Implement unified sync/async database repository (`config/database.py`).
- [ ] **4.2** Expose programmatic compilation hooks for on-demand artifact generation.
- [ ] **4.3** Wire live mutation triggers into Web API and Discord Bot.

### Phase 5: Simulator Protocol & Replay Telemetry

- [ ] **5.1** Implement Room Manager HTTP API client (port 7922).
- [ ] **5.2** Implement `.yrp` replay parser for automated match outcome extraction.

### Phase 6: Verification & Release Packaging

- [ ] **6.1** Run full unit test suite (`./manage.sh test`).
- [ ] **6.2** Validate all Lua bytecode (`./manage.sh validate-lua`).
- [ ] **6.3** Verify 0 failpoints in platform diagnostics (`./manage.sh diagnose`).
- [ ] **6.4** Build and verify distribution release packages (`./manage.sh package`).

---

## ⚠️ 4. Technical Debt & Inconsistency Register

| ID | Severity | Location | Description | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **DEBT-01** | Medium | `production/main/discord_bot/services/` | Duplicate files: `card.py`, `deck.py`, `duel.py`, `rating.py`, `story.py` coexist with directories of the same name. | Remove single-file shims; verify `__init__.py` in packages. |
| **DEBT-02** | High | `data/authoritative/schema.sql` | `player_saved_decks` table is missing from `schema.sql`, leading to schema drift on fresh installs. | Add table definition to `schema.sql` and update seeder. |
| **DEBT-03** | Medium | `config/debugger/diagnostics.py` | Database auditing must check both two-tier stores (`content.db` and `telemetry.db`). | **RESOLVED**: Partitioned into two-tier auditing across 11 content tables and 6 telemetry tables. All 17 tables and FTS5 verified passing. |
| **DEBT-04** | Low | Root workspace | `Duelingbook Master Tracker - Set 1 - The Land of Kustomazi.csv` is an exact duplicate of file in `development/trackers/`. | **RESOLVED**: Removed root duplicate; all tools re-anchored to `TRACKERS_DIR`. |
| **DEBT-05** | Low | `data/decks/` | 16 `.ydk` files exist for 11 decks due to conflicting sanitization rules. | Prune duplicate/orphaned `.ydk` files; standardize names. |
| **DEBT-06** | Low | `packages/client/config.json` | Contains expired `*.trycloudflare.com` URL. | **RESOLVED**: Removed expired ephemeral tunnel URL; pinned authoritative domain and DuckDNS fallback. |

---

## 📝 5. Session Log & Revision History

| Timestamp | Actor | Action / Changes | Result |
| :--- | :--- | :--- | :--- |
| `2026-10-05 13:40` | Pair Session | Full repository audit & architectural analysis performed. | Identified schema drift, service duplicates, and deck naming inconsistencies. |
| `2026-10-05 14:05` | Pair Session | Created `docs/` architecture foundation: `README.md`, `ARCHITECTURE_PHILOSOPHY.md`, `ACTION_PLAN.md`, `REPOSITORY_STATE_TRACKER.md`. | Established formal systems engineering doctrine, phased action plan, and living state tracker. |
| `2026-10-05 14:26` | Pair Session | Cleaned and aligned project root directory: removed root CSV mirror, moved `sync_oracle_vm.sh` to `packages/server/scripts/`, formalized `RAW_CARD_ART_DIR` & `DOCS_DIR` in `config/paths.py`, pruned `egg-info`. | Pristine project root established; all 112 pytest unit tests passing. |
| `2026-10-05 14:50` | Pair Session | Upgraded root configuration and environment files (`setup.py`, `manage.py`, `manage.sh`, `.env`, `.env.example`, `.gitignore`, `pyproject.toml`, `requirements.txt`, `docker-compose.yml`) to 4-block compilation units. | Root compilation unit architecture established. |
| `2026-10-05 15:20` | Pair Session | Unified platform data into centralized `data/` subsystem (`authoritative/`, `trackers/`, `artwork/`, `expansions/`, `decks/`, `simulator/`). Re-anchored database, CDB builder, Lua generator, Duelingbook importer, tracker sync, and documentation. | Zero redundant data copies; single source of truth across all tools. |
| `2026-10-05 15:50` | Pair Session | Authored foundational architectural documentation: [`DATA_ARCHITECTURE.md`](file:///home/professorseanex/yugioh-server/docs/DATA_ARCHITECTURE.md) and [`CONFIGURATION_SYSTEM.md`](file:///home/professorseanex/yugioh-server/docs/CONFIGURATION_SYSTEM.md). | Comprehensive 6-tier storage and 5-tier configuration precedence documented. |
| `2026-10-05 16:30` | Pair Session | Comprehensive Configuration & Telemetry sweep: created [`config/game_rules.py`](file:///home/professorseanex/yugioh-server/config/game_rules.py), upgraded [`config/settings.py`](file:///home/professorseanex/yugioh-server/config/settings.py) (typed dataclasses with `DatabaseConfig` & `DebugConfig`), structured [`config/logging/`](file:///home/professorseanex/yugioh-server/config/logging/), built [`config/debugger/`](file:///home/professorseanex/yugioh-server/config/debugger/) (tracer + 14-table diagnostics), resolved **DEBT-03** & **DEBT-06**, upgraded [`config/__init__.py`](file:///home/professorseanex/yugioh-server/config/__init__.py). | All 289 diagnostic checks pass; all 112 pytest tests green (1.9s). |
