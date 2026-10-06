#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: data.authoritative.seed_databases
Description:
    Authoritative Two-Tier Database Seeder & Initializer Pipeline.
    Initializes and seeds the dual-tier SQLite database baseline:
    1. Tier 1 (Authoritative Content Store - content.db):
       Applies schema_content.sql and seeds canonical lore sagas, factions,
       worldbuilding elements, duelist characters, pre-made character decks,
       story chapters, stage encounters, duel logs, and Set 1 custom cards.
    2. Tier 2 (Dynamic Telemetry Store - telemetry.db):
       Applies schema_telemetry.sql and initializes zeroed baseline usage stats
       for all registered cards in card_usage_stats.

Architectural Classification:
    Layer 1 (L1) - Database & Data Architecture Subsystem
    Subsystem: Core Data Seeding & Relational Store Initialization

Usage:
    python3 data/authoritative/seed_databases.py
    # Or via master management CLI:
    ./manage.sh install
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Imports & Path Resolution)
# =============================================================================

import os
import sys
import glob
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any

# Ensure project root is available in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from config.paths import (
        CONTENT_DB_PATH,
        TELEMETRY_DB_PATH,
        SCHEMA_CONTENT_PATH,
        SCHEMA_TELEMETRY_PATH,
        BASE_DIR,
        DECKS_DIR,
        LORE_DATA_DIR,
        STORY_DATA_DIR,
        TRACKERS_DIR,
    )
except ImportError:
    BASE_DIR = _PROJECT_ROOT
    CONTENT_DB_PATH = os.path.join(BASE_DIR, "data", "authoritative", "content.db")
    TELEMETRY_DB_PATH = os.path.join(BASE_DIR, "data", "telemetry", "telemetry.db")
    SCHEMA_CONTENT_PATH = os.path.join(BASE_DIR, "data", "authoritative", "schema_content.sql")
    SCHEMA_TELEMETRY_PATH = os.path.join(BASE_DIR, "data", "authoritative", "schema_telemetry.sql")
    DECKS_DIR = os.path.join(BASE_DIR, "data", "decks")
    LORE_DATA_DIR = os.path.join(BASE_DIR, "data", "lore")
    STORY_DATA_DIR = os.path.join(BASE_DIR, "data", "story")
    TRACKERS_DIR = os.path.join(BASE_DIR, "data", "trackers")

from development.tools.tracker_sync import parse_raw_tracker, sync_tracker_to_database, DEFAULT_ROOT_CSV


# =============================================================================
# BLOCK 3: BODY BLOCK (Two-Tier Database Seeding Engine)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Schema Application & Verification
# -----------------------------------------------------------------------------
def apply_schema(db_path: str, schema_path: str) -> None:
    """Creates directory if needed, connects to SQLite database, and executes DDL schema."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"[*] Initializing database schema at {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    with open(schema_path, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"[+] Database schema verified and ready at {db_path}.")


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Lore Sagas, Factions, Worldbuilding & Character Ingestion
# -----------------------------------------------------------------------------
def seed_lore_and_worldbuilding(
    conn: sqlite3.Connection,
    data_dir: str,
    lore_dir: Optional[str] = None
) -> None:
    """Ingests lore sagas, factions, worldbuilding elements, and duelist characters."""
    search_dir = lore_dir if (lore_dir and os.path.isdir(lore_dir)) else data_dir
    cur = conn.cursor()

    # 1. Lore Arcs
    arcs_file = os.path.join(search_dir, "lore_arcs.json")
    if not os.path.exists(arcs_file):
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
    factions_file = os.path.join(search_dir, "factions.json")
    if not os.path.exists(factions_file):
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
    world_file = os.path.join(search_dir, "worldbuilding.json")
    if not os.path.exists(world_file):
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
    chars_file = os.path.join(search_dir, "characters.json")
    if not os.path.exists(chars_file):
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
# Sub-Block 3.3: Pre-Made Character Decks & YDK Registration
# -----------------------------------------------------------------------------
def parse_ydk_file(ydk_path: str) -> Tuple[List[int], List[int], List[int], str]:
    """Parses a simulator .ydk file into main, extra, side integer passcode lists and raw text."""
    if not os.path.exists(ydk_path):
        return [], [], [], ""

    with open(ydk_path, "r", encoding="utf-8") as f:
        ydk_text = f.read()

    main_ids: List[int] = []
    extra_ids: List[int] = []
    side_ids: List[int] = []
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
                main_ids.append(card_id)
            elif current_section == "extra":
                extra_ids.append(card_id)
            elif current_section == "side":
                side_ids.append(card_id)

    return main_ids, extra_ids, side_ids, ydk_text


def seed_decks(conn: sqlite3.Connection, data_dir: str, decks_dir: str) -> int:
    """Loads deck profiles from decks.json, parses .ydk files, and populates decks & deck_cards."""
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
        main_ids, extra_ids, side_ids, ydk_raw = parse_ydk_file(ydk_path) if ydk_path else ([], [], [], "")

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

        cur.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck_id,))

        section_mappings = [
            ("MAIN", main_ids),
            ("EXTRA", extra_ids),
            ("SIDE", side_ids),
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
# Sub-Block 3.4: Story Chapters, Stages & Duel Logs Synchronization
# -----------------------------------------------------------------------------
def seed_story_scenarios(conn: sqlite3.Connection, story_dir: str) -> None:
    """Populates story_chapters, story_stages, and duel_logs narrative chronicles."""
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
            """, (
                log["id"],
                log.get("arc_id", 1),
                log["chapter_or_episode"],
                log.get("duelist_1_id", 1),
                log.get("duelist_2_id", 1),
                log.get("winner_id", 1),
                log["duel_summary"]
            ))
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
# Sub-Block 3.5: Custom Cards Synchronization from Master Tracker
# -----------------------------------------------------------------------------
def seed_custom_cards(content_db_path: str) -> int:
    """Synchronizes custom cards from the Master Tracker into content.db."""
    print(f"[*] Synchronizing Set 1 cards from Master Tracker into {content_db_path}...")
    records = parse_raw_tracker(DEFAULT_ROOT_CSV)
    synced = sync_tracker_to_database(records, db_path=content_db_path)
    print(f"[+] Successfully seeded {synced} custom cards into {content_db_path}!")
    return synced


# -----------------------------------------------------------------------------
# Sub-Block 3.6: Dynamic Telemetry Store Baseline Initialization
# -----------------------------------------------------------------------------
def seed_telemetry_baseline(content_db_path: str, telemetry_db_path: str) -> None:
    """Initializes zeroed baseline usage stats for all active cards in telemetry.db."""
    c_conn = sqlite3.connect(content_db_path)
    c_cur = c_conn.cursor()
    c_cur.execute("SELECT id FROM custom_cards")
    card_ids = [row[0] for row in c_cur.fetchall()]
    c_conn.close()

    t_conn = sqlite3.connect(telemetry_db_path)
    t_cur = t_conn.cursor()
    for cid in card_ids:
        t_cur.execute("""
            INSERT OR IGNORE INTO card_usage_stats (card_id, times_decked, times_drawn, times_played, wins, losses)
            VALUES (?, 0, 0, 0, 0, 0)
        """, (cid,))
    t_conn.commit()
    t_conn.close()
    print(f"[+] Initialized baseline telemetry for {len(card_ids)} cards in {telemetry_db_path}")


# -----------------------------------------------------------------------------
# Sub-Block 3.7: Master Two-Tier Seeding Orchestrator
# -----------------------------------------------------------------------------
def seed_all_databases(
    content_db_path: str = CONTENT_DB_PATH,
    telemetry_db_path: str = TELEMETRY_DB_PATH,
    schema_content_path: str = SCHEMA_CONTENT_PATH,
    schema_telemetry_path: str = SCHEMA_TELEMETRY_PATH,
    data_dir: str = STORY_DATA_DIR,
    lore_dir: str = LORE_DATA_DIR,
    decks_dir: str = DECKS_DIR,
) -> None:
    """
    Master pipeline executing the authoritative two-tier database seeding sequence:
    1. Tier 1 (Authoritative Content Store - content.db):
       Applies schema_content.sql, seeds lore, factions, worldbuilding,
       characters, decks, story stages, duel logs, and custom cards.
    2. Tier 2 (Dynamic Telemetry Store - telemetry.db):
       Applies schema_telemetry.sql and populates baseline card_usage_stats.
    """
    # -------------------------------------------------------------------------
    # Tier 1: Authoritative Content Database (CONTENT_DB_PATH)
    # -------------------------------------------------------------------------
    apply_schema(content_db_path, schema_content_path)
    c_conn = sqlite3.connect(content_db_path)
    seed_lore_and_worldbuilding(c_conn, data_dir, lore_dir=lore_dir)
    seed_decks(c_conn, data_dir, decks_dir)
    seed_story_scenarios(c_conn, data_dir)
    c_conn.close()

    # Synchronize custom cards via tracker into content store
    seed_custom_cards(content_db_path)
    print(f"[+] Synchronized authoritative content store at {content_db_path}")

    # -------------------------------------------------------------------------
    # Tier 2: Dynamic Telemetry Database (TELEMETRY_DB_PATH)
    # -------------------------------------------------------------------------
    apply_schema(telemetry_db_path, schema_telemetry_path)
    seed_telemetry_baseline(content_db_path, telemetry_db_path)
    print(f"[+] Synchronized dynamic telemetry store at {telemetry_db_path}")

    print("[+] Database bootstrap and synchronization sequence successfully completed!")


# Canonical alias for platform callers
initialize_database = seed_all_databases


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest & CLI Entry Point)
# =============================================================================

__all__ = [
    "apply_schema",
    "seed_lore_and_worldbuilding",
    "seed_decks",
    "seed_story_scenarios",
    "seed_custom_cards",
    "seed_telemetry_baseline",
    "seed_all_databases",
    "initialize_database",
    "CONTENT_DB_PATH",
    "TELEMETRY_DB_PATH",
]


def main() -> None:
    """CLI execution entrypoint for two-tier database seeding."""
    seed_all_databases()


if __name__ == "__main__":
    main()

