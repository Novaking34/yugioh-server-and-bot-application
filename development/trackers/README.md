# 📊 Yu-Gi-Oh! Master Card Tracker & Google Sheets Guide

This directory houses the master spreadsheet trackers for custom card sets, designed for seamless bidirectional synchronization with Google Sheets, the SQLite story database (`ygo_story.db`), the simulator binary CDB (`custom_cards.cdb`), and local card artwork.

---

## 📁 Available Formats

| File | Description | Recommended Google Sheets Import Method |
| :--- | :--- | :--- |
| [`Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv`](file:///home/professorseanex/yugioh-server/development/trackers/Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv) | Full RFC 4180 CSV with escaped quotes | **File -> Import -> Upload** |
| [`Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv`](file:///home/professorseanex/yugioh-server/development/trackers/Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv) | Tab-separated values file | **Copy all text & Paste directly into Sheet** |
| [`Duelingbook Master Tracker - Set 1 - The Land of Kustomazi.csv`](file:///home/professorseanex/yugioh-server/Duelingbook%20Master%20Tracker%20-%20Set%201%20-%20The%20Land%20of%20Kustomazi.csv) | Workspace root mirror | Legacy path mirror |

---

## 🚀 How to Upload into Google Sheets

### Method A: Direct File Upload (Recommended)

1. Open [Google Sheets](https://sheets.new) and create a new blank spreadsheet.
2. Click **File** > **Import** > **Upload**.
3. Select `Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv`.
4. In the import settings dialog:
   * **Import location**: *Replace spreadsheet*
   * **Separator type**: *Detect automatically* (or *Comma*)
   * **Convert text to numbers, dates, and formulas**: **YES** (Checked)
5. Click **Import data**.

### Method B: Fast Copy & Paste (via TSV)

1. Open `Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv` in any text editor.
2. Select all (`Ctrl+A` / `Cmd+A`) and copy (`Ctrl+C` / `Cmd+C`).
3. Click cell `A1` in Google Sheets and paste (`Ctrl+V` / `Cmd+V`).
4. Google Sheets will automatically split the columns and evaluate the `=IMAGE(...)` formula!

---

## 🖼️ Google Sheets `=IMAGE(...)` Formula

Column D (`Image Preview`) contains the formula:

```excel
=IF(ISBLANK(E2), "", IMAGE(E2))
```

When imported into Google Sheets:

* Google Sheets automatically fetches the artwork from the URL in Column E (`Image Link`) and renders it directly inside the spreadsheet cell!
* To enlarge the preview, simply increase the row height in Google Sheets (e.g., select rows > right-click > *Resize rows* > set to 80-120 pixels).

---

## 📋 Schema Mapping: Tracker Columns vs Database & Simulator

Every column in the Master Tracker maps 1:1 to platform subsystems:

| # | Column Header | Data Type | SQLite Column (`custom_cards`) | ocgcore Simulator CDB | Purpose |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **A** | `Passcode (ID)` | Integer | `id` (PRIMARY KEY) | `datas.id`, `texts.id` | 8-digit unique card passcode (e.g. `50000101`) |
| **B** | `Set Number` | Text | `set_number` | - | Card set identifier (e.g. `TLOK-001`) |
| **C** | `Card Name` | Text | `name` | `texts.name` | Display card title |
| **D** | `Image Preview` | Formula | - | - | `=IF(ISBLANK(E2), "", IMAGE(E2))` visual preview |
| **E** | `Image Link` | URL | `image_url` | - | Duelingbook remote artwork URL |
| **F** | `Local Image File` | Path | `local_image_path` | `pics/<id>.jpg` | Local file path for EDOPro / simulator |
| **G** | `Image Status` | Text | - | - | `Downloaded` or `Pending` |
| **H** | `Card Category` | Text | `card_type` | `datas.type` (primary) | `Monster`, `Spell`, or `Trap` |
| **I** | `Card Subtype` | Text | `card_subtype` | `datas.type` (subtype) | `Normal`, `Effect`, `Fusion`, `Quick-Play`, `Counter`, etc. |
| **J** | `Monster Race` | Text | `monster_type` | `datas.race` | `Divine-Beast`, `Warrior`, `Dragon`, `Spellcaster`, etc. |
| **K** | `Attribute` | Text | `attribute` | `datas.attribute` | `DIVINE`, `DARK`, `LIGHT`, `EARTH`, `WATER`, `FIRE`, `WIND` |
| **L** | `Level/Rank/Link` | Integer | `level_or_rank_or_link` | `datas.level` | Monster Level / Rank / Link Rating |
| **M** | `ATK` | Number | `atk` | `datas.atk` | Attack stat (`-2` for `?`) |
| **N** | `DEF` | Number | `def` | `datas.def` | Defense stat (`-2` for `?`, or Link arrows bitmask) |
| **O** | `Pendulum Scale` | Integer | `scale` | `datas.level` (bit-packed) | Scale rating (0-13) |
| **P** | `Link Arrows` | Text | `link_arrows` | `datas.def` (Link bitmask) | Link markers (e.g. `BL,BR`) |
| **Q** | `Effect Text` | Text | `effect_text` | `texts.desc` | Rules text or flavor lore |
| **R** | `Pendulum Effect` | Text | `pendulum_effect` | `texts.desc` | Pendulum spell box text |
| **S** | `Archetype/Series` | Text | `archetype` | `datas.setcode` | Primary series (e.g. `Kasutamaiza`, `Fusion Card`) |
| **T** | `Rarity` | Text | `rarity` | - | Printing rarity (`Ultra Rare`, `Common`, etc.) |
| **U** | `Creator` | Text | `creator_name` | - | Card designer (`ProfessorSeanEX`) |
| **V** | `Faction Alignment` | Text | `faction_id` (FK) | - | In-universe lore faction (`The Creators of Kustomazi`) |
| **W** | `Signature Duelist` | Text | `signature_character_id` | - | Signature duelist (`ProfessorSeanEX`) |
| **X** | `Story Significance` | Text | `story_significance` | - | Role (`Creator Deity`, `Core Engine`, `Boss`) |
| **Y** | `Story/Lore Context` | Text | `lore_text` | - | Extended background narrative |
| **Z** | `Synergy/Combos` | Text | - | - | Key gameplay combos and search targets |
| **AA** | `Designer Notes` | Text | - | - | Design philosophy, rulings, and erratas |
| **AB** | `Duelingbook Card ID` | Text | `duelingbook_id` | - | Internal Duelingbook card serial (e.g. `2282769`) |
| **AC** | `Script File` | Text | `script_file` | `expansions/scripts/` | Lua effect script (e.g. `c50000101.lua`) |
| **AD** | `Script Status` | Text | `script_status` | - | `Implemented`, `Draft`, `Stub`, `Vanilla` |
| **AE** | `CDB Bitmask Type` | Hex | - | `datas.type` | Binary classification bitmask (e.g. `0x21`, `0x60002`) |
| **AF** | `Banlist Status` | Text | `banlist_status` | - | `Unlimited`, `Semi-Limited`, `Limited`, `Forbidden` |
| **AG** | `Playtesting Status` | Text | `playtesting_status` | - | `In Testing`, `Approved`, `Needs Revision` |

---

## 🛠️ Synchronization Tool CLI Commands

The synchronization tool [`development/tools/tracker_sync.py`](file:///home/professorseanex/yugioh-server/development/tools/tracker_sync.py) provides turn-key synchronization:

```bash
# 1. Regenerate and upgrade the Master Tracker CSV and TSV:
python3 development/tools/tracker_sync.py upgrade

# 2. Synchronize all cards from the tracker into the SQLite story database:
python3 development/tools/tracker_sync.py import

# 3. Automatically download card artwork into production/shared/expansions/pics/:
python3 development/tools/tracker_sync.py download-images

# 4. Verify tracker parity and asset integrity:
python3 development/tools/tracker_sync.py verify

# 5. Compile SQLite database into custom_cards.cdb and generate Lua scripts:
./manage.sh sync
```
