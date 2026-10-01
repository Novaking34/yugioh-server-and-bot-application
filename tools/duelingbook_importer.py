#!/usr/bin/env python3
"""
=============================================================================
Duelingbook Custom Card Importer & Pipeline Synchronizer
=============================================================================
Duelingbook (duelingbook.com) is the primary web application where Yu-Gi-Oh!
custom card creators design card artwork, type out card effects, and assign
parameters (Attribute, Level/Rank/Link Rating, Scales, ATK/DEF).

This tool bridges Duelingbook and our live platform by:
1. Parsing raw Duelingbook JSON card definitions (or standardized dictionaries).
2. Generating a valid, non-colliding 8-digit custom passcode (50,000,000 range).
3. Inserting/updating the card in the SQLite Story Database (`ygo_story.db`).
4. Updating the Full-Text Search (FTS5) virtual table index.
5. Automatically calling `cdb_builder.py` to update the duel simulator CDB.
6. Automatically calling `lua_generator.py` to scaffold the card's Lua effect script.
=============================================================================
"""

import json
import sqlite3
import os
import sys
import random
from typing import Dict, Any, Optional, List, Union, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")

# Import centralized tools and constants
sys.path.append(os.path.join(BASE_DIR, "tools"))
from constants import (
    DB_CARD_TYPES, DB_MONSTER_COLORS, DB_SPELL_PROPERTIES,
    DB_TRAP_PROPERTIES, DB_ATTRIBUTES
)
from cdb_builder import build_cdb
from lua_generator import generate_lua_for_card


def generate_custom_passcode(conn: sqlite3.Connection) -> int:
    """
    Generates a unique 8-digit passcode in the 50000000-59999999 range.
    In the Yu-Gi-Oh! simulator community, the 50,000,000-89,999,999 range is
    traditionally reserved for custom and anime-exclusive cards to prevent
    ID collisions with official Konami database passcodes (10,000,000-99,999,999).
    """
    cur = conn.cursor()
    while True:
        candidate_code = random.randint(50000000, 59999999)
        cur.execute("SELECT id FROM custom_cards WHERE id = ?", (candidate_code,))
        if not cur.fetchone():
            return candidate_code


def resolve_card_classification(data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Extracts and standardizes the card type ('Monster', 'Spell', 'Trap')
    and subtype ('Effect', 'Xyz', 'Quick-Play', etc.) from Duelingbook data.
    """
    # 1. Primary Card Type
    raw_type = data.get("card_type")
    if isinstance(raw_type, int):
        card_type = DB_CARD_TYPES.get(raw_type, "Monster")
    else:
        card_type = str(raw_type or "Monster").strip().capitalize()

    # 2. Subtype / Classification
    card_subtype = data.get("card_subtype") or data.get("subtype")
    if not card_subtype:
        if card_type == "Monster":
            color_code = data.get("monster_color", 2)
            card_subtype = DB_MONSTER_COLORS.get(color_code, "Effect")
        elif card_type == "Spell":
            prop_code = data.get("property", 1)
            card_subtype = DB_SPELL_PROPERTIES.get(prop_code, "Normal")
        elif card_type == "Trap":
            prop_code = data.get("property", 1)
            card_subtype = DB_TRAP_PROPERTIES.get(prop_code, "Normal")
        else:
            card_subtype = "Normal"

    return card_type, str(card_subtype).strip()


def resolve_attribute(data: Dict[str, Any]) -> Optional[str]:
    """Normalizes the card attribute into uppercase standard (LIGHT, DARK, etc.)."""
    raw_attr = data.get("attribute")
    if isinstance(raw_attr, int):
        return DB_ATTRIBUTES.get(raw_attr, "DARK")
    if raw_attr:
        return str(raw_attr).strip().upper()
    return None


def import_card_data(
    data: Dict[str, Any],
    lore_text: Optional[str] = None,
    faction_id: Optional[int] = None,
    character_id: Optional[int] = None,
    db_path: str = STORY_DB_PATH,
    sync_simulator: bool = True
) -> int:
    """
    Imports a single card from a dictionary, commits to the Story DB,
    and updates simulator expansions.

    Args:
        data: Card dictionary containing attributes from Duelingbook or custom creator.
        lore_text: Optional in-universe story lore.
        faction_id: Optional ID of the associated faction/archetype.
        character_id: Optional ID of the signature duelist.
        db_path: Path to the SQLite story database.
        sync_simulator: Whether to automatically rebuild CDB and Lua files.

    Returns:
        int: The resolved card passcode / ID.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    name = (data.get("name") or "").strip()
    if not name:
        conn.close()
        raise ValueError("Card name is required.")

    # Determine unique passcode
    cid = data.get("id") or data.get("serial_number")
    if not cid or int(cid) < 1000:
        # Check if card already exists by name
        cur.execute("SELECT id FROM custom_cards WHERE name = ?", (name,))
        existing = cur.fetchone()
        if existing:
            cid = existing[0]
        else:
            cid = generate_custom_passcode(conn)
    else:
        cid = int(cid)

    # Classifications
    card_type, card_subtype = resolve_card_classification(data)
    attribute = resolve_attribute(data)

    monster_type = data.get("monster_type") or data.get("type")
    level = data.get("level") or data.get("rank") or data.get("link_rating")
    scale = data.get("scale") or data.get("pendulum_scale")
    atk = data.get("atk") or data.get("attack")
    defense = data.get("def") or data.get("defense")
    link_arrows = data.get("link_arrows") or data.get("arrows")

    effect_text = (data.get("effect_text") or data.get("effect") or "").strip()
    pendulum_effect = data.get("pendulum_effect")

    # Duelingbook references
    db_id = str(data.get("duelingbook_id") or data.get("db_id") or cid)
    db_url = data.get("duelingbook_url") or f"https://www.duelingbook.com/card?id={db_id}"
    image_url = data.get("image_url") or data.get("picture")
    creator = data.get("creator_name") or data.get("username") or "Duelingbook Designer"

    story_lore = lore_text or data.get("lore_text") or "A celestial relic discovered along the edge of the Astral Fracture."
    story_sig = data.get("story_significance", "Custom Card")

    # Insert or update record in custom_cards table
    cur.execute("""
        INSERT OR REPLACE INTO custom_cards (
            id, name, card_type, card_subtype, attribute, monster_type,
            level_or_rank_or_link, scale, atk, def, link_arrows,
            effect_text, pendulum_effect, duelingbook_id, duelingbook_url,
            image_url, creator_name, lore_text, faction_id,
            signature_character_id, story_significance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cid, name, card_type, card_subtype, attribute, monster_type,
        level, scale, atk, defense, link_arrows,
        effect_text, pendulum_effect, db_id, db_url,
        image_url, creator, story_lore, faction_id,
        character_id, story_sig
    ))

    # Synchronize Full-Text Search index
    cur.execute("DELETE FROM cards_fts WHERE rowid = ?", (cid,))
    cur.execute("""
        INSERT INTO cards_fts (rowid, name, effect_text, lore_text, card_type, monster_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cid, name, effect_text, story_lore, card_type, monster_type))

    conn.commit()
    conn.close()

    # Synchronize with YGOPro simulator if requested
    if sync_simulator:
        build_cdb(story_db_path=db_path)
        generate_lua_for_card((cid, name, card_type, card_subtype, db_url), overwrite=True)

    print(f"[+] Successfully registered '{name}' [Passcode: {cid}]")
    return cid


def import_from_json_file(file_path: str, sync_simulator: bool = True) -> List[int]:
    """
    Reads a Duelingbook export file (.json) containing a single card or list of cards
    and imports them into the system.
    """
    if not os.path.exists(file_path):
        print(f"[-] File not found: {file_path}", file=sys.stderr)
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    imported_ids = []
    if isinstance(data, list):
        for item in data:
            imported_ids.append(import_card_data(item, sync_simulator=False))
    elif isinstance(data, dict):
        if "cards" in data and isinstance(data["cards"], list):
            for item in data["cards"]:
                imported_ids.append(import_card_data(item, sync_simulator=False))
        else:
            imported_ids.append(import_card_data(data, sync_simulator=False))

    # Perform a single bulk simulator synchronization if multiple cards were imported
    if sync_simulator and imported_ids:
        build_cdb()
        from lua_generator import generate_all_scripts
        generate_all_scripts()

    print(f"[+] Imported {len(imported_ids)} cards from {file_path}")
    return imported_ids


if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_from_json_file(sys.argv[1])
    else:
        print("Yu-Gi-Oh! Duelingbook Card Importer")
        print("Usage: python3 duelingbook_importer.py <cards.json>")
