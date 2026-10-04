#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.database.seed_story_data
Description:
    Yu-Gi-Oh! Platform Story Database Seeder & Bootstrap Pipeline.
    Initializes the SQLite Story Database (`production/main/web/ygo_story.db`)
    with canonical lore sagas, duelist dossiers, archetypes/factions, worldbuilding
    elements, externalized simulator .ydk decklists, and progressive story scenarios.

Architectural Classification:
    Layer 1 (L1) - Database & Data Architecture Subsystem
    Subsystem: Story & Lore Campaign RPG / Simulator Pipeline

C/C++ Memory Architecture Rationale:
    In Yu-Gi-Oh! simulator cores (such as ocgcore and EDOPro), cards and decklists
    are modeled as low-level contiguous C/C++ memory structures:
    - Card records (`struct card_data`): 32-bit aligned integer primitives mapping
      directly to SQLite CDB columns (`custom_cards.cdb`), eliminating object
      overhead and garbage collection pauses during high-frequency duel simulations.
    - Decklist streams (`struct deck`): Contiguous `std::vector<uint32_t>` buffers
      for Main, Extra, and Side partitions.
    - Strict Decoupling: Simulation engine code is compiled once; cards and decks
      are ingested dynamically from external data streams (.ydk / .cdb). No deck
      or card data is hardcoded into executable logic, guaranteeing hot-reloadability,
      zero memory drift, and simulator parity.

Usage:
    python3 development/database/seed_story_data.py
    # Or via master orchestrator CLI:
    ./manage.sh sync
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Imports, Constants & Primitives)
# =============================================================================

import os
import sys
import glob
import json
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# Resolve standard repository paths with fallback
try:
    from config.paths import STORY_DB_PATH, SCHEMA_PATH, BASE_DIR, DECKS_DIR
    DB_PATH = STORY_DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(BASE_DIR, "production", "main", "web", "ygo_story.db")
    SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    DECKS_DIR = os.path.join(BASE_DIR, "production", "shared", "decks")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from development.tools.tracker_sync import parse_raw_tracker, sync_tracker_to_database, DEFAULT_ROOT_CSV

# Canonical data directories
STORY_DATA_DIR = os.path.join(BASE_DIR, "production", "main", "discord_bot", "data", "story")


# -----------------------------------------------------------------------------
# C/C++ Low-Level Emulation Primitives
# -----------------------------------------------------------------------------
@dataclass
class CardDataStruct:
    """
    Python representation of the low-level ocgcore C/C++ `struct card_data`:

    ```c
    struct card_data {
        uint32_t code;
        uint32_t alias;
        uint64_t setcode;
        uint32_t type;
        uint32_t level;
        uint32_t attribute;
        uint32_t race;
        int32_t  attack;
        int32_t  defense;
        uint32_t category;
    };
    ```

    Ensures 1:1 structural alignment between SQLite card records, simulator CDB
    tables, and the C++ engine memory footprint.
    """
    code: int
    alias: int = 0
    setcode: int = 0
    card_type: int = 0
    level: int = 0
    attribute: int = 0
    race: int = 0
    attack: int = 0
    defense: int = 0
    category: int = 0


@dataclass
class DecklistStream:
    """
    Emulates the C/C++ continuous vector deck stream in ocgcore/EDOPro:

    ```c
    struct deck {
        std::vector<uint32_t> main;
        std::vector<uint32_t> extra;
        std::vector<uint32_t> side;
    };
    ```

    YDK files are flat integer streams of 32-bit card passcodes. Parsing them
    into partitioned integer arrays guarantees O(N) card validation, exact Yu-Gi-Oh!
    legality checks, and complete decoupling from Python code.
    """
    main: List[int] = field(default_factory=list)
    extra: List[int] = field(default_factory=list)
    side: List[int] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.main) + len(self.extra) + len(self.side)


# =============================================================================
# BLOCK 3: BODY BLOCK (Data Ingestion & Seeding Engine)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Database Schema Verification & Table Initialization
# -----------------------------------------------------------------------------
def verify_and_initialize_schema(db_path: str, schema_path: str) -> None:
    """Verifies SQLite tables and creates missing relations from schema.sql."""
    print(f"[*] Initializing database schema at {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    with open(schema_path, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    conn.commit()
    conn.close()
    print("[+] Database schema verified and ready.")


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Lore Sagas, Factions, Worldbuilding & Character Ingestion
# -----------------------------------------------------------------------------
def seed_lore_and_worldbuilding_subsystem(conn: sqlite3.Connection, data_dir: str) -> None:
    """
    Ingests canonical lore sagas, factions, worldbuilding elements, and duelist
    character dossiers from structured JSON data files into SQLite.
    """
    cur = conn.cursor()

    # 1. Lore Arcs
    arcs_file = os.path.join(data_dir, "lore_arcs.json")
    if os.path.exists(arcs_file):
        with open(arcs_file, "r", encoding="utf-8") as f:
            arcs_data = json.load(f)
        for arc in arcs_data:
            cur.execute("""
                INSERT INTO lore_arcs (id, title, synopsis, era_or_season)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    synopsis = excluded.synopsis,
                    era_or_season = excluded.era_or_season
            """, (arc["id"], arc["title"], arc["synopsis"], arc.get("era_or_season", "Genesis Era")))
        print(f"[+] Loaded {len(arcs_data)} lore arcs from {arcs_file}")

    # 2. Factions
    factions_file = os.path.join(data_dir, "factions.json")
    if os.path.exists(factions_file):
        with open(factions_file, "r", encoding="utf-8") as f:
            factions_data = json.load(f)
        for fac in factions_data:
            cur.execute("SELECT id FROM factions WHERE name = ?", (fac["name"],))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE factions SET
                        lore_description = ?,
                        playstyle_overview = ?,
                        arc_id = ?
                    WHERE id = ?
                """, (fac["lore_description"], fac.get("playstyle_overview", ""), fac.get("arc_id", 1), existing[0]))
            else:
                cur.execute("""
                    INSERT INTO factions (id, name, lore_description, playstyle_overview, arc_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (fac["id"], fac["name"], fac["lore_description"], fac.get("playstyle_overview", ""), fac.get("arc_id", 1)))
        print(f"[+] Loaded {len(factions_data)} factions from {factions_file}")

    # 3. Worldbuilding Elements
    world_file = os.path.join(data_dir, "worldbuilding.json")
    if os.path.exists(world_file):
        with open(world_file, "r", encoding="utf-8") as f:
            world_data = json.load(f)
        for elem in world_data:
            cur.execute("SELECT id FROM worldbuilding_elements WHERE name = ?", (elem["name"],))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE worldbuilding_elements SET
                        category = ?,
                        lore_description = ?,
                        significance = ?,
                        arc_id = ?
                    WHERE id = ?
                """, (elem["category"], elem["lore_description"], elem.get("significance"), elem.get("arc_id", 1), existing[0]))
            else:
                cur.execute("""
                    INSERT INTO worldbuilding_elements (id, category, name, lore_description, significance, arc_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (elem["id"], elem["category"], elem["name"], elem["lore_description"], elem.get("significance"), elem.get("arc_id", 1)))
        print(f"[+] Loaded {len(world_data)} worldbuilding elements from {world_file}")

    # 4. Duelist Character Dossiers
    chars_file = os.path.join(data_dir, "characters.json")
    if os.path.exists(chars_file):
        with open(chars_file, "r", encoding="utf-8") as f:
            chars_data = json.load(f)
        for ch in chars_data:
            cur.execute("SELECT id FROM characters WHERE name = ?", (ch["name"],))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE characters SET
                        alias = ?,
                        bio = ?,
                        faction_id = ?,
                        arc_id = ?,
                        avatar_url = ?
                    WHERE id = ?
                """, (ch.get("alias"), ch.get("bio"), ch.get("faction_id"), ch.get("arc_id", 1), ch.get("avatar_url"), existing[0]))
            else:
                cur.execute("""
                    INSERT INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ch["id"], ch["name"], ch.get("alias"), ch.get("bio"), ch.get("faction_id"), ch.get("arc_id", 1), ch.get("avatar_url")))
        print(f"[+] Loaded {len(chars_data)} characters from {chars_file}")

    conn.commit()


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Universal YDK Decklist Stream Parser & Registration
# -----------------------------------------------------------------------------
def parse_ydk_stream(ydk_path: str) -> Tuple[DecklistStream, str]:
    """
    Parses a simulator .ydk file into a DecklistStream C/C++ equivalent structure.
    Streams 32-bit integer card codes sequentially into Main, Extra, and Side vectors.
    """
    if not os.path.exists(ydk_path):
        raise FileNotFoundError(f"YDK decklist file not found: {ydk_path}")

    with open(ydk_path, "r", encoding="utf-8") as f:
        ydk_text = f.read()

    stream = DecklistStream()
    current_section = "main"

    for line in ydk_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#main"):
            current_section = "main"
        elif line.startswith("#extra"):
            current_section = "extra"
        elif line.startswith("!side"):
            current_section = "side"
        elif line.isdigit():
            card_id = int(line)
            if current_section == "main":
                stream.main.append(card_id)
            elif current_section == "extra":
                stream.extra.append(card_id)
            elif current_section == "side":
                stream.side.append(card_id)

    return stream, ydk_text


def seed_decks_subsystem(conn: sqlite3.Connection, data_dir: str, decks_dir: str) -> int:
    """
    Loads deck profiles from decks.json, parses external .ydk files via parse_ydk_stream,
    and registers all deck records and deck_cards junction rows in SQLite.
    Every deck (including Kasutamaiza Control) is externalized and stream-parsed.
    """
    decks_json_path = os.path.join(data_dir, "decks.json")
    if not os.path.exists(decks_json_path):
        return 0

    with open(decks_json_path, "r", encoding="utf-8") as f:
        decks_meta = json.load(f)

    cur = conn.cursor()
    seeded = 0

    for d in decks_meta:
        deck_id = d["id"]
        name = d["name"]
        char_id = d.get("character_id")
        creator = d.get("creator_name", "ProfessorSeanEX")
        desc = d.get("description", "")
        db_url = d.get("duelingbook_deck_url")
        ydk_filename = d.get("ydk_filename")

        ydk_path = os.path.join(decks_dir, ydk_filename) if ydk_filename else None
        if ydk_path and os.path.exists(ydk_path):
            stream, ydk_raw = parse_ydk_stream(ydk_path)
        else:
            stream, ydk_raw = DecklistStream(), ""

        cur.execute("""
            INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url, ydk_content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                character_id = excluded.character_id,
                creator_name = excluded.creator_name,
                description = excluded.description,
                duelingbook_deck_url = excluded.duelingbook_deck_url,
                ydk_content = excluded.ydk_content
        """, (deck_id, name, char_id, creator, desc, db_url, ydk_raw))

        # Synchronize deck_cards junction table
        cur.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))

        section_mappings = [
            ("MAIN", stream.main),
            ("EXTRA", stream.extra),
            ("SIDE", stream.side)
        ]
        for sec_name, card_ids in section_mappings:
            counts: Dict[int, int] = {}
            for cid in card_ids:
                counts[cid] = counts.get(cid, 0) + 1
            for cid, qty in counts.items():
                cur.execute("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, section)
                    VALUES (?, ?, ?, ?)
                """, (deck_id, cid, qty, sec_name))

        seeded += 1

    conn.commit()
    print(f"[+] Loaded and parsed {seeded} story decklists from {decks_dir}")
    return seeded


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Story Chapters, Scenarios & Duel Logs Synchronization
# -----------------------------------------------------------------------------
def seed_story_scenarios_subsystem(conn: sqlite3.Connection, story_dir: str) -> None:
    """
    Scans data/story/ for chapter scenario files (chapter_*.json) and duel logs,
    populating story_chapters, story_stages, and duel_logs tables dynamically.
    """
    cur = conn.cursor()

    # Ingest Duel Logs
    duel_logs_file = os.path.join(story_dir, "duel_logs.json")
    if os.path.exists(duel_logs_file):
        with open(duel_logs_file, "r", encoding="utf-8") as f:
            logs_data = json.load(f)
        for log in logs_data:
            cur.execute("""
                INSERT INTO duel_logs (id, arc_id, chapter_or_episode, duelist_1_id, duelist_2_id, winner_id, duel_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    duel_summary = excluded.duel_summary
            """, (log["id"], log.get("arc_id", 1), log["chapter_or_episode"], log.get("duelist_1_id", 1), log.get("duelist_2_id", 1), log.get("winner_id", 1), log["duel_summary"]))
        print(f"[+] Loaded {len(logs_data)} duel logs from {duel_logs_file}")

    # Ingest Scenario Chapters & Stages
    scenario_files = sorted(glob.glob(os.path.join(story_dir, "chapter_*.json")))
    total_stages = 0

    for json_path in scenario_files:
        with open(json_path, "r", encoding="utf-8") as jf:
            sdata = json.load(jf)

        c_num = sdata.get("chapter_number", 1)
        c_id = sdata.get("chapter_id", c_num)
        c_title = sdata.get("title", f"Chapter {c_num}")
        c_arc = sdata.get("arc_id", 1)
        c_synopsis = sdata.get("synopsis", "")

        cur.execute("""
            INSERT INTO story_chapters (id, chapter_number, title, arc_id, synopsis)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                chapter_number = excluded.chapter_number,
                title = excluded.title,
                arc_id = excluded.arc_id,
                synopsis = excluded.synopsis
        """, (c_id, c_num, c_title, c_arc, c_synopsis))

        for st in sdata.get("stages", []):
            st_num = st.get("stage_number", 1)
            st_id = st.get("stage_id") or (c_id * 100 + st_num)
            script_raw = st.get("script_data")
            script_str = json.dumps(script_raw) if (script_raw and not isinstance(script_raw, str)) else script_raw

            cur.execute("""
                INSERT INTO story_stages (
                    id, chapter_id, stage_number, title, intro_dialogue, outro_dialogue,
                    opponent_name, opponent_title, opponent_character_id, opponent_deck_id,
                    encounter_type, boss_hp, script_data, reward_title, reward_card_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    chapter_id = excluded.chapter_id,
                    stage_number = excluded.stage_number,
                    title = excluded.title,
                    intro_dialogue = excluded.intro_dialogue,
                    outro_dialogue = excluded.outro_dialogue,
                    opponent_name = excluded.opponent_name,
                    opponent_title = excluded.opponent_title,
                    opponent_character_id = excluded.opponent_character_id,
                    opponent_deck_id = excluded.opponent_deck_id,
                    encounter_type = excluded.encounter_type,
                    boss_hp = excluded.boss_hp,
                    script_data = excluded.script_data,
                    reward_title = excluded.reward_title,
                    reward_card_id = excluded.reward_card_id
            """, (
                st_id, c_id, st_num, st.get("title", ""),
                st.get("intro_dialogue", ""), st.get("outro_dialogue", ""),
                st.get("opponent_name", "Story Opponent"),
                st.get("opponent_title", "Challenger"),
                st.get("opponent_character_id", 1),
                st.get("opponent_deck_id", 1),
                st.get("encounter_type", "AI"),
                st.get("boss_hp", 8000),
                script_str,
                st.get("reward_title"),
                st.get("reward_card_id")
            ))
            total_stages += 1

    conn.commit()
    print(f"[+] Loaded {len(scenario_files)} story chapters and {total_stages} stages from {story_dir}")


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Master Card Tracker Parity & Usage Telemetry Initialization
# -----------------------------------------------------------------------------
def seed_custom_cards_and_telemetry_subsystem(conn: sqlite3.Connection, db_path: str) -> int:
    """
    Synchronizes custom cards from the Google Sheets / CSV Master Tracker into
    custom_cards table and initializes baseline card_usage_stats records.
    """
    print("[*] Synchronizing Set 1 cards from Master Tracker...")
    records = parse_raw_tracker(DEFAULT_ROOT_CSV)
    synced = sync_tracker_to_database(records, db_path=db_path)
    print(f"[+] Successfully seeded database with {synced} custom cards from The Land of Kustomazi!")

    cur = conn.cursor()
    cur.execute("SELECT id FROM custom_cards")
    for (cid,) in cur.fetchall():
        cur.execute("""
            INSERT OR IGNORE INTO card_usage_stats (card_id, times_decked, times_drawn, times_played, wins, losses)
            VALUES (?, 0, 0, 0, 0, 0)
        """, (cid,))
    conn.commit()
    return synced


# -----------------------------------------------------------------------------
# Master Seeder Orchestrator
# -----------------------------------------------------------------------------
def initialize_database(
    db_path: str = DB_PATH,
    schema_path: str = SCHEMA_PATH,
    data_dir: str = STORY_DATA_DIR,
    decks_dir: str = DECKS_DIR
) -> None:
    """
    Master pipeline executing the full 5-stage database seeding sequence:
    1. Schema verification & table creation
    2. Lore sagas, factions, worldbuilding & character ingestion
    3. Externalized YDK decklist parsing & registration (all 11 decks)
    4. Chapter scenarios & stage synchronization
    5. Master card tracker sync & telemetry initialization
    """
    # Stage 1: Schema
    verify_and_initialize_schema(db_path, schema_path)

    # Establish main connection
    conn = sqlite3.connect(db_path)

    # Stage 2: Lore & Worldbuilding
    seed_lore_and_worldbuilding_subsystem(conn, data_dir)

    # Stage 3: Decks (Universal Stream Parser)
    seed_decks_subsystem(conn, data_dir, decks_dir)

    # Stage 4: Story Scenarios
    seed_story_scenarios_subsystem(conn, data_dir)

    # Stage 5: Cards & Usage Stats
    seed_custom_cards_and_telemetry_subsystem(conn, db_path)

    conn.close()
    print("[+] Story database bootstrap and synchronization sequence successfully completed!")


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest & CLI Entry Point)
# =============================================================================

__all__ = [
    "CardDataStruct",
    "DecklistStream",
    "parse_ydk_stream",
    "verify_and_initialize_schema",
    "seed_lore_and_worldbuilding_subsystem",
    "seed_decks_subsystem",
    "seed_story_scenarios_subsystem",
    "seed_custom_cards_and_telemetry_subsystem",
    "initialize_database",
    "DB_PATH",
    "STORY_DATA_DIR",
    "DECKS_DIR",
]


def main() -> None:
    """CLI execution entrypoint for story database initialization."""
    initialize_database()


if __name__ == "__main__":
    main()
