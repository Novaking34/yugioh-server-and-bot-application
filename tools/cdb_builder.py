#!/usr/bin/env python3
"""
CDB Builder for Yu-Gi-Oh Game Simulators (YGOPro / EDOPro / Koishi / Project Ignis).
Builds or synchronizes custom cards from ygo_story.db into custom_cards.cdb.
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
CDB_OUTPUT_PATH = os.path.join(BASE_DIR, "server-data", "expansions", "custom_cards.cdb")

# YGOPro bitmasks
TYPE_MONSTER    = 0x1
TYPE_SPELL      = 0x2
TYPE_TRAP       = 0x4
TYPE_NORMAL     = 0x10
TYPE_EFFECT     = 0x20
TYPE_FUSION     = 0x40
TYPE_RITUAL     = 0x80
TYPE_TRAPMONSTER= 0x100
TYPE_SPIRIT     = 0x200
TYPE_UNION      = 0x400
TYPE_DUAL       = 0x800
TYPE_TUNER      = 0x1000
TYPE_SYNCHRO    = 0x2000
TYPE_TOKEN      = 0x4000
TYPE_QUICKPLAY  = 0x10000
TYPE_CONTINUOUS = 0x20000
TYPE_EQUIP      = 0x40000
TYPE_FIELD      = 0x80000
TYPE_COUNTER    = 0x100000
TYPE_FLIP       = 0x200000
TYPE_TOON       = 0x400000
TYPE_XYZ        = 0x800000
TYPE_PENDULUM   = 0x1000000
TYPE_SPECIAL    = 0x2000000
TYPE_LINK       = 0x4000000

ATTRIBUTE_EARTH   = 0x01
ATTRIBUTE_WATER   = 0x02
ATTRIBUTE_FIRE    = 0x04
ATTRIBUTE_WIND    = 0x08
ATTRIBUTE_LIGHT   = 0x10
ATTRIBUTE_DARK    = 0x20
ATTRIBUTE_DIVINE  = 0x40

RACE_WARRIOR      = 0x1
RACE_SPELLCASTER  = 0x2
RACE_FAIRY        = 0x4
RACE_FIEND        = 0x8
RACE_ZOMBIE       = 0x10
RACE_MACHINE      = 0x20
RACE_AQUA         = 0x40
RACE_PYRO         = 0x80
RACE_ROCK         = 0x100
RACE_WINGEDBEAST  = 0x200
RACE_PLANT        = 0x400
RACE_INSECT       = 0x800
RACE_THUNDER      = 0x1000
RACE_DRAGON       = 0x2000
RACE_BEAST        = 0x4000
RACE_BEASTWARRIOR = 0x8000
RACE_DINOSAUR     = 0x10000
RACE_FISH         = 0x20000
RACE_SEASERPENT   = 0x40000
RACE_REPTILE      = 0x80000
RACE_PSYCHIC      = 0x100000
RACE_DIVINEBEAST  = 0x200000
RACE_CREATORGOD   = 0x400000
RACE_WYRM         = 0x800000
RACE_CYBERSE      = 0x1000000
RACE_ILLUSION     = 0x2000000

# Link arrows bitmasks
LINK_B   = 0o001
LINK_BL  = 0o002
LINK_BR  = 0o004
LINK_L   = 0o010
LINK_R   = 0o040
LINK_T   = 0o100
LINK_TL  = 0o200
LINK_TR  = 0o400

LINK_MAP = {
    'B': LINK_B, 'BL': LINK_BL, 'BR': LINK_BR,
    'L': LINK_L, 'R': LINK_R,
    'T': LINK_T, 'TL': LINK_TL, 'TR': LINK_TR,
    'BOTTOM': LINK_B, 'BOTTOM-LEFT': LINK_BL, 'BOTTOM-RIGHT': LINK_BR,
    'TOP': LINK_T, 'TOP-LEFT': LINK_TL, 'TOP-RIGHT': LINK_TR
}

def parse_card_type(ctype, csubtype):
    val = 0
    ctype_l = (ctype or '').lower()
    csub_l = (csubtype or '').lower()
    
    if ctype_l == 'monster':
        val |= TYPE_MONSTER
        if 'effect' in csub_l: val |= TYPE_EFFECT
        elif 'normal' in csub_l: val |= TYPE_NORMAL
        if 'fusion' in csub_l: val |= TYPE_FUSION
        if 'synchro' in csub_l: val |= TYPE_SYNCHRO
        if 'xyz' in csub_l: val |= TYPE_XYZ
        if 'link' in csub_l: val |= TYPE_LINK
        if 'ritual' in csub_l: val |= TYPE_RITUAL
        if 'pendulum' in csub_l: val |= TYPE_PENDULUM
        if 'tuner' in csub_l: val |= TYPE_TUNER
    elif ctype_l == 'spell':
        val |= TYPE_SPELL
        if 'quick' in csub_l: val |= TYPE_QUICKPLAY
        elif 'continuous' in csub_l: val |= TYPE_CONTINUOUS
        elif 'field' in csub_l: val |= TYPE_FIELD
        elif 'equip' in csub_l: val |= TYPE_EQUIP
        elif 'ritual' in csub_l: val |= TYPE_RITUAL
        else: val |= TYPE_NORMAL
    elif ctype_l == 'trap':
        val |= TYPE_TRAP
        if 'counter' in csub_l: val |= TYPE_COUNTER
        elif 'continuous' in csub_l: val |= TYPE_CONTINUOUS
        else: val |= TYPE_NORMAL
    return val

def parse_attribute(attr):
    mapping = {
        'earth': ATTRIBUTE_EARTH, 'water': ATTRIBUTE_WATER,
        'fire': ATTRIBUTE_FIRE, 'wind': ATTRIBUTE_WIND,
        'light': ATTRIBUTE_LIGHT, 'dark': ATTRIBUTE_DARK,
        'divine': ATTRIBUTE_DIVINE
    }
    return mapping.get((attr or '').lower(), 0)

def parse_race(race):
    mapping = {
        'warrior': RACE_WARRIOR, 'spellcaster': RACE_SPELLCASTER,
        'fairy': RACE_FAIRY, 'fiend': RACE_FIEND, 'zombie': RACE_ZOMBIE,
        'machine': RACE_MACHINE, 'aqua': RACE_AQUA, 'pyro': RACE_PYRO,
        'rock': RACE_ROCK, 'wingedbeast': RACE_WINGEDBEAST,
        'winged beast': RACE_WINGEDBEAST, 'plant': RACE_PLANT,
        'insect': RACE_INSECT, 'thunder': RACE_THUNDER,
        'dragon': RACE_DRAGON, 'beast': RACE_BEAST,
        'beastwarrior': RACE_BEASTWARRIOR, 'beast-warrior': RACE_BEASTWARRIOR,
        'dinosaur': RACE_DINOSAUR, 'fish': RACE_FISH,
        'seaserpent': RACE_SEASERPENT, 'sea serpent': RACE_SEASERPENT,
        'reptile': RACE_REPTILE, 'psychic': RACE_PSYCHIC,
        'wyrm': RACE_WYRM, 'cyberse': RACE_CYBERSE, 'illusion': RACE_ILLUSION
    }
    return mapping.get((race or '').lower(), 0)

def parse_level(level, scale, ctype, csubtype, link_arrows):
    if not level:
        return 0
    csub_l = (csubtype or '').lower()
    
    # If link monster, def is arrow mask and level is link rating
    if 'link' in csub_l:
        return int(level)
        
    val = int(level) & 0xFF
    if scale is not None:
        left_scale = (int(scale) & 0xFF) << 24
        right_scale = (int(scale) & 0xFF) << 16
        val |= (left_scale | right_scale)
    return val

def parse_link_arrows(arrows_str):
    if not arrows_str:
        return 0
    val = 0
    parts = [p.strip().upper() for p in arrows_str.replace(';', ',').split(',')]
    for p in parts:
        if p in LINK_MAP:
            val |= LINK_MAP[p]
    return val

def build_cdb(story_db=STORY_DB_PATH, cdb_out=CDB_OUTPUT_PATH):
    print(f"[*] Building CDB from {story_db} -> {cdb_out}...")
    os.makedirs(os.path.dirname(cdb_out), exist_ok=True)
    
    # Connect to story database
    story_conn = sqlite3.connect(story_db)
    story_cur = story_conn.cursor()
    
    # Connect / create CDB
    cdb_conn = sqlite3.connect(cdb_out)
    cdb_cur = cdb_conn.cursor()
    
    # Create standard YGOPro CDB schema
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
    
    story_cur.execute("""
        SELECT id, name, card_type, card_subtype, attribute, monster_type,
               level_or_rank_or_link, scale, atk, def, link_arrows,
               effect_text, pendulum_effect
        FROM custom_cards
    """)
    
    cards = story_cur.fetchall()
    count = 0
    
    for card in cards:
        (cid, name, ctype, csubtype, attribute, monster_type,
         level, scale, atk, defense, link_arrows, effect_text, pendulum_effect) = card
        
        c_type = parse_card_type(ctype, csubtype)
        c_attr = parse_attribute(attribute)
        c_race = parse_race(monster_type)
        c_lvl = parse_level(level, scale, ctype, csubtype, link_arrows)
        
        c_atk = atk if atk is not None else 0
        
        # Link monster defense field holds link arrows
        if (csubtype or '').lower() == 'link':
            c_def = parse_link_arrows(link_arrows)
        else:
            c_def = defense if defense is not None else 0
            
        full_desc = effect_text
        if pendulum_effect:
            full_desc = f"[ Pendulum Effect ]\n{pendulum_effect}\n----------------------------------------\n[ Monster Effect ]\n{effect_text}"
            
        # Insert / replace into datas
        cdb_cur.execute("""
            INSERT OR REPLACE INTO datas (
                id, ot, alias, setcode, type, atk, def, level, race, attribute, category
            ) VALUES (?, 4, 0, 0, ?, ?, ?, ?, ?, ?, 0)
        """, (cid, c_type, c_atk, c_def, c_lvl, c_race, c_attr))
        
        # Insert / replace into texts
        cdb_cur.execute("""
            INSERT OR REPLACE INTO texts (
                id, name, desc
            ) VALUES (?, ?, ?)
        """, (cid, name, full_desc))
        
        count += 1
        
    cdb_conn.commit()
    cdb_conn.close()
    story_conn.close()
    print(f"[+] Successfully synchronized {count} cards into {cdb_out}!")

if __name__ == "__main__":
    build_cdb()
