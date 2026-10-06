# 🛠️ Action Plan: Repository Modernization & Architecture Realignment

This document outlines the concrete, phased execution roadmap to modernize, condense, and realign the **Yu-Gi-Oh! Custom Card, Story & Simulator Platform** with the principles defined in [**`ARCHITECTURE_PHILOSOPHY.md`**](file:///home/professorseanex/yugioh-server/docs/ARCHITECTURE_PHILOSOPHY.md).

---

## 🎯 Executive Summary & Objectives

1. **Condense Redundancies:** Eliminate duplicate shim files in the Discord bot services, remove mirrored CSV trackers, prune divergent deck names, and streamline symlinks.
2. **Re-Align Schemas & Diagnostics:** Synchronize the database schema with active application state (`player_saved_decks`) and expand system diagnostics to audit all 14 platform tables.
3. **Extract Shared Functional Core (`common/ygo_core`):** Centralize card models, pure bitmask arithmetic, and rules parsers into a unified, zero-dependency library shared across all tools and applications.
4. **Wire Bi-Directional Pipelines:** Transition batch compilation scripts into service-callable APIs so that actions taken in Discord or on the Web automatically recompile artifacts (`.cdb`, `.lua`, `.ydk`) and update simulator state.
5. **Verify & Package:** Ensure all unit tests pass, diagnostic auditors report 100% green, and release packages build deterministically.

---

## 📅 Phased Execution Roadmap

### Phase 1: Condensation & Redundancy Pruning

*Goal: Eliminate dead code, redundant file shims, and file system duplicates.*

* [ ] **Task 1.1: Retire Legacy Discord Bot Service Shims**
  * Verify that all subpackages in [`production/main/discord_bot/services/`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/services/) (`card/`, `deck/`, `duel/`, `rating/`, `story/`) have complete `__init__.py` interface contracts.
  * Remove redundant single-file shims: `card.py`, `deck.py`, `duel.py`, `rating.py`, and `story.py`.
  * Retire [`production/main/discord_bot/utils.py`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/utils.py) in favor of the modular `utils/` package.
* [x] **Task 1.2: Consolidate Master Trackers** *(Completed)*
  * Remove the duplicate root tracker: `Duelingbook Master Tracker - Set 1 - The Land of Kustomazi.csv`.
  * Update [`tracker_sync.py`](file:///home/professorseanex/yugioh-server/development/tools/tracker_sync.py) and [`seed_databases.py`](file:///home/professorseanex/yugioh-server/data/authoritative/seed_databases.py) to reference the canonical path via `config.paths.TRACKERS_DIR`.
* [ ] **Task 1.3: Deduplicate and Normalize Deck Files**
  * Review all `.ydk` files in [`production/shared/decks/`](file:///home/professorseanex/yugioh-server/production/shared/decks/).
  * Eliminate duplicate files created by divergent sanitization (e.g. `'Base of Story Kas.ydk'` vs `'Base of Story (Kas.).ydk'`).
  * Normalize deck filenames to match [`production/main/discord_bot/data/story/decks.json`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/data/story/decks.json).
* [ ] **Task 1.4: Normalize Package & Symlink Structure**
  * Ensure `packages/client/` and `packages/server/` serve as the canonical source of release code.
  * Ensure `./manage.sh package` bundles directly from canonical package roots without relying on fragile filesystem symlinks.

---

### Phase 2: Schema Realignment & Diagnostic Expansion

*Goal: Bring database schemas, seeder logic, and diagnostic auditing into 100% parity with runtime requirements.*

* [ ] **Task 2.1: Add `player_saved_decks` to Authoritative Schema**
  * Add the `player_saved_decks` table definition (including macro telemetry columns: `times_used`, `wins`, `losses`, `last_used_at`) directly into [`development/database/schema.sql`](file:///home/professorseanex/yugioh-server/development/database/schema.sql).
  * Ensure [`seed_databases.py`](file:///home/professorseanex/yugioh-server/data/authoritative/seed_databases.py) creates all required tables on fresh installation.
* [ ] **Task 2.2: Expand Platform Diagnostic Auditor**
  * Expand [`PlatformDiagnostics.audit_database`](file:///home/professorseanex/yugioh-server/development/tools/debug_diagnostics.py#L110) in [`debug_diagnostics.py`](file:///home/professorseanex/yugioh-server/development/tools/debug_diagnostics.py) to audit all 14 active tables:
    * `custom_cards`, `factions`, `worldbuilding_elements`, `characters`, `decks`, `deck_cards`, `cards_fts`, `player_ratings`, `duel_matches`, `card_usage_stats`, `story_chapters`, `story_stages`, `player_story_progress`, `player_saved_decks`.
* [ ] **Task 2.3: Clean Up Stale Endpoint URLs & Docstrings**
  * Update [`packages/client/config.json`](file:///home/professorseanex/yugioh-server/packages/client/config.json) to remove obsolete ephemeral tunnel URLs.
  * Update outdated docstrings in [`production/main/web/api_server.py`](file:///home/professorseanex/yugioh-server/production/main/web/api_server.py).

---

### Phase 3: Core Utility Extraction (The Shared Functional Core)

*Goal: Extract all card math, bitmask encoders, and validation logic into an authoritative, zero-dependency domain package.*

* [ ] **Task 3.1: Create `common/ygo_core` (or `development/tools/core`)**
  * Define immutable `@dataclass(frozen=True) class CardDataStruct` matching C/C++ `struct card_data`.
  * Centralize pure bitmask conversion functions:
    * `encode_card_type(types: List[str]) -> int`
    * `encode_attribute(attr: str) -> int`
    * `encode_race(race: str) -> int`
    * `encode_link_arrows(arrows: str) -> int`
    * `decode_bitmasks(data: CardDataStruct) -> Dict[str, Any]`
  * Implement pure card effect text tokenizer (OPT clause detection, activation cost vs effect delimiters).
* [ ] **Task 3.2: Refactor Downstream Tools to Consume the Core**
  * Refactor [`cdb_builder.py`](file:///home/professorseanex/yugioh-server/development/tools/cdb_builder.py), [`lua_generator.py`](file:///home/professorseanex/yugioh-server/development/tools/lua_generator.py), [`duelingbook_importer.py`](file:///home/professorseanex/yugioh-server/development/tools/duelingbook_importer.py), and [`tracker_sync.py`](file:///home/professorseanex/yugioh-server/development/tools/tracker_sync.py) to import from `common/ygo_core`.
  * Ensure full test coverage and eliminate parallel constant definitions in Discord bot utils.

---

### Phase 4: Bi-Directional Pipeline & Repository Abstraction

*Goal: Enable application layer actions to safely write data and programmatically trigger compiler updates.*

* [ ] **Task 4.1: Unified Database Repository (`config/database.py`)**
  * Provide synchronous database session context manager (`get_db_session()`) for CLI tools, generators, and FastAPI.
  * Provide asynchronous database session manager (`get_async_db()`) for Discord bot cogs.
  * Standardize transactional boundaries and connection pooling.
* [ ] **Task 4.2: Programmatic Pipeline Interfaces**
  * Expose programmatic entry points:
    * `compile_card(card_data) -> Tuple[bool, str]`: Compiles single card delta into `.cdb` and generates `.lua`.
    * `export_deck_to_ydk(deck_id, output_path) -> str`: Serializes deck to `.ydk` stream.
* [ ] **Task 4.3: Wire Live Application Triggers**
  * Connect FastAPI `POST /api/cards` to the programmatic card compilation pipeline.
  * Connect Discord bot deck saving (`/mydeck save`) to immediate `.ydk` export.
  * Connect match resolution (`/duel`) to `card_usage_stats` telemetry and ELO rating updates.

---

### Phase 5: Simulator Protocol & Replay Telemetry

*Goal: Deepen integration with the live ocgcore Docker engine.*

* [ ] **Task 5.1: Room Manager API Client**
  * Implement client interacting with the simulator container's HTTP port 7922 (active rooms, player count, match states).
* [ ] **Task 5.2: Replay (`.yrp`) Parser**
  * Implement parser for replays generated in [`production/main/simulator/replays/`](file:///home/professorseanex/yugioh-server/production/main/simulator/replays/) to auto-extract match results.

---

### Phase 6: Verification & Release Packaging

*Goal: Ensure end-to-end platform integrity and build verified release artifacts.*

* [ ] **Task 6.1: Run Full Pytest Suite**
  * Execute `./manage.sh test` and ensure all existing and new tests pass.
* [ ] **Task 6.2: Validate Lua Bytecode**
  * Run `./manage.sh validate-lua` across all generated scripts.
* [ ] **Task 6.3: Run Diagnostic Auditor**
  * Run `./manage.sh diagnose` and ensure 0 failpoints and 0 warnings.
* [ ] **Task 6.4: Build Distribution Packages**
  * Run `./manage.sh package` and verify integrity checksums in `dist/SHA256SUMS.txt`.
