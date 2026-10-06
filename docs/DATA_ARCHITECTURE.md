# 💾 Master Data Architecture & Pipeline Specification

This document serves as the authoritative architectural blueprint for the unified **Data Subsystem** (`data/`) across the Yu-Gi-Oh! Story, Bot, and Live Duel Simulator Platform.

It details storage tiers, schema relationships, data lifecycle pipelines, immutability rules, and cross-application consumption contracts.

---

## 🏗️ 1. Architectural Philosophy: The Data Hierarchy

In accordance with [`docs/ARCHITECTURE_PHILOSOPHY.md`](file:///home/professorseanex/yugioh-server/docs/ARCHITECTURE_PHILOSOPHY.md), application code and runtime logic must be decoupled from persistent state. Data is organized into **six strictly segregated tiers**:

```text
                       ┌─────────────────────────────────────┐
                       │  TIER 1: AUTHORITATIVE & TELEMETRY  │
                       │(content.db & telemetry.db)          │
                       └──────────────────┬──────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
      ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
      │   TIER 2: TRACKERS    │ │  TIER 3: ARTWORK  │ │  TIER 4: EXPANSIONS   │
      │   (data/trackers/)    │ │(data/artwork/raw/)│ │  (data/expansions/)   │
      │ Master CSV/TSV Sheets │ │ Master Raw Images │ │ CDB SQLite + Lua + Pic│
      └───────────────────────┘ └───────────────────┘ └───────────┬───────────┘
                                                                  │
                                  ┌───────────────────────────────┴──────────┐
                                  ▼                                          ▼
                      ┌───────────────────────┐                  ┌───────────────────────┐
                      │    TIER 5: DECKS      │                  │   TIER 6: SIMULATOR   │
                      │    (data/decks/)      │                  │   (data/simulator/)   │
                      │  Canonical .ydk Files │                  │ Engine Config & .yrp  │
                      └───────────────────────┘                  └───────────────────────┘
```

---

## 📁 2. Data Subsystem Directory Layout

```bash
data/
├── authoritative/                     # TIER 1: Master Content Relational Store & Schemas
│   ├── content.db                     # Canonical SQLite content database (WAL mode, foreign keys)
│   ├── schema_content.sql             # Content DDL defining 11 relational tables + FTS5
│   ├── schema.sql                     # Full composite DDL defining 17 relational tables
│   ├── seed_databases.py              # Idempotent two-tier database seeder
│   └── README.md                      # Schema documentation & query guides
├── telemetry/                         # TIER 1b: Dynamic Telemetry & Runtime Player Store
│   ├── telemetry.db                   # High-churn player ratings, matches, and deck slots
│   └── schema_telemetry.sql           # Dynamic telemetry DDL defining 6 relational tables
├── trackers/                          # TIER 2: Master Spreadsheets & Ingestion Data
│   ├── Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv  # RFC 4180 CSV with =IMAGE()
│   ├── Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv  # Tab-separated spreadsheet format
│   └── README.md                      # Google Sheets integration & formula documentation
├── artwork/                           # TIER 3: Master Raw High-Resolution Artwork
│   └── raw/                           # Uncompressed master artwork organized by archetype
│       ├── Kasutamaiza/               # Archetype character and monster illustrations
│       └── Generics/                  # Generic spells, traps, and boss artwork
├── expansions/                        # TIER 4: Compiled Game Engine Binary Expansions
│   ├── custom_cards.cdb               # Binary SQLite CDB matching ocgcore specifications
│   ├── scripts/                       # 64 Lua effect scripts (c<passcode>.lua)
│   └── pics/                          # 64 Local JPEG card artwork files (<passcode>.jpg)
│       └── thumbnail/                 # 64 Downscaled web & bot card thumbnails
├── decks/                             # TIER 5: Pre-Made Story & Character Decks
│   ├── *.ydk                          # Canonical character story decks (e.g. Kasutamaiza.ydk)
│   └── renders/                       # 10-column composite visual canvas renders (.png)
└── simulator/                         # TIER 6: Duel Engine Configuration & Telemetry
    ├── config/                        # Live container engine configuration (mounted into Docker)
    │   ├── config.json                # Server network ports, banlist rules, timeouts
    │   ├── admin_user.json            # Simulator in-game administrator credentials
    │   ├── badwords.json              # Chat profanity filters
    │   ├── dialogues.json             # In-duel character banter & NPC quotes
    │   ├── tips.json                  # Loading screen lore tips
    │   └── README.md                  # Container mount & restart instructions
    └── replays/                       # Live duel match recordings
        └── *.yrp                      # Binary ocgcore match replays
```

---

## 🗄️ 3. Tier Specifications & Invariants

### Tier 1: Authoritative Relational Store ([`data/authoritative/`](file:///home/professorseanex/yugioh-server/data/authoritative/))

* **Primary Store**: [`content.db`](file:///home/professorseanex/yugioh-server/data/authoritative/content.db) (Content) & [`telemetry.db`](file:///home/professorseanex/yugioh-server/data/telemetry/telemetry.db) (Telemetry)
* **Design Pattern**: Two-Tier Partitioned Store for card stats, narrative lore, faction alignments, duelist dossiers, match histories, and player inventories.
* **Schema Integrity**: Defined in [`schema_content.sql`](file:///home/professorseanex/yugioh-server/data/authoritative/schema_content.sql) and [`schema_telemetry.sql`](file:///home/professorseanex/yugioh-server/data/authoritative/schema_telemetry.sql).
  * 14 relational tables: `factions`, `characters`, `cards`, `custom_cards`, `decks`, `deck_cards`, `stories`, `story_stages`, `player_profiles`, `player_decks`, `player_saved_decks`, `player_inventory`, `matches`, `card_usage_stats`.
  * `PRAGMA foreign_keys = ON;` strictly enforced.
  * Full-text search (FTS5) virtual tables for lightning-fast card name, effect, and lore queries.

### Tier 2: Master Trackers ([`data/trackers/`](file:///home/professorseanex/yugioh-server/data/trackers/))

* **Primary Stores**: Master CSV and TSV spreadsheets.
* **Design Pattern**: Human-collaborative bridge between card designers (working in Google Sheets / Excel) and the database engine.
* **Invariants**:
  * Column D contains dynamic `=IMAGE("https://www.duelingbook.com/images/low-res-cards/" & C<row> & ".jpg")` formulas.
  * 1:1 parity with `custom_cards` table in Tier 1.

### Tier 3: Raw Card Artwork ([`data/artwork/raw/`](file:///home/professorseanex/yugioh-server/data/artwork/raw/))

* **Design Pattern**: Archival storage of original high-resolution artwork before compression or cropping.
* **Resolution**: Replaces the old loose root directory `card-art/`.

### Tier 4: Compiled Engine Expansions ([`data/expansions/`](file:///home/professorseanex/yugioh-server/data/expansions/))

* **Design Pattern**: The exact filesystem format required by the **EDOPro / ocgcore** simulation engine:
  1. `custom_cards.cdb`: SQLite binary database containing `datas` table (bitmasks, stats) and `texts` table (name, description, strings).
  2. `scripts/c<id>.lua`: Syntactically validated Lua 5.3 scripts implementing card effects.
  3. `pics/<id>.jpg`: 421x614 JPEG card artwork displayed inside the duel field.

### Tier 5: Canonical Decks ([`data/decks/`](file:///home/professorseanex/yugioh-server/data/decks/))

* **Design Pattern**: Official Master Rule 5 `.ydk` deck format.
* **Sections**: `#main` (40-60 cards), `#extra` (up to 15 cards), `!side` (up to 15 cards).
* **Render Cache**: `data/decks/renders/` holds pre-rendered 10-column visual images generated by Pillow for instant Discord / Web display.

### Tier 6: Simulator Datasets ([`data/simulator/`](file:///home/professorseanex/yugioh-server/data/simulator/))

* **Design Pattern**: Live ocgcore runtime configuration and persistent match telemetry.
* **Container Mount**: Mounted directly via `docker-compose.yml` into `/ygoserver/config` and `/ygoserver/replays`.

---

## 🔄 4. Data Lifecycle & Ingestion Pipelines

```text
[Duelingbook / Designer]
          │
          ▼
   Master Tracker CSV / Duelingbook Export JSON
          │
          ▼  (./manage.sh import OR ./manage.sh tracker import)
┌────────────────────────────────────────────────────────┐
│ 1. VALIDATE & SANITIZE                                 │
│    - Assert Passcode Range: 50000000 <= id <= 99999999 │
│    - Compute Bitmasks: Type, Attribute, Race, Link     │
└─────────────────────────┬──────────────────────────────┘
                          ▼
┌────────────────────────────────────────────────────────┐
│ 2. AUTHORITATIVE PERSISTENCE                           │
│    - INSERT / UPDATE INTO content.db (custom_cards)    │
│    - Auto-link Factions & Characters                   │
└─────────────────────────┬──────────────────────────────┘
                          ▼
┌────────────────────────────────────────────────────────┐
│ 3. COMPILATION & GENERATION                            │
│    - Rebuild data/expansions/custom_cards.cdb          │
│    - Render data/expansions/scripts/c<id>.lua          │
│    - Cache Artwork to data/expansions/pics/<id>.jpg    │
└─────────────────────────┬──────────────────────────────┘
                          ▼
┌────────────────────────────────────────────────────────┐
│ 4. CONSUMPTION ACROSS ECOSYSTEM                        │
│    - Live Simulator: Container live-reads new CDB      │
│    - Discord Bot: Autocomplete instantly reflects card │
│    - Web Catalog: Card immediately visible at port 8000│
│    - Client Sync: Downloadable via /api/shared/cdb     │
└────────────────────────────────────────────────────────┘
```

---

## 🛡️ 5. Data Invariants & Security Boundaries

1. **Passcode Range Guarantee**:
   * All custom cards strictly reside within the custom passcode partition: `50000000` through `99999999`.
   * Standard passcodes (`< 50000000`) are reserved for official Konami / OCG cards.
2. **Bitmask Orthogonality**:
   * Card types must follow power-of-two bitflags (e.g. `TYPE_MONSTER = 0x1`, `TYPE_SPELL = 0x2`, `TYPE_TRAP = 0x4`).
   * Attributes are strictly mutually exclusive powers of two (`0x01` through `0x40`).
3. **Transaction Safety**:
   * Database writes must use ACID-compliant transactions with `IMMEDIATE` lock acquisition to avoid `database is locked` concurrency errors.
4. **Data vs Config Separation**:
   * No static configuration variables (ports, tokens, timeouts) may be stored in `data/`.
   * No mutable application state may be written into `config/`.
