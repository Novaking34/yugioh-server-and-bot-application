# 🛠️ Card Compilation & Pipeline Tools (`development/tools/`)

The `development/tools/` package contains the automated compilers, converters, and code generators responsible for transforming custom card text and metadata into simulator-ready SQLite databases and Lua effect scripts.

---

## 📁 Toolchain Manifest

| Script | Purpose | Input Source | Output Destination |
| :--- | :--- | :--- | :--- |
| [`cdb_builder.py`](file:///home/professorseanex/yugioh-server/development/tools/cdb_builder.py) | Compiles SQLite CDB binary for ocgcore | `data/authoritative/content.db` | `data/expansions/custom_cards.cdb` |
| [`constants.py`](file:///home/professorseanex/yugioh-server/development/tools/constants.py) | Centralized bitmasks, types, races, attributes | — | Exported across toolchain |
| [`debug_diagnostics.py`](file:///home/professorseanex/yugioh-server/development/tools/debug_diagnostics.py) | System auditor inspecting DB, bitmasks, CDB parity, Lua, and decks | Database, CDB, scripts, decks | Terminal report & JSON diagnostics |
| [`duelingbook_importer.py`](file:///home/professorseanex/yugioh-server/development/tools/duelingbook_importer.py) | Parses and imports Duelingbook JSON cards | Duelingbook JSON export | `content.db`, `custom_cards.cdb`, `c<id>.lua` |
| [`export_deck.py`](file:///home/professorseanex/yugioh-server/development/tools/export_deck.py) | Exports story and player decks to `.ydk` | `decks` & `player_decks` tables | `production/shared/decks/*.ydk` |
| [`lua_generator.py`](file:///home/professorseanex/yugioh-server/development/tools/lua_generator.py) | Generates syntactically valid ocgcore Lua | `custom_cards` table | `production/shared/expansions/scripts/c<id>.lua` |

---

## ⚙️ 1. SQLite CDB Compiler (`cdb_builder.py`)

Reads custom card parameters from the Story Database and packs them into the exact two-table schema required by the `ocgcore` duel engine:

* **`datas` Table**:
  * `id`: 8-digit unique passcode (e.g. `50000001`).
  * `ot`: Format flag (`4` = Custom Card).
  * `type`: Composite bitmask of card classifications (`TYPE_MONSTER | TYPE_EFFECT | TYPE_XYZ`).
  * `atk`: Attack points (`-2` for `?`).
  * `def`: Defense points (`-2` for `?`). **Note**: For Link Monsters, this column stores the Link Arrows bitmask instead of DEF.
  * `level`: Bit-packed integer containing Level, Right Scale, and Left Scale:

    ```python
    packed_level = ((left_scale << 24) | (right_scale << 16) | level)
    ```

  * `race`: Monster species/class bitmask (`RACE_WARRIOR`, `RACE_DRAGON`, etc.).
  * `attribute`: Elemental attribute bitmask (`ATTRIBUTE_LIGHT`, `ATTRIBUTE_DARK`, etc.).

* **`texts` Table**:
  * `id`: Matching passcode.
  * `name`: Card display name.
  * `desc`: Full card text. For Pendulum monsters, formats both Pendulum Effect and Monster Effect separated by dashes.
  * `str1` - `str16`: Multi-choice prompt strings referenced in Lua scripts.

### CDB Compilation Commands

```bash
python3 development/tools/cdb_builder.py
```

---

## 📜 2. Lua Script Generator (`lua_generator.py`)

Analyzes card type, subtype, and effect text using pattern matching to generate standard `c<id>.lua` effect scripts for ocgcore:

* **Procedure Generation**:
  * Xyz Monsters: `Xyz.AddProcedure(c, nil, 8, 2)` (Rank 8, 2 materials).
  * Link Monsters: `Link.AddProcedure(c, nil, 2, 2, s.lcheck)` (Link-2, arrow bindings).
  * Pendulum Monsters: `Pendulum.AddProcedure(c)` (Scale registration).
* **Effect Mechanics Scaffolding**:
  * Once-Per-Turn limits (`SetCountLimit(1, id)`).
  * Search & Detach handlers (`Duel.SendtoHand`, `Duel.DiscardDeck`).
  * Destruction and targeting protections (`EFFECT_DESTROY_REPLACE`, `EFFECT_CANNOT_BE_EFFECT_TARGET`).

### Lua Generation Commands

```bash
python3 development/tools/lua_generator.py
```

---

## 📥 3. Duelingbook Card Importer (`duelingbook_importer.py`)

Takes cards exported from Duelingbook (JSON format) and integrates them into the platform pipeline:

1. Generates a unique 8-digit passcode in the non-colliding community custom range (`50,000,000` - `59,999,999`).
2. Inserts or updates the record in `content.db`.
3. Re-indexes Full-Text Search (FTS5).
4. Automatically invokes `cdb_builder` and `lua_generator` to compile simulator assets immediately.

### Duelingbook Import Commands

```bash
# Direct execution:
python3 development/tools/duelingbook_importer.py /path/to/duelingbook_export.json

# Via Master CLI:
./manage.sh import /path/to/duelingbook_export.json
```

---

## 🎴 4. Deck Exporter (`export_deck.py`)

Extracts story character decks and Discord player decks into `.ydk` files recognized by EDOPro, YGOPro, and Duelingbook:

### Format Structure (`.ydk`)

```text
#created by Yu-Gi-Oh Story Platform
#deck: Sol Radiance - Valen Signature
#main
50000001
50000001
#extra
50000002
!side
```

### Deck Export Commands

```bash
# Export all story decks:
python3 development/tools/export_deck.py

# Export specific player deck:
./manage.sh export-player <discord_user_id>
```

---

## 🔍 5. System Diagnostic & Debugging Tool (`debug_diagnostics.py`)

A deep diagnostic auditor engineered to inspect, assert, and isolate failpoints across the entire pipeline:

* **Database & Schema**: Runs SQLite `PRAGMA integrity_check`, audits table definitions, and checks `cards_fts` synchronization.
* **Card Bitmask Diagnostics**: Audits custom cards for valid passcodes (`50,000,000` - `59,999,999`), Link arrow compass masks (`0o757` octal / `495` dec, verifying the center coordinate `0o020` is omitted), Pendulum scale bounds (`0` - `13`), and single-bit elemental attributes.
* **CDB Compilation Parity**: Asserts that `custom_cards.cdb` exists and that all custom cards from `content.db` are present in both `datas` and `texts` tables.
* **Lua Script Auditing**: Validates that all custom cards have matching `c<id>.lua` scripts with mandatory `local s, id = GetID()` and `s.initial_effect(c)` headers, plus bytecode syntax checking via `luac -p`.
* **Deck Integrity**: Audits all `.ydk` files for proper `#main`, `#extra`, and `!side` section markers and valid numeric passcodes.

### Diagnostic Execution Commands

```bash
# Run full diagnostic suite via Master CLI:
./manage.sh diagnose

# Direct execution with specific audit targets:
python3 development/tools/debug_diagnostics.py --all
python3 development/tools/debug_diagnostics.py --db
python3 development/tools/debug_diagnostics.py --cards
python3 development/tools/debug_diagnostics.py --cdb
python3 development/tools/debug_diagnostics.py --lua
python3 development/tools/debug_diagnostics.py --decks

# Machine-readable JSON output for automated pipelines:
python3 development/tools/debug_diagnostics.py --json
```
