#!/usr/bin/env python3
"""
Duelingbook Importer Tool
Parses Duelingbook custom cards (from JSON files or raw exports) and imports them
into the Story Database, synchronizing with the game simulator's CDB and Lua scripts.
"""

import json
import sqlite3
import os
import sys
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")

from cdb_builder import build_cdb
from lua_generator import generate_lua_for_card

# Duelingbook type mappings
DB_CARD_TYPES = {
    1: 'Monster',
    2: 'Spell',
    3: 'Trap'
}

DB_MONSTER_COLORS = {
    1: 'Normal',
    2: 'Effect',
    3: 'Ritual',
    4: 'Fusion',
    5: 'Synchro',
    6: 'Xyz',
    7: 'Pendulum',
    8: 'Link'
}

DB_SPELL_TYPES = {
    1: 'Normal',
    2: 'Quick-Play',
    3: 'Continuous',
    4: 'Equip',
    5: 'Field',
    6: 'Ritual'
}

DB_TRAP_TYPES = {
    1: 'Normal',
    2: 'Continuous',
    3: 'Counter'
}

DB_ATTRIBUTES = {
    1: 'EARTH',
    2: 'WATER',
    3: 'FIRE',
    4: 'WIND',
    5: 'LIGHT',
    6: 'DARK',
    7: 'DIVINE'
}

def generate_custom_passcode(conn):
    cur = conn.cursor()
    while True:
        # 50000000 - 59999999 range commonly reserved for custom cards
        code = random.randint(50000000, 59999999)
        cur.execute("SELECT id FROM custom_cards WHERE id = ?", (code,))
        if not cur.fetchone():
            return code

def import_card_data(data, lore_text=None, faction_id=None, character_id=None, db_path=STORY_DB_PATH):
    """
    Imports a single card from a standardized dict or raw Duelingbook JSON dict.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Extract / normalize fields
    name = data.get("name")
    if not name:
        raise ValueError("Card name is required.")
        
    cid = data.get("id") or data.get("serial_number")
    if not cid or int(cid) < 1000:
        # Check if card already exists by name
        cur.execute("SELECT id FROM custom_cards WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            cid = row[0]
        else:
            cid = generate_custom_passcode(conn)
    else:
        cid = int(cid)

    # Resolve card types
    raw_card_type = data.get("card_type")
    if isinstance(raw_card_type, int):
        card_type = DB_CARD_TYPES.get(raw_card_type, "Monster")
    else:
        card_type = str(raw_card_type or "Monster").capitalize()
        
    card_subtype = data.get("card_subtype") or data.get("subtype")
    if not card_subtype:
        if card_type == "Monster":
            color = data.get("monster_color", 2)
            card_subtype = DB_MONSTER_COLORS.get(color, "Effect")
        elif card_type == "Spell":
            stype = data.get("property", 1)
            card_subtype = DB_SPELL_TYPES.get(stype, "Normal")
        elif card_type == "Trap":
            ttype = data.get("property", 1)
            card_subtype = DB_TRAP_TYPES.get(ttype, "Normal")
            
    # Attribute
    raw_attr = data.get("attribute")
    if isinstance(raw_attr, int):
        attribute = DB_ATTRIBUTES.get(raw_attr, "DARK")
    else:
        attribute = str(raw_attr).upper() if raw_attr else None
        
    monster_type = data.get("monster_type") or data.get("type")
    level = data.get("level") or data.get("rank") or data.get("link_rating")
    scale = data.get("scale") or data.get("pendulum_scale")
    atk = data.get("atk") or data.get("attack")
    defense = data.get("def") or data.get("defense")
    link_arrows = data.get("link_arrows") or data.get("arrows")
    
    effect_text = data.get("effect_text") or data.get("effect", "")
    pendulum_effect = data.get("pendulum_effect")
    
    db_id = str(data.get("duelingbook_id") or data.get("db_id") or cid)
    db_url = data.get("duelingbook_url") or f"https://www.duelingbook.com/card?id={db_id}"
    image_url = data.get("image_url") or data.get("picture")
    creator = data.get("creator_name") or data.get("username") or "Duelingbook Designer"
    
    story_lore = lore_text or data.get("lore_text") or "A relic discovered along the edge of the Astral Fracture."
    story_sig = data.get("story_significance", "Custom Card")
    
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
    
    # Update FTS index
    cur.execute("DELETE FROM cards_fts WHERE rowid = ?", (cid,))
    cur.execute("""
        INSERT INTO cards_fts (rowid, name, effect_text, lore_text, card_type, monster_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (cid, name, effect_text, story_lore, card_type, monster_type))
    
    conn.commit()
    conn.close()
    
    # Re-sync with CDB and generate starter Lua script
    build_cdb()
    generate_lua_for_card((cid, name, card_type, card_subtype, db_url))
    
    print(f"[+] Successfully imported card '{name}' [ID: {cid}] from Duelingbook format!")
    return cid

def import_from_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        for item in data:
            import_card_data(item)
    elif isinstance(data, dict):
        if "cards" in data and isinstance(data["cards"], list):
            for item in data["cards"]:
                import_card_data(item)
        else:
            import_card_data(data)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_from_json_file(sys.argv[1])
    else:
        print("Usage: python3 duelingbook_importer.py <cards.json>")
