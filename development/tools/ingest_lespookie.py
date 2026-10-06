#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator - LeSpookie Commons Ingestion Pipeline
=============================================================================
Ingests all 50 cards from Duelingbook deck 8114120 ("LeSpookie Singles")
into:
1. SQLite Authoritative Content Database (`data/authoritative/content.db`)
2. Master Trackers (CSV and TSV in `data/trackers/`)
3. Simulator Binary Database (`data/expansions/custom_cards.cdb`)
4. Local Artwork Cache (`data/expansions/pics/*.jpg`)
5. Pre-built Story Deck (`data/decks/LeSpookie Singles.ydk`)
6. Story Mode Campaign (Chapter 2: The LeSpookiest Night, Stages 2-1 to 2-3)
=============================================================================
"""

import os
import sys
import json
import sqlite3
import re
import csv
import urllib.request
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, PICS_DIR, TRACKERS_DIR,
    DECKS_DIR, SCRIPTS_DIR, ensure_directories
)
from development.tools.cdb_builder import build_cdb, parse_card_type
from development.tools.constants import LINK_ARROW_MAP

TRACKER_CSV = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv")
ROOT_TRACKER_CSV = TRACKER_CSV
TRACKER_TSV = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv")

# Duelingbook arrow bit order -> compass string
DB_ARROW_MAP = [
    "TL",  # 0: Top Left
    "T",   # 1: Top Center
    "TR",  # 2: Top Right
    "R",   # 3: Middle Right
    "BR",  # 4: Bottom Right
    "B",   # 5: Bottom Center
    "BL",  # 6: Bottom Left
    "L",   # 7: Middle Left
]


def convert_db_arrows(arrows_str: Optional[str]) -> str:
    """Converts Duelingbook 8-character arrow string into comma-separated compass string."""
    if not arrows_str or len(arrows_str) != 8:
        return "N/A"
    active = [DB_ARROW_MAP[i] for i, ch in enumerate(arrows_str) if ch == "1"]
    return ",".join(active) if active else "N/A"


def determine_card_subtypes(card: Dict[str, Any]) -> Tuple[str, str]:
    """
    Returns (card_type, card_subtype) normalized for content.db and cdb_builder.
    """
    ctype = card.get("card_type", "Monster")
    mcolor = (card.get("monster_color") or "").strip()
    ability = (card.get("ability") or "").strip()
    raw_type = (card.get("type") or "").strip()

    if ctype == "Monster":
        if "Synchro" in mcolor:
            subtype = "Synchro / Effect"
        elif "Link" in mcolor:
            subtype = "Link / Effect"
        elif "Gemini" in ability or "Gemini" in mcolor:
            subtype = "Gemini / Effect"
        elif "Tuner" in ability:
            subtype = "Tuner / Effect"
        elif "Normal" in mcolor:
            subtype = "Normal"
        else:
            subtype = "Effect"
        return "Monster", subtype

    elif ctype == "Spell":
        valid_spells = ["Continuous", "Field", "Quick-Play", "Equip", "Ritual", "Normal"]
        subtype = raw_type if raw_type in valid_spells else "Normal"
        return "Spell", subtype

    elif ctype == "Trap":
        valid_traps = ["Continuous", "Counter", "Normal"]
        subtype = raw_type if raw_type in valid_traps else "Normal"
        return "Trap", subtype

    return ctype, "Normal"


def determine_rarity(name: str, ctype: str, subtype: str) -> str:
    """Determines thematic rarity for cards in Set 1."""
    ultra_rares = {
        "Magnolia, the Ghost of LeSpookie Street",
        "Magnolia, Lantern Eternal of LeSpookie",
        "Magnolia, Lantern Ascended",
        "Crimson Cloak of LeSpookie Night",
        "LeSpookiest Night"
    }
    super_rares = {
        "A Wicked Shadow",
        "LeSpookie Commons, the Cursed Town of Whimsy",
        "Anubis, Entombed Guardian of LeSpookie",
        "Hexla Awakened, Witch of LeSpookie Circles",
        "Jack-O-Lantern, Spirit Spark of LeSpookie",
        "DaSpookie, Mayor of LeSpookie Street",
        "LeSpookie Street, Cursed Lane",
        "The End of LeSpookiest Night"
    }
    if name in ultra_rares:
        return "Ultra Rare"
    if name in super_rares:
        return "Super Rare"
    if "Synchro" in subtype or "Link" in subtype:
        return "Super Rare"
    return "Common"


def run_ingestion():
    ensure_directories()
    with open(JSON_DECK_PATH, "r", encoding="utf-8") as f:
        deck_data = json.load(f)

    main_cards = deck_data.get("main", [])
    extra_cards = deck_data.get("extra", [])
    total_raw_cards = main_cards + extra_cards

    print(f"[*] Ingesting {len(main_cards)} Main Deck + {len(extra_cards)} Extra Deck cards ({len(total_raw_cards)} total)...")

    # Connect to SQLite Story DB
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()

    # 1. Seed Faction 2: The LeSpookiest Night
    cur.execute("""
        INSERT INTO factions (id, name, lore_description, playstyle_overview, arc_id)
        VALUES (2, 'The LeSpookiest Night',
                'In a quiet town on Halloween night, where costumed youths trick-or-treat under bright streetlights and the shadows dance, ordinary mortals awaken as supernatural entities.',
                'Gemini and Trick-or-Treat Counter strategy that transitions Normal Monsters into supernatural Effect, Synchro, and Link evolutions.',
                1)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            lore_description = excluded.lore_description,
            playstyle_overview = excluded.playstyle_overview
    """)

    # 2. Seed Character 2: Magnolia, Ghost of LeSpookie Street
    cur.execute("""
        INSERT INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
        VALUES (2, 'Magnolia, Ghost of LeSpookie Street', 'The Lantern Maiden',
                'A wandering spirit of LeSpookie Street who guides the costumed children and dances when the shadows awaken under the streetlights.',
                2, 1, 'https://images.duelingbook.com/custom-pics/800000/831546.jpg?version=3')
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            alias = excluded.alias,
            bio = excluded.bio,
            avatar_url = excluded.avatar_url
    """)

    # Process all 50 cards
    card_records = []
    main_passcodes = []
    extra_passcodes = []

    for idx, c in enumerate(total_raw_cards, 15):
        passcode = 50000100 + idx
        set_number = f"TLOK-{idx:03d}"
        name = c["name"].strip()
        db_id = c["id"]
        folder = (int(db_id) // 100000) * 100000
        pic_ver = c.get("pic", 1)
        img_url = f"https://images.duelingbook.com/custom-pics/{folder}/{db_id}.jpg?version={pic_ver}"
        local_img = f"pics/{passcode}.jpg"
        db_card_url = f"https://www.duelingbook.com/card?id={db_id}"

        ctype, csubtype = determine_card_subtypes(c)
        attribute = c.get("attribute") if ctype == "Monster" and c.get("attribute") else None
        mtype = c.get("type") if ctype == "Monster" and c.get("type") else None

        level_val = c.get("level")
        level = int(level_val) if level_val is not None and str(level_val).isdigit() and int(level_val) > 0 else None

        # Link arrows
        raw_arrows = c.get("arrows")
        link_arrows_str = convert_db_arrows(raw_arrows) if "Link" in csubtype else "N/A"
        link_arrows_db = link_arrows_str if link_arrows_str != "N/A" else None

        # ATK / DEF
        atk_raw = str(c.get("atk", "")).strip()
        if atk_raw == "?":
            atk = -2
        elif atk_raw.isdigit():
            atk = int(atk_raw)
        else:
            atk = 0 if ctype == "Monster" else None

        def_raw = str(c.get("def", "")).strip()
        if "Link" in csubtype:
            defense = None
        elif def_raw == "?":
            defense = -2
        elif def_raw.isdigit():
            defense = int(def_raw)
        else:
            defense = 0 if ctype == "Monster" else None

        raw_effect = (c.get("effect") or "").strip()
        # Clean up effect for single-line CSV/TSV storage
        clean_effect = re.sub(r'[\r\n]+', ' ', raw_effect)
        clean_effect = re.sub(r'\s*●\s*', ' ● ', clean_effect).strip()

        rarity = determine_rarity(name, ctype, csubtype)
        archetype = "LeSpookie"
        creator = "ProfessorSeanEX"
        significance = "Boss Monster" if "Magnolia" in name or "Crimson" in name else "Core Archetype"
        lore_val = raw_effect if csubtype == "Normal" else f"Key {archetype} {csubtype} in the Halloween LeSpookie chronicle."
        combos_val = "Combines with Trick-or-Treat Counters and LeSpookie Field Spells."
        notes_val = f"Passcode {passcode} from Set 1 LeSpookie deck."
        script_file = f"c{passcode}.lua"
        script_status = "Draft"

        # CDB Bitmask
        cdb_bitmask = hex(parse_card_type(ctype, csubtype))

        # Check section
        is_extra = idx >= 51  # idx 51-64 are Extra Deck (TLOK-051 to TLOK-064)
        if is_extra:
            extra_passcodes.append(passcode)
        else:
            main_passcodes.append(passcode)

        # Insert or update in custom_cards
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
            passcode, name, ctype, csubtype, attribute, mtype,
            level, None, atk, defense, link_arrows_db,
            raw_effect, None,
            str(db_id), db_card_url,
            img_url, creator, lore_val, 2, 2,
            significance, set_number, "TLOK", rarity, archetype,
            "Unlimited", "In Testing", local_img, script_file, script_status
        ))

        # Initialize card_usage_stats
        cur.execute("""
            INSERT OR IGNORE INTO card_usage_stats (card_id, times_decked, times_drawn, times_played, wins, losses)
            VALUES (?, 0, 0, 0, 0, 0)
        """, (passcode,))

        # Build tracker dictionary
        card_records.append({
            "passcode": passcode,
            "set_number": set_number,
            "name": name,
            "image_link": img_url,
            "local_image": local_img,
            "image_status": "Downloaded" if os.path.exists(os.path.join(PICS_DIR, f"{passcode}.jpg")) else "Pending",
            "category": ctype,
            "subtype": csubtype,
            "race": mtype or "N/A",
            "attribute": attribute or "N/A",
            "level": str(level) if level is not None else "N/A",
            "atk": str(atk) if atk is not None else "N/A",
            "def": str(defense) if defense is not None else "N/A",
            "scale": "N/A",
            "link_arrows": link_arrows_str,
            "effect_text": clean_effect,
            "pendulum_effect": "N/A",
            "archetype": archetype,
            "rarity": rarity,
            "creator": creator,
            "faction": "The LeSpookiest Night",
            "duelist": "Magnolia, Ghost of LeSpookie Street",
            "significance": significance,
            "lore": lore_val,
            "combos": combos_val,
            "notes": notes_val,
            "duelingbook_id": str(db_id),
            "duelingbook_url": db_card_url,
            "script_file": script_file,
            "script_status": script_status,
            "cdb_bitmask": cdb_bitmask,
            "banlist_status": "Unlimited",
            "playtesting_status": "In Testing"
        })

    # 3. Create Deck 2: LeSpookie Singles
    ydk_lines = ["#created by ProfessorSeanEX", "#main"]
    for p in main_passcodes:
        ydk_lines.append(str(p))
    ydk_lines.append("#extra")
    for p in extra_passcodes:
        ydk_lines.append(str(p))
    ydk_lines.append("!side")
    ydk_lines.append("")
    ydk_content = "\n".join(ydk_lines)

    # Save to production/shared/decks/LeSpookie Singles.ydk
    ydk_path = os.path.join(DECKS_DIR, "LeSpookie Singles.ydk")
    with open(ydk_path, "w", encoding="utf-8") as f:
        f.write(ydk_content)
    print(f"[+] Written YDK deck to {ydk_path}")

    cur.execute("""
        INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url, ydk_content)
        VALUES (2, 'LeSpookie Singles', 2, 'ProfessorSeanEX',
                'A 50-card Gemini and trick-or-treat counter strategy featuring costumed children who enter as Normal Monsters and awaken with Gemini summon, dancing shadows, and spooky extra deck evolutions.',
                'https://www.duelingbook.com/deck?id=8114120', ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            character_id = excluded.character_id,
            description = excluded.description,
            duelingbook_deck_url = excluded.duelingbook_deck_url,
            ydk_content = excluded.ydk_content
    """, (ydk_content,))

    # Insert deck_cards for Deck 2
    cur.execute("DELETE FROM deck_cards WHERE deck_id = 2")
    for p in main_passcodes:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (2, ?, 1, 'MAIN')", (p,))
    for p in extra_passcodes:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (2, ?, 1, 'EXTRA')", (p,))

    # 4. Seed Story Chapter 2: The LeSpookiest Night
    cur.execute("""
        INSERT INTO story_chapters (id, chapter_number, title, arc_id, synopsis)
        VALUES (2, 2, 'The LeSpookiest Night', 1,
                'On a quiet Halloween night when Magnolia dances and shadows are a fright, costumed mortals awaken their inner spirits. Duel through the haunted streets and face the mysterious shadows.')
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            synopsis = excluded.synopsis
    """)

    # Stage Scripts
    stage5_script = json.dumps({
        "turns": {
            "1": {
                "play": "A chilly wind sweeps the lane. A Wicked Shadow manifests beneath the streetlamp, placing Trick-or-Treat Counters on all monsters and Normal Summoning **LeSpookie Jack, Ember of the Hollow Smile** (`TLOK-021`)!",
                "damage": 800,
                "quote": "\"When Magnolia dances and shadows are a fright... let's see if you can survive the night!\""
            },
            "2": {
                "play": "A Wicked Shadow removes 3 Trick-or-Treat Counters to conduct an instant Quick Synchro! The flames erupt into **Jack-O-Lantern, Spirit Spark of LeSpookie** (`TLOK-054`)!",
                "damage": 1200,
                "quote": "\"The embers burn bright! Feel the bite of Halloween!\""
            },
            "3": {
                "play": "The phantasm activates **LeSpookiest Trick!** (`TLOK-046`), shuffling cards and unleashing a wave of spectral fright!",
                "damage": 1500,
                "quote": "\"Trick or treat, smell my feet, give me something good to beat!\""
            }
        },
        "repeat": {
            "play": "A Wicked Shadow lashes out from the corners of the dark alley!",
            "damage": 900,
            "quote": "\"The shadows will never truly vanish!\""
        },
        "threshold_4000": "🎃 *A Wicked Shadow flickers wildly as its spectral form is destabilized! \"What an extraordinary duelist... your light burns too bright!\"*"
    })

    stage6_script = json.dumps({
        "turns": {
            "1": {
                "play": "Magnolia glides across the cobbles as lanterns ignite. Normal Summons **Magnolia, the Ghost of LeSpookie Street** (`TLOK-030`) with 2500 ATK!",
                "damage": 1000,
                "quote": "\"Every child in costume carries an inner light waiting to be awakened...\""
            },
            "2": {
                "play": "Magnolia raises her lantern! Activates **LeSpookiest Night** (`TLOK-040`), awakening her Gemini companions and Synchro Summoning **Magnolia, Lantern Eternal of LeSpookie** (`TLOK-058`) (3300 ATK)!",
                "damage": 1600,
                "quote": "\"Dance with me under the streetlights! Let the spirits celebrate!\""
            },
            "3": {
                "play": "Magnolia conducts a Link Summon into **Magnolia, Lantern Ascended** (`TLOK-064`), linking the field with radiant protective light!",
                "damage": 1800,
                "quote": "\"Our inner lives shine eternal, even when the night draws to a close!\""
            }
        },
        "repeat": {
            "play": "Magnolia's lantern radiates warm spectral energy, illuminating the entire avenue!",
            "damage": 1200,
            "quote": "\"Let the music of the quiet town continue!\""
        },
        "threshold_4000": "🏮 *Magnolia's eyes sparkle with joyful wonder! \"Breathtaking! Your bond with your cards illuminates the entire LeSpookie Commons!\"*"
    })

    stages_to_insert = [
        (4, 2, 1, 'Halloween on LeSpookie Street',
         'The autumn breeze carries the scent of caramel and fallen leaves. Children in handmade masks laugh beneath the glowing amber streetlights. But there is a peculiar resonance in the air—these aren\'t mere costumes. Tonight, the boundary between mortal whimsy and the spirit realm is gossamer-thin.',
         'The costumed trick-or-treater giggles and hands you a handful of sugary sweets. \'You duel like you really believe in magic! Keep this safe—the shadows grow longer tonight!\'',
         'Costumed Trick-or-Treater', 'Wandering Reveler', 2, 2, 'AI', 8000, None, 'Street Reveler', 50000128),
        (5, 2, 2, 'When the Shadows Are a Fright',
         'A flicker along the brick alleyway catches your eye. The streetlight flickers and dims to a pale violet hue. From the base of the lamppost, a silhouette detaches itself, grinning with needle-thin fangs. \'Trick or treat... or perhaps a duel in the dark?\'',
         'The wicked shadow dissolves into tendrils of harmless dusk. \'Hehehe... delightful! You do not flinch from the twilight. Go forth—Magnolia awaits where the lanterns burn brightest!\'',
         'A Wicked Shadow', 'Formless Phantasm', 2, 2, 'SCRIPTED', 8000, stage5_script, 'Shadow Weaver', 50000115),
        (6, 2, 3, 'The Dance of Magnolia',
         'At the town square fountain, floating jack-o\'-lanterns cast warm, undulating amber ripples. A spectral maiden with braided hair twirls softly, clutching an ancient, luminous lantern. She turns to you with gentle, ancient eyes. \'Welcome to our quiet town, traveler. When the world was created, our inner spirits were granted this sacred night. Shall we dance beneath the streetlights?\'',
         'Magnolia lowers her lantern and bows gracefully. \'Magnificent! You have embraced the spirit of the Gemini—ordinary mortals capable of wondrous, supernatural awakening. Wherever the streetlights shine, LeSpookie Commons welcomes you home.\'',
         'Magnolia, the Ghost of LeSpookie Street', 'The Lantern Maiden', 2, 2, 'SCRIPTED', 8000, stage6_script, "Lantern Maiden's Bond", 50000130)
    ]

    for s in stages_to_insert:
        cur.execute("""
            INSERT INTO story_stages (
                id, chapter_id, stage_number, title, intro_dialogue, outro_dialogue,
                opponent_name, opponent_title, opponent_character_id, opponent_deck_id,
                encounter_type, boss_hp, script_data, reward_title, reward_card_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                intro_dialogue = excluded.intro_dialogue,
                outro_dialogue = excluded.outro_dialogue,
                opponent_name = excluded.opponent_name,
                opponent_title = excluded.opponent_title,
                encounter_type = excluded.encounter_type,
                boss_hp = excluded.boss_hp,
                script_data = excluded.script_data,
                reward_title = excluded.reward_title,
                reward_card_id = excluded.reward_card_id
        """, s)

    # Rebuild FTS5 search index with all cards
    cur.execute("INSERT INTO cards_fts(cards_fts) VALUES('rebuild')")

    conn.commit()
    conn.close()
    print("[+] Successfully seeded custom_cards, decks, chapters, and stages into content.db!")

    # 5. Append rows to Master Trackers
    append_to_trackers(card_records)

    # 6. Compile CDB file
    print("[*] Recompiling custom_cards.cdb...")
    compiled = build_cdb()
    print(f"[+] Compiled {compiled} cards into {CDB_OUTPUT_PATH}!")

    # 7. Download Artwork
    print("[*] Downloading artwork for 50 LeSpookie cards...")
    download_images(card_records)


def append_to_trackers(card_records: List[Dict[str, Any]]):
    """Appends the 50 new cards to both CSV and TSV Master Trackers."""
    # Check existing lines in ROOT_TRACKER_CSV
    with open(ROOT_TRACKER_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    
    header = reader[0]
    existing_passcodes = {r[0] for r in reader[1:] if r}

    def build_tracker_row(r: Dict[str, Any], row_idx: int) -> List[str]:
        image_preview_formula = f'=IF(ISBLANK(E{row_idx}), "", IMAGE(E{row_idx}))'
        return [
            str(r["passcode"]),
            r["set_number"],
            r["name"],
            image_preview_formula,
            r["image_link"],
            r["local_image"],
            r["image_status"],
            r["category"],
            r["subtype"],
            r["race"],
            r["attribute"],
            r["level"],
            r["atk"],
            r["def"],
            r["scale"],
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
            r["duelingbook_url"],
            r["script_file"],
            r["script_status"],
            r["cdb_bitmask"],
            r["banlist_status"],
            r["playtesting_status"],
        ]

    rows_to_append = []
    current_row_idx = len(reader) + 1
    for r in card_records:
        if str(r["passcode"]) not in existing_passcodes:
            rows_to_append.append(build_tracker_row(r, current_row_idx))
            current_row_idx += 1

    if rows_to_append:
        # Append to TRACKER_CSV
        with open(TRACKER_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows_to_append)

        # Append to TRACKER_TSV
        with open(TRACKER_TSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            writer.writerows(rows_to_append)

        print(f"[+] Appended {len(rows_to_append)} new cards to Master Trackers (CSV and TSV)!")
    else:
        print("[!] Cards already present in Master Trackers.")


def download_images(card_records: List[Dict[str, Any]]):
    """Downloads card pictures from Duelingbook custom pics CDN."""
    headers = {"User-Agent": "Mozilla/5.0"}
    success_count = 0
    fail_count = 0

    for r in card_records:
        target_path = os.path.join(PICS_DIR, f"{r['passcode']}.jpg")
        if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
            success_count += 1
            continue

        url = r["image_link"]
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            with open(target_path, "wb") as f:
                f.write(data)
            success_count += 1
        except Exception as e:
            print(f"[-] Failed to download image for {r['name']} ({url}): {e}")
            fail_count += 1

    print(f"[+] Artwork cache updated: {success_count} available, {fail_count} failed.")


if __name__ == "__main__":
    run_ingestion()
