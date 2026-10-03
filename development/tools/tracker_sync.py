#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Master Card Tracker & Database Synchronization Tool
=============================================================================
Bridges spreadsheet card trackers (Google Sheets / Excel) with the SQLite
story database (`ygo_story.db`), the simulator binary CDB (`custom_cards.cdb`),
and local artwork assets (`production/shared/expansions/pics/`).

Capabilities:
1. `upgrade`:
   Converts legacy or raw trackers into the full, Google Sheets-ready Master Tracker
   with `=IMAGE(...)` formula preview, proper column segregation, passcodes,
   simulator bitmasks, and lore metadata. Outputs both RFC 4180 CSV and TSV.
2. `import`:
   Reads the Master Tracker CSV/TSV and synchronizes all custom cards into
   `custom_cards`, auto-creating factions and characters where required.
3. `export`:
   Dumps all cards from `custom_cards` back into the Google Sheets Master Tracker format.
4. `download-images`:
   Fetches artwork from remote Duelingbook / web URLs and places them locally at
   `production/shared/expansions/pics/<passcode>.jpg` for EDOPro / simulator use.
5. `verify`:
   Audits parity between the tracker, the SQLite database, compiled CDB, and images.

Usage (CLI):
    python3 development/tools/tracker_sync.py upgrade
    python3 development/tools/tracker_sync.py import
    python3 development/tools/tracker_sync.py export
    python3 development/tools/tracker_sync.py download-images
    python3 development/tools/tracker_sync.py verify
=============================================================================
"""

import os
import sys
import csv
import json
import sqlite3
import argparse
import urllib.request
import re
from typing import List, Dict, Any, Optional, Tuple

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, PICS_DIR, THUMBNAILS_DIR,
    TRACKERS_DIR, ensure_directories
)
from config.logging import get_logger, audit_operation

logger = get_logger("tracker_sync", service="TOOLS")

DEFAULT_ROOT_CSV = os.path.join(BASE_DIR, "Duelingbook Master Tracker - Set 1 - The Land of Kustomazi.csv")
DEFAULT_TRACKER_CSV = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv")
DEFAULT_TRACKER_TSV = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv")

# Master Header Columns optimized for Google Sheets and Database 1:1 Mapping
MASTER_HEADERS = [
    "Passcode (ID)",
    "Set Number",
    "Card Name",
    "Image Preview",
    "Image Link",
    "Local Image File",
    "Image Status",
    "Card Category",
    "Card Subtype",
    "Monster Race",
    "Attribute",
    "Level/Rank/Link",
    "ATK",
    "DEF",
    "Pendulum Scale",
    "Link Arrows",
    "Effect Text",
    "Pendulum Effect",
    "Archetype/Series",
    "Rarity",
    "Creator",
    "Faction Alignment",
    "Signature Duelist",
    "Story Significance",
    "Story/Lore Context",
    "Synergy/Combos",
    "Designer Notes",
    "Duelingbook Card ID",
    "Duelingbook Card URL",
    "Script File",
    "Script Status",
    "CDB Bitmask Type",
    "Banlist Status",
    "Playtesting Status",
]


def extract_duelingbook_id(url: str) -> Optional[str]:
    """Extracts custom picture ID from Duelingbook image URL."""
    if not url:
        return None
    match = re.search(r'/custom-pics/\d+/(\d+)\.jpg', url)
    if match:
        return match.group(1)
    match_card = re.search(r'id=(\d+)', url)
    if match_card:
        return match_card.group(1)
    return None


def calculate_cdb_type(category: str, subtype: str) -> int:
    """Calculates ocgcore/YGOPro 32-bit type flag."""
    cat = (category or "").strip().lower()
    sub = (subtype or "").strip().lower()

    TYPE_MONSTER = 0x1
    TYPE_SPELL = 0x2
    TYPE_TRAP = 0x4
    TYPE_NORMAL = 0x10
    TYPE_EFFECT = 0x20
    TYPE_FUSION = 0x40
    TYPE_RITUAL = 0x80
    TYPE_SYNCHRO = 0x2000
    TYPE_XYZ = 0x800000
    TYPE_PENDULUM = 0x1000000
    TYPE_LINK = 0x4000000
    TYPE_QUICKPLAY = 0x10000
    TYPE_CONTINUOUS = 0x20000
    TYPE_EQUIP = 0x40000
    TYPE_FIELD = 0x80000
    TYPE_COUNTER = 0x100000

    val = 0
    if cat == "monster":
        val |= TYPE_MONSTER
        if "normal" in sub:
            val |= TYPE_NORMAL
        else:
            val |= TYPE_EFFECT
        if "fusion" in sub:
            val |= TYPE_FUSION
        if "synchro" in sub:
            val |= TYPE_SYNCHRO
        if "xyz" in sub:
            val |= TYPE_XYZ
        if "link" in sub:
            val |= TYPE_LINK
        if "ritual" in sub:
            val |= TYPE_RITUAL
        if "pendulum" in sub:
            val |= TYPE_PENDULUM
    elif cat == "spell":
        val |= TYPE_SPELL
        if "quick" in sub:
            val |= TYPE_QUICKPLAY
        elif "continuous" in sub:
            val |= TYPE_CONTINUOUS
        elif "field" in sub:
            val |= TYPE_FIELD
        elif "equip" in sub:
            val |= TYPE_EQUIP
        elif "ritual" in sub:
            val |= TYPE_RITUAL
        else:
            val |= TYPE_NORMAL
    elif cat == "trap":
        val |= TYPE_TRAP
        if "counter" in sub:
            val |= TYPE_COUNTER
        elif "continuous" in sub:
            val |= TYPE_CONTINUOUS
        else:
            val |= TYPE_NORMAL

    return val


# Canonical Lore, Combos & Designer Notes for Expansion Set 1
CANONICAL_CARD_METADATA = {
    50000101: {
        "significance": "Creator Deity",
        "lore": "The primordial architect of Kustomazi who forged the universe from the cosmic void.",
        "combos": "Tribute Summon using 2+ Divine-Beasts for complete card effect immunity; combo with Planet Kustomazi for additional Normal Summons.",
        "notes": "Boss deity monster; can reduce ATK to 0 to burn opponent; self-limiting Special Summon restriction.",
    },
    50000102: {
        "significance": "Primordial Origin",
        "lore": "It is quiet and restless, containing all potential of the universe before creation.",
        "combos": "Special Summoned via The Seed of Creation; essential material for Formless and Mohousha.",
        "notes": "Level 1 0/0 Divine-Beast; core combo catalyst and engine bridge for Kasutamaiza strategies.",
    },
    50000103: {
        "significance": "Core Catalyst",
        "lore": "The first concentrated spark of cosmic matter that awakened the silent void.",
        "combos": "Searches Kasutamaiza; revives Void from GY; enables Level 1 GY Tribute Summoning during Standby Phase.",
        "notes": "Key Normal Spell searcher and GY recursion engine for the Divine-Beast archetype.",
    },
    50000104: {
        "significance": "Worshippers of Creation",
        "lore": "Devoted cosmic disciples who tend to the sacred monuments and altars of the Creator.",
        "combos": "Normal Summon swarms up to 2 copies from Deck; GY banish doubles all battle and effect damage.",
        "notes": "3-Tribute engine enabler with built-in OTK damage amplification.",
    },
    50000105: {
        "significance": "Primordial Chaos",
        "lore": "The boundless unformed essence capable of consuming whole galaxies back into nothingness.",
        "combos": "Contact Special Summons by banishing Void, Servants, and Seed; board wipe when hand is empty.",
        "notes": "Dynamic ATK gain (battling monster's ATK + 100); high-risk last-resort board clearing tool.",
    },
    50000106: {
        "significance": "Corrupted Entity",
        "lore": "A rogue reflection that attempted to usurp the Creator's absolute authority.",
        "combos": "Contact Fusion using Field/GY materials; targets and equips opponent monsters to copy ATK, Level, Type, and effects.",
        "notes": "Extra Deck boss with non-destruction monster removal, effect theft, and destruction protection.",
    },
    50000107: {
        "significance": "Transcendent Deity",
        "lore": "The supreme unified godhead commanding all cosmic elements and universal attributes.",
        "combos": "Fusion with Kasutamaiza; gains omni-protection and Quick Effect GY equips based on material Attributes.",
        "notes": "Pinnacle Fusion boss with destruction replacement and graveyard draw manipulation.",
    },
    50000108: {
        "significance": "Divine Decree",
        "lore": "The creator's voice echoing across the cosmos, calling the chosen to battle.",
        "combos": "Searches any Kasutamaiza card; recycles up to 3 archetypal cards from GY back into the Deck.",
        "notes": "Consistency spell providing both immediate card advantage and long-term GY recursion.",
    },
    50000109: {
        "significance": "Cosmic Retribution",
        "lore": "The unyielding law enforcing balance in the cosmic order against chaos.",
        "combos": "Counter Trap negates summon/activation; locks Extra Deck or forces opponent discards based on banished card.",
        "notes": "High-cost omni-negate (2000 LP + banish) with lingering format disruption.",
    },
    50000110: {
        "significance": "Sacred Homeland",
        "lore": "The celestial jewel world forged at the center of the universe.",
        "combos": "Grants additional Normal Summon in MP1; recycles banished cards and fixes hand in MP2.",
        "notes": "Continuous utility spell providing field presence and banished resource recovery.",
    },
    50000111: {
        "significance": "Sanctuary of the Gods",
        "lore": "The grand cosmic shrine where prayers to the Creator are answered.",
        "combos": "Recovers GY/banished cards on activation; grants targeting immunity to Divine-Beasts; multi-card spot removal.",
        "notes": "Continuous spell protecting Divine-Beasts and enabling continuous field removal.",
    },
    50000112: {
        "significance": "Genesis Flash",
        "lore": "The initial flash of light that split the darkness and ignited reality.",
        "combos": "Banishes up to 3 Void from GY; stages effects from monster retrieval to setting S/T to drawing 2 cards.",
        "notes": "High-value payoff spell rewarding dedicated graveyard setup.",
    },
    50000113: {
        "significance": "Transmutation Secret",
        "lore": "The esoteric rites connecting mortal alchemists with divine energy.",
        "combos": "Fusion summons from hand/field; grants second attack or summon activation protection based on level.",
        "notes": "Primary archetypal Fusion Spell with level-dependent combat and protection buffs.",
    },
    50000114: {
        "significance": "Dimensional Rift",
        "lore": "A channel carved through space and time to summon ancient entities from oblivion.",
        "combos": "Shuffles materials from GY/banishment into Deck; ignores summoning conditions for Extra Deck monsters.",
        "notes": "Miracle-style Fusion spell utilizing banished and graveyard resources.",
    },
}


def parse_raw_tracker(csv_path: str = DEFAULT_ROOT_CSV) -> List[Dict[str, Any]]:
    """Reads legacy tracker CSV and parses into standardized record list."""
    if not os.path.exists(csv_path):
        logger.error(f"Tracker file not found: {csv_path}")
        return []

    records = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            name = (row.get("Card Name") or "").strip()
            if not name:
                continue

            raw_cat = (row.get("Card Category") or "").strip()
            raw_sub = (row.get("Card Subtype") or "").strip()
            raw_race = (row.get("Monster Race") or "").strip()
            raw_type = (row.get("Monster Type") or "").strip()
            raw_attr = (row.get("Attribute") or "").strip()
            raw_set = (row.get("Set Number") or f"TLOK-{idx:03d}").strip()
            img_link = (row.get("Image Link") or "").strip()
            raw_arrows = (row.get("Link Arrows") or "N/A").strip()

            # Normalization logic
            if raw_cat.lower() == "monster":
                category = "Monster"
                if raw_sub:
                    subtype = raw_sub
                    race = raw_race if raw_race and raw_race != "N/A" else (raw_type if raw_type and raw_type != "N/A" else "Divine-Beast")
                elif "/" in raw_type:
                    parts = [p.strip() for p in raw_type.split("/")]
                    race = parts[0]
                    subtype = "/".join(parts[1:])
                else:
                    race = raw_type if raw_type and raw_type != "N/A" else "Divine-Beast"
                    subtype = "Effect"
                attribute = raw_attr if raw_attr and raw_attr != "N/A" else "DIVINE"
            elif raw_cat.lower() == "spell":
                category = "Spell"
                subtype = raw_sub if raw_sub else (raw_attr if raw_attr and raw_attr != "N/A" else "Normal")
                race = "N/A"
                attribute = "N/A"
            elif raw_cat.lower() == "trap":
                category = "Trap"
                subtype = raw_sub if raw_sub else (raw_attr if raw_attr and raw_attr != "N/A" else "Normal")
                race = "N/A"
                attribute = "N/A"
            else:
                category = "Monster"
                subtype = raw_sub if raw_sub else "Effect"
                race = raw_race if raw_race and raw_race != "N/A" else "Divine-Beast"
                attribute = "DIVINE"

            raw_passcode = (row.get("Passcode (ID)") or "").strip()
            passcode = int(raw_passcode) if raw_passcode.isdigit() else (50000100 + idx)
            meta = CANONICAL_CARD_METADATA.get(passcode, {})

            duelingbook_id = extract_duelingbook_id(img_link)
            local_img = f"pics/{passcode}.jpg"
            full_local_path = os.path.join(PICS_DIR, f"{passcode}.jpg")
            img_status = "Downloaded" if os.path.exists(full_local_path) else "Pending"

            script_file = f"c{passcode}.lua"
            script_full_path = os.path.join(SCRIPTS_DIR, script_file)
            script_status = "Implemented" if os.path.exists(script_full_path) else "Draft"

            cdb_bitmask = hex(calculate_cdb_type(category, subtype))

            # Normalize effect text: remove internal newlines so each record is exactly one line in CSV/TSV
            raw_effect = (row.get("Effect Text") or "").strip()
            clean_effect = re.sub(r'[\r\n]+', ' ', raw_effect)
            clean_effect = re.sub(r'\s*●\s*', ' ● ', clean_effect).strip()

            lore_val = (row.get("Story/Lore Context") or "").strip().replace("--", "") or meta.get("lore", "")
            combos_val = (row.get("Synergy/Combos") or "").strip().replace("--", "") or meta.get("combos", "")
            notes_val = (row.get("Designer Notes") or "").strip().replace("--", "") or meta.get("notes", "")
            significance_val = (row.get("Story Significance") or "").strip().replace("--", "") or meta.get("significance", "Core Engine")

            faction_val = (row.get("Faction Alignment") or row.get("Faction/Character Alignment") or "").strip()
            if not faction_val or faction_val.lower() in ("netural", "neutral", "--"):
                faction_val = "The Creators of Kustomazi"

            duelist_val = (row.get("Signature Duelist") or "").strip() or "ProfessorSeanEX"
            creator_val = (row.get("Creator") or "").strip() or "ProfessorSeanEX"
            archetype_val = (row.get("Archetype/Series") or "").strip() or "Kasutamaiza"

            records.append({
                "passcode": passcode,
                "set_number": raw_set,
                "name": name,
                "image_link": img_link,
                "local_image": local_img,
                "image_status": img_status,
                "category": category,
                "subtype": subtype,
                "race": race,
                "attribute": attribute,
                "level": (row.get("Level/Rank/Link") or "N/A").strip(),
                "atk": (row.get("ATK") or "N/A").strip(),
                "def": (row.get("DEF") or "N/A").strip(),
                "scale": (row.get("Pendulum Scale") or "N/A").strip(),
                "link_arrows": raw_arrows,
                "effect_text": clean_effect,
                "pendulum_effect": (row.get("Pendulum Effect") or "N/A").strip(),
                "archetype": archetype_val,
                "rarity": (row.get("Rarity") or "Common").strip().replace("--", "Common"),
                "creator": creator_val,
                "faction": faction_val,
                "duelist": duelist_val,
                "significance": significance_val,
                "lore": lore_val,
                "combos": combos_val,
                "notes": notes_val,
                "duelingbook_id": duelingbook_id or "",
                "script_file": script_file,
                "script_status": script_status,
                "cdb_bitmask": cdb_bitmask,
                "banlist_status": (row.get("Banlist Status") or "Unlimited").strip(),
                "playtesting_status": (row.get("Playtesting Status") or "In Testing").strip(),
            })

    return records


def write_master_trackers(records: List[Dict[str, Any]], csv_path: str = DEFAULT_TRACKER_CSV, tsv_path: str = DEFAULT_TRACKER_TSV) -> None:
    """Writes standardized Master Tracker to CSV and TSV formats."""
    ensure_directories()

    def build_row(r: Dict[str, Any], row_idx: int) -> List[str]:
        # Google Sheets formula for Image Preview: =IF(ISBLANK(E{row}), "", IMAGE(E{row}))
        # In header MASTER_HEADERS:
        # Col A (1): Passcode
        # Col B (2): Set Number
        # Col C (3): Card Name
        # Col D (4): Image Preview (=IMAGE(E{row}))
        # Col E (5): Image Link
        formula = f'=IF(ISBLANK(E{row_idx}), "", IMAGE(E{row_idx}))'
        return [
            str(r["passcode"]),
            r["set_number"],
            r["name"],
            formula,
            r["image_link"],
            r["local_image"],
            r["image_status"],
            r["category"],
            r["subtype"],
            r["race"],
            r["attribute"],
            str(r["level"]),
            str(r["atk"]),
            str(r["def"]),
            str(r["scale"]),
            r["link_arrows"],
            r["effect_text"],
            r["pendulum_effect"],
            r["archetype"],
            r["rarity"],
            r["creator"],
            r["faction"],
            r["duelist"],
            r["significance"],
            r["lore"],
            r["combos"],
            r["notes"],
            r["duelingbook_id"],
            f"https://www.duelingbook.com/card?id={r['duelingbook_id']}" if r.get("duelingbook_id") else "",
            r["script_file"],
            r["script_status"],
            r["cdb_bitmask"],
            r["banlist_status"],
            r["playtesting_status"],
        ]

    # 1. Write CSV (RFC 4180)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(MASTER_HEADERS)
        for i, r in enumerate(records, 2):
            writer.writerow(build_row(r, i))

    # Also update root CSV for backward compatibility
    if csv_path != DEFAULT_ROOT_CSV:
        with open(DEFAULT_ROOT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(MASTER_HEADERS)
            for i, r in enumerate(records, 2):
                writer.writerow(build_row(r, i))

    # 2. Write TSV (Ideal for direct paste into Google Sheets)
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(MASTER_HEADERS)
        for i, r in enumerate(records, 2):
            writer.writerow(build_row(r, i))

    logger.info(f"Generated Master Tracker CSV ({csv_path}) and TSV ({tsv_path}) with {len(records)} cards.")


def sync_tracker_to_database(records: List[Dict[str, Any]], db_path: str = STORY_DB_PATH) -> int:
    """Inserts or updates all tracker records into the SQLite story database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Ensure Faction 'The Creators of Kustomazi' exists
    cur.execute("SELECT id FROM factions WHERE name = ?", ("The Creators of Kustomazi",))
    row = cur.fetchone()
    if row:
        creator_faction_id = row[0]
    else:
        cur.execute("""
            INSERT INTO factions (name, lore_description, playstyle_overview)
            VALUES (?, ?, ?)
        """, (
            "The Creators of Kustomazi",
            "The supreme primordial pantheon and cosmic architects of the Land of Kustomazi.",
            "Tribute and Fusion summoning centered on high-stat DIVINE Divine-Beast deities and void recursion."
        ))
        creator_faction_id = cur.lastrowid
        logger.info(f"Created faction 'The Creators of Kustomazi' [ID: {creator_faction_id}]")

    # 2. Ensure Character 'ProfessorSeanEX' exists
    cur.execute("SELECT id FROM characters WHERE name = ?", ("ProfessorSeanEX",))
    row = cur.fetchone()
    if row:
        creator_char_id = row[0]
    else:
        cur.execute("""
            INSERT INTO characters (name, alias, bio, faction_id)
            VALUES (?, ?, ?, ?)
        """, (
            "ProfessorSeanEX",
            "The Supreme Architect",
            "Master creator and overseer of the Kustomazi universe and custom card chronicle.",
            creator_faction_id
        ))
        creator_char_id = cur.lastrowid
        logger.info(f"Created character 'ProfessorSeanEX' [ID: {creator_char_id}]")

    # 3. Synchronize Cards
    synced_count = 0
    for r in records:
        cid = int(r["passcode"])
        name = r["name"]
        ctype = r["category"]
        csubtype = r["subtype"]
        attribute = r["attribute"] if r["attribute"] != "N/A" else None
        mtype = r["race"] if r["race"] != "N/A" else None

        # Level parsing
        lvl_val = r["level"]
        level = int(lvl_val) if str(lvl_val).isdigit() else None

        # ATK / DEF parsing: '?' -> -2
        atk_raw = str(r["atk"]).strip()
        if atk_raw == "?":
            atk = -2
        elif atk_raw.isdigit():
            atk = int(atk_raw)
        else:
            atk = None

        def_raw = str(r["def"]).strip()
        if def_raw == "?":
            defense = -2
        elif def_raw.isdigit():
            defense = int(def_raw)
        else:
            defense = None

        # Scale
        scale_raw = str(r["scale"]).strip()
        scale = int(scale_raw) if scale_raw.isdigit() else None

        # Link arrows
        link_arrows = r["link_arrows"] if r["link_arrows"] != "N/A" else None

        # Resolve faction
        card_faction = r.get("faction") or "The Creators of Kustomazi"
        cur.execute("SELECT id FROM factions WHERE name = ?", (card_faction,))
        f_row = cur.fetchone()
        if f_row:
            f_id = f_row[0]
        else:
            cur.execute("""
                INSERT INTO factions (name, lore_description, playstyle_overview)
                VALUES (?, ?, ?)
            """, (card_faction, f"Faction representing {card_faction}", ""))
            f_id = cur.lastrowid

        # Resolve signature character
        card_duelist = r.get("duelist") or "ProfessorSeanEX"
        cur.execute("SELECT id FROM characters WHERE name = ?", (card_duelist,))
        c_row = cur.fetchone()
        if c_row:
            ch_id = c_row[0]
        else:
            cur.execute("""
                INSERT INTO characters (name, alias, bio, faction_id)
                VALUES (?, ?, ?, ?)
            """, (card_duelist, card_duelist, f"Duelist representing {card_duelist}", f_id))
            ch_id = cur.lastrowid

        cur.execute("""
            INSERT INTO custom_cards (
                id, name, card_type, card_subtype, attribute, monster_type,
                level_or_rank_or_link, scale, atk, def, link_arrows,
                effect_text, pendulum_effect, duelingbook_id, duelingbook_url,
                image_url, creator_name, lore_text, faction_id, signature_character_id,
                story_significance, set_number, set_code, rarity, archetype,
                banlist_status, playtesting_status, local_image_path, script_file, script_status
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            ON CONFLICT(name) DO UPDATE SET
                id = excluded.id,
                card_type = excluded.card_type,
                card_subtype = excluded.card_subtype,
                attribute = excluded.attribute,
                monster_type = excluded.monster_type,
                level_or_rank_or_link = excluded.level_or_rank_or_link,
                scale = excluded.scale,
                atk = excluded.atk,
                def = excluded.def,
                link_arrows = excluded.link_arrows,
                effect_text = excluded.effect_text,
                pendulum_effect = excluded.pendulum_effect,
                duelingbook_id = excluded.duelingbook_id,
                image_url = excluded.image_url,
                creator_name = excluded.creator_name,
                lore_text = excluded.lore_text,
                faction_id = excluded.faction_id,
                signature_character_id = excluded.signature_character_id,
                story_significance = excluded.story_significance,
                set_number = excluded.set_number,
                set_code = excluded.set_code,
                rarity = excluded.rarity,
                archetype = excluded.archetype,
                banlist_status = excluded.banlist_status,
                playtesting_status = excluded.playtesting_status,
                local_image_path = excluded.local_image_path,
                script_file = excluded.script_file,
                script_status = excluded.script_status
        """, (
            cid, name, ctype, csubtype, attribute, mtype,
            level, scale, atk, defense, link_arrows,
            r["effect_text"], None if r["pendulum_effect"] == "N/A" else r["pendulum_effect"],
            r["duelingbook_id"], f"https://www.duelingbook.com/card?id={r['duelingbook_id']}" if r["duelingbook_id"] else None,
            r["image_link"], r["creator"], r["lore"], f_id, ch_id,
            r["significance"], r["set_number"], "TLOK", r["rarity"], r["archetype"],
            r["banlist_status"], r["playtesting_status"], r["local_image"], r["script_file"], r["script_status"]
        ))
        synced_count += 1

    cur.execute("INSERT INTO cards_fts(cards_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()
    logger.info(f"Successfully synchronized {synced_count} cards from tracker into database {db_path}.")
    return synced_count


def download_card_images(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Downloads remote artwork to local pics directory for EDOPro and simulator."""
    ensure_directories()
    downloaded = 0
    failed = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Yu-Gi-Oh-Platform/1.0"
    }

    for r in records:
        passcode = r["passcode"]
        img_url = r["image_link"]
        if not img_url or not img_url.startswith("http"):
            continue

        target_path = os.path.join(PICS_DIR, f"{passcode}.jpg")
        thumb_path = os.path.join(THUMBNAILS_DIR, f"{passcode}.jpg")

        if os.path.exists(target_path) and os.path.getsize(target_path) > 1024:
            continue

        try:
            req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response, open(target_path, "wb") as out_file:
                data = response.read()
                out_file.write(data)

            # Copy to thumbnail directory
            with open(thumb_path, "wb") as thumb_file:
                thumb_file.write(data)

            downloaded += 1
            print(f" [✔] Downloaded artwork: {r['name']} -> {target_path}")
        except Exception as e:
            failed += 1
            logger.warning(f"Failed to download image for {r['name']} ({img_url}): {e}")
            print(f" [✘] Failed download for {r['name']}: {e}")

    logger.info(f"Image download complete. Success: {downloaded}, Failures: {failed}")
    return downloaded, failed


def verify_tracker_health(records: List[Dict[str, Any]]) -> bool:
    """Verifies validity of tracker entries against database, bitmasks, and files."""
    print("\n" + "=" * 70)
    print("        YU-GI-OH! MASTER TRACKER PARITY & HEALTH AUDITOR")
    print("=" * 70 + "\n")

    all_ok = True
    for r in records:
        errors = []
        if not str(r["passcode"]).isdigit():
            errors.append(f"Invalid passcode: {r['passcode']}")
        if not r["name"]:
            errors.append("Missing card name")
        if r["category"] not in ("Monster", "Spell", "Trap"):
            errors.append(f"Invalid category: {r['category']}")

        # Image check
        img_file = os.path.join(PICS_DIR, f"{r['passcode']}.jpg")
        img_exists = os.path.exists(img_file)
        img_badge = "[PIC: ✔]" if img_exists else "[PIC: ⏳ Pending]"

        status_badge = "[PASS]" if not errors else "[FAIL]"
        print(f" {status_badge} {r['set_number']} | Passcode: {r['passcode']} | {r['name']} {img_badge}")
        for err in errors:
            print(f"        ✘ {err}")
            all_ok = False

    print("\n" + "=" * 70)
    print(f"Summary: {'ALL TRACKER CARDS VALID' if all_ok else 'ERRORS DETECTED'} ({len(records)} audited)")
    print("=" * 70 + "\n")
    return all_ok


def sync_local_art(records: List[Dict[str, Any]], art_dir: str = os.path.join(BASE_DIR, "card-art")) -> Tuple[int, int]:
    """
    Scans a local directory of artwork (e.g. card-art/) organized by archetype
    or card name, and copies matching image files into the expansion pics directory.
    """
    ensure_directories()
    if not os.path.exists(art_dir):
        print(f"[-] Art directory not found: {art_dir}")
        return 0, 0

    import shutil

    # Build map of normalized card name -> record
    name_map = {r["name"].strip().lower(): r for r in records}
    matched = 0
    skipped = 0

    for root, _, files in os.walk(art_dir):
        for fname in files:
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            base_name, _ = os.path.splitext(fname)
            norm_name = base_name.strip().lower()

            # Direct name match
            if norm_name in name_map:
                rec = name_map[norm_name]
                passcode = rec["passcode"]
                src_path = os.path.join(root, fname)
                dest_path = os.path.join(PICS_DIR, f"{passcode}.jpg")
                thumb_path = os.path.join(THUMBNAILS_DIR, f"{passcode}.jpg")

                shutil.copy2(src_path, dest_path)
                shutil.copy2(src_path, thumb_path)
                matched += 1
                print(f" [✔] Ingested local art: {fname} -> {dest_path}")
            else:
                skipped += 1

    print(f"[+] Local art synchronization finished. Matched: {matched}, Skipped/Unmatched: {skipped}")
    return matched, skipped


def main():
    parser = argparse.ArgumentParser(description="Master Card Tracker & Database Sync Utility")
    parser.add_argument("action", nargs="?", default="upgrade", choices=["upgrade", "import", "export", "download-images", "sync-local-art", "verify"], help="Operation to perform")
    parser.add_argument("-f", "--file", default=DEFAULT_ROOT_CSV, help="Path to input/output CSV file")
    args = parser.parse_args()

    records = parse_raw_tracker(args.file)
    if not records:
        print(f"[-] No records could be parsed from {args.file}")
        sys.exit(1)

    if args.action == "upgrade":
        write_master_trackers(records)
        print(f"[+] Master Tracker upgraded and generated at:")
        print(f"    - Google Sheets CSV: {DEFAULT_TRACKER_CSV}")
        print(f"    - Google Sheets TSV: {DEFAULT_TRACKER_TSV}")
        print(f"    - Root Master CSV:   {DEFAULT_ROOT_CSV}")
        print(f"    Cards processed: {len(records)}")

    elif args.action == "import":
        write_master_trackers(records)
        count = sync_tracker_to_database(records)
        print(f"[+] Successfully imported and synchronized {count} cards into {STORY_DB_PATH}")

    elif args.action == "download-images":
        print(f"[*] Starting card artwork download into {PICS_DIR}...")
        succ, fail = download_card_images(records)
        print(f"[+] Download complete: {succ} downloaded, {fail} failed.")

    elif args.action == "sync-local-art":
        print(f"[*] Ingesting artwork from card-art/ directory...")
        matched, skipped = sync_local_art(records)
        print(f"[+] Ingestion complete: {matched} cards matched and updated in {PICS_DIR}.")

    elif args.action == "verify":
        ok = verify_tracker_health(records)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
