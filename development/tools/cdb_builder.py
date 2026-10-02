#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator SQLite CDB Builder & Synchronizer
=============================================================================
This tool compiles custom card entries from the main relational Story Database
(`production/main/web/ygo_story.db`) into an official YGOPro / EDOPro SQLite `.cdb`
file (`production/shared/expansions/custom_cards.cdb`).

How the YGOPro CDB Binary Format Works:
---------------------------------------
Every YGOPro duel simulator (including ocgcore, EDOPro, Project Ignis, and Koishi)
reads its card database from SQLite files ending in `.cdb`. A CDB file has
exactly two relational tables:

1. `datas`: Stores numerical parameters, stats, bitwise classifications, and IDs:
   - `id`: Unique 8-digit card passcode (primary key).
   - `ot`: Origin/Format (1=OCG, 2=TCG, 3=Anime, 4=Custom/Beta).
   - `alias`: Used for alternate artworks or name sharing (e.g. Harpie Lady 1 -> 2).
   - `setcode`: Archetype membership bitmask (e.g. 0x101f for "Starforged").
   - `type`: Bitmask of card categories (Monster, Spell, Trap, Xyz, Link, etc.).
   - `atk`: Attack points (-2 for ?, 0 for 0, positive integers for stats).
   - `def`: Defense points (-2 for ?). Note: FOR LINK MONSTERS, this field holds
     the active Link Arrows bitmask instead of defense points!
   - `level`: Monster Level or Rank or Link Rating. For Pendulum Monsters, this
     field encodes both Pendulum Scales and the Level using bit-packing:
     `((left_scale << 24) | (right_scale << 16) | level)`.
   - `race`: Monster Race/Species bitmask (Warrior, Dragon, Spellcaster, etc.).
   - `attribute`: Monster Elemental Attribute bitmask (LIGHT, DARK, FIRE, etc.).
   - `category`: Effect category bitmask (Destruction, Search, Banish, etc.).

2. `texts`: Stores the user-facing text, name, effect, and dialog strings:
   - `id`: Matching card passcode (primary key).
   - `name`: Display name of the card.
   - `desc`: Complete effect text (or Pendulum effect + Monster effect combined).
   - `str1` through `str16`: String descriptions referenced by Lua scripts when
     prompting players for multiple choice effect selections.
=============================================================================
"""

import sqlite3
import os
import sys
from typing import Optional, Tuple

# Resolve project base directory
try:
    from config.paths import BASE_DIR, STORY_DB_PATH, CDB_OUTPUT_PATH, EXPANSIONS_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORY_DB_PATH = os.path.join(BASE_DIR, "production", "main", "web", "ygo_story.db")
    EXPANSIONS_DIR = os.path.join(BASE_DIR, "production", "shared", "expansions")
    CDB_OUTPUT_PATH = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")

# Import centralized YGOPro constants from local tools directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from constants import (
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_NORMAL, TYPE_EFFECT,
    TYPE_FUSION, TYPE_RITUAL, TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK,
    TYPE_TUNER, TYPE_QUICKPLAY, TYPE_CONTINUOUS, TYPE_EQUIP, TYPE_FIELD, TYPE_COUNTER,
    ATTRIBUTE_MAP, RACE_MAP, LINK_ARROW_MAP
)


def parse_card_type(card_type: Optional[str], card_subtype: Optional[str]) -> int:
    """
    Computes the composite bitmask for `datas.type` from card classification strings.
    
    Example:
        ("Monster", "Effect Xyz") -> TYPE_MONSTER | TYPE_EFFECT | TYPE_XYZ
        ("Spell", "Field")        -> TYPE_SPELL | TYPE_FIELD
    """
    val = 0
    ctype_lower = (card_type or '').strip().lower()
    csub_lower = (card_subtype or '').strip().lower()

    if ctype_lower == 'monster':
        val |= TYPE_MONSTER
        # Subtype flags for monsters
        if 'effect' in csub_lower:
            val |= TYPE_EFFECT
        elif 'normal' in csub_lower:
            val |= TYPE_NORMAL

        if 'fusion' in csub_lower:
            val |= TYPE_FUSION
        if 'synchro' in csub_lower:
            val |= TYPE_SYNCHRO
        if 'xyz' in csub_lower:
            val |= TYPE_XYZ
        if 'link' in csub_lower:
            val |= TYPE_LINK
        if 'ritual' in csub_lower:
            val |= TYPE_RITUAL
        if 'pendulum' in csub_lower:
            val |= TYPE_PENDULUM
        if 'tuner' in csub_lower:
            val |= TYPE_TUNER

    elif ctype_lower == 'spell':
        val |= TYPE_SPELL
        if 'quick' in csub_lower:
            val |= TYPE_QUICKPLAY
        elif 'continuous' in csub_lower:
            val |= TYPE_CONTINUOUS
        elif 'field' in csub_lower:
            val |= TYPE_FIELD
        elif 'equip' in csub_lower:
            val |= TYPE_EQUIP
        elif 'ritual' in csub_lower:
            val |= TYPE_RITUAL
        else:
            val |= TYPE_NORMAL

    elif ctype_lower == 'trap':
        val |= TYPE_TRAP
        if 'counter' in csub_lower:
            val |= TYPE_COUNTER
        elif 'continuous' in csub_lower:
            val |= TYPE_CONTINUOUS
        else:
            val |= TYPE_NORMAL

    return val


def parse_attribute(attribute_str: Optional[str]) -> int:
    """
    Maps an attribute name (e.g., 'LIGHT', 'DARK') to its ocgcore integer bitmask.
    Returns 0 if attribute is unspecified or invalid.
    """
    if not attribute_str:
        return 0
    return ATTRIBUTE_MAP.get(attribute_str.strip().lower(), 0)


def parse_race(race_str: Optional[str]) -> int:
    """
    Maps a monster type/race name (e.g., 'Warrior', 'Dragon') to its ocgcore integer bitmask.
    Returns 0 if race is unspecified or invalid.
    """
    if not race_str:
        return 0
    return RACE_MAP.get(race_str.strip().lower(), 0)


def parse_level_and_scale(
    level: Optional[int],
    scale: Optional[int],
    card_subtype: Optional[str]
) -> int:
    """
    Encodes Level, Rank, Link Rating, and Pendulum Scales into `datas.level`.
    
    YGOPro Level Bit-Packing Format:
    - Bits 0-7   (0xFF): Monster Level / Rank / Link Rating
    - Bits 16-23 (0xFF0000): Right Pendulum Scale
    - Bits 24-31 (0xFF000000): Left Pendulum Scale
    
    For Link Monsters, the level column stores purely the integer Link Rating (e.g. 2 for Link-2).
    """
    if level is None:
        return 0

    csub_lower = (card_subtype or '').lower()
    
    # Link monsters store raw link rating without scale packing
    if 'link' in csub_lower:
        return int(level)

    # Standard level/rank fits into the lowest byte (0xFF)
    packed_value = int(level) & 0xFF

    # If pendulum monster, pack scales into bytes 3 and 4
    if scale is not None:
        left_scale = (int(scale) & 0xFF) << 24
        right_scale = (int(scale) & 0xFF) << 16
        packed_value |= (left_scale | right_scale)

    return packed_value


def parse_link_arrows(arrows_str: Optional[str]) -> int:
    """
    Converts a comma- or semicolon-separated string of Link arrows (e.g. 'BL,BR,T')
    into the octal bitmask expected in `datas.def` for Link Monsters.
    """
    if not arrows_str:
        return 0

    arrow_bitmask = 0
    parts = [p.strip().upper() for p in arrows_str.replace(';', ',').split(',') if p.strip()]
    for p in parts:
        if p in LINK_ARROW_MAP:
            arrow_bitmask |= LINK_ARROW_MAP[p]

    return arrow_bitmask


def format_card_description(effect_text: str, pendulum_effect: Optional[str]) -> str:
    """
    Formats the card description for the `texts.desc` column.
    If the card is a Pendulum Monster, standard YGOPro format separates the
    Pendulum Effect and Monster Effect with bracketed headings and dashes.
    """
    clean_monster = (effect_text or "").strip()
    if pendulum_effect and pendulum_effect.strip():
        clean_pendulum = pendulum_effect.strip()
        return (
            f"[ Pendulum Effect ]\n"
            f"{clean_pendulum}\n"
            f"----------------------------------------\n"
            f"[ Monster Effect ]\n"
            f"{clean_monster}"
        )
    return clean_monster


def build_cdb(
    story_db_path: str = STORY_DB_PATH,
    cdb_output_path: str = CDB_OUTPUT_PATH
) -> int:
    """
    Reads all custom cards from `production/main/web/ygo_story.db` and writes them
    into the YGOPro simulator SQLite `.cdb` file at `production/shared/expansions/custom_cards.cdb`.
    
    Returns:
        int: The number of cards compiled into the CDB.
    """
    print(f"[*] Starting CDB compilation: {story_db_path} -> {cdb_output_path}")
    os.makedirs(os.path.dirname(cdb_output_path), exist_ok=True)

    # 1. Connect to source Story Database
    story_conn = sqlite3.connect(story_db_path)
    story_cur = story_conn.cursor()

    # 2. Connect to target CDB database and initialize tables
    cdb_conn = sqlite3.connect(cdb_output_path)
    cdb_cur = cdb_conn.cursor()

    cdb_cur.execute("""
        CREATE TABLE IF NOT EXISTS datas (
            id integer primary key,
            ot integer,
            alias integer,
            setcode integer,
            type integer,
            atk integer,
            def integer,
            level integer,
            race integer,
            attribute integer,
            category integer
        )
    """)

    cdb_cur.execute("""
        CREATE TABLE IF NOT EXISTS texts (
            id integer primary key,
            name text,
            desc text,
            str1 text, str2 text, str3 text, str4 text,
            str5 text, str6 text, str7 text, str8 text,
            str9 text, str10 text, str11 text, str12 text,
            str13 text, str14 text, str15 text, str16 text
        )
    """)

    # 3. Fetch all custom cards from Story DB
    story_cur.execute("""
        SELECT id, name, card_type, card_subtype, attribute, monster_type,
               level_or_rank_or_link, scale, atk, def, link_arrows,
               effect_text, pendulum_effect
        FROM custom_cards
        ORDER BY id ASC
    """)
    cards = story_cur.fetchall()
    compiled_count = 0

    for card in cards:
        (cid, name, ctype, csubtype, attribute, monster_type,
         level, scale, atk, defense, link_arrows, effect_text, pendulum_effect) = card

        # Compute YGOPro binary flags
        c_type = parse_card_type(ctype, csubtype)
        c_attr = parse_attribute(attribute)
        c_race = parse_race(monster_type)
        c_lvl = parse_level_and_scale(level, scale, csubtype)
        c_atk = atk if atk is not None else 0

        # In YGOPro, Link monsters store the link arrows bitmask in the defense column
        if (csubtype or '').lower() == 'link':
            c_def = parse_link_arrows(link_arrows)
        else:
            c_def = defense if defense is not None else 0

        full_desc = format_card_description(effect_text, pendulum_effect)

        # 4. Insert or update entry in datas table
        # ot=4 represents Custom Card format in ocgcore
        cdb_cur.execute("""
            INSERT OR REPLACE INTO datas (
                id, ot, alias, setcode, type, atk, def, level, race, attribute, category
            ) VALUES (?, 4, 0, 0, ?, ?, ?, ?, ?, ?, 0)
        """, (cid, c_type, c_atk, c_def, c_lvl, c_race, c_attr))

        # 5. Insert or update entry in texts table
        cdb_cur.execute("""
            INSERT OR REPLACE INTO texts (
                id, name, desc
            ) VALUES (?, ?, ?)
        """, (cid, name, full_desc))

        compiled_count += 1

    # Commit changes and clean up
    cdb_conn.commit()
    cdb_conn.close()
    story_conn.close()

    print(f"[+] Successfully compiled {compiled_count} cards into {cdb_output_path}!")
    return compiled_count


if __name__ == "__main__":
    build_cdb()
