#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator - Authoritative Kasutamaiza Story Alignment Pipeline
=============================================================================
Synchronizes the 14 foundational Set 1 cards with Duelingbook deck 20861703
("Base of Story (Kas.)"), encoding:
1. Normal Monster status for The Void of Creation (TLOK-002)
2. Field Spell classifications for Planet Kustomazi & Temple
3. Quick-Play classification for The Seed of Creation
4. Counter Trap classification for Divine Justice
5. Fusion classifications for Mohousha & The Great Kasutamaiza
6. Story lore integration:
   - The Fusion art stems from the Spellspires.
   - "A Wicked Shadow" was a manifestation of Mohousha before he was unsealed
     by Contact from Beyond.
7. Creation of pre-built deck: "Base of Story (Kas.)" (YDK & database)
8. Master Tracker & CDB synchronization
=============================================================================
"""

import os
import sys
import json
import sqlite3
import csv
import re
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import STORY_DB_PATH, CDB_OUTPUT_PATH, DECKS_DIR, TRACKERS_DIR
from development.tools.cdb_builder import build_cdb, parse_card_type

JSON_DECK_PATH = "/home/professorseanex/.gemini/antigravity-ide/brain/3ee778d3-38e4-483c-aa6e-cd58a9c1f8b3/scratch/deck_20861703_full.json"
ROOT_TRACKER_CSV = os.path.join(BASE_DIR, "Duelingbook Master Tracker - Set 1 - The Land of Kustomazi.csv")
TRACKER_CSV = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.csv")
TRACKER_TSV = os.path.join(TRACKERS_DIR, "Duelingbook_Master_Tracker_Set_1_The_Land_of_Kustomazi.tsv")


NAME_TO_PASSCODE = {
    "Kasutamaiza, the Creator of Kustomazi": 50000101,
    "The Void of Creation": 50000102,
    "The Seed of Creation": 50000103,
    "Servants of the Great Kasutamaiza": 50000104,
    "Formless the True Void of Creation": 50000105,
    "Mohousha the Accursed of the Great Kasutamaiza": 50000106,
    "The Great Kasutamaiza": 50000107,
    "The Call of the Great Kasutamaiza": 50000108,
    "Divine Justice of the Great Kasutamaiza": 50000109,
    "Planet Kustomazi": 50000110,
    "Temple of the Great Kasutamaiza": 50000111,
    "The Spark of Creation": 50000112,
    "Alchemical Bonds": 50000113,
    "Contact from Beyond": 50000114,
}

UPDATED_LORE = {
    50000101: "The primordial supreme architect of Kustomazi who forged the universe from the cosmic void, establishing the sacred temple grounds and celestial laws.",
    50000102: "The silent, unshaped void of potential existing before the first word of creation. A pure primordial canvas from which all cosmic manifestations originate.",
    50000103: "The concentrated initial spark of cosmic matter that awakened the silent void, bridging nothingness into physical reality.",
    50000104: "Devoted cosmic acolytes who tend to the sacred monuments and altars of the Creator, channeling divine sacrifices.",
    50000105: "The shifting, volatile current of unshaped antimatter dwelling at the deep core of the primordial void.",
    50000106: "The dark alchemical reflection of the supreme architect, forged through the esoteric Fusion art of the Spellspires. When banished into the void by Divine Justice, his lingering malice leaked into the mortal realm as 'A Wicked Shadow' before he was unsealed once again by Contact from Beyond.",
    50000107: "The pinnacle cosmic synthesis of creation, summoned through the supreme Fusion art taught by the celestial Spellspires.",
    50000108: "The resonant celestial invocation summoning disciples to the grand altars of the Creator.",
    50000109: "The absolute decree of cosmic law that banished Mohousha the Accursed into the abyss when he sought to usurp creation.",
    50000110: "The sovereign celestial realm where the laws of Kustomazi govern reality and extra normal summons manifest.",
    50000111: "The grand golden sanctuary where acolytes offer tribute to maintain harmony between sacrifice and creation.",
    50000112: "The luminous spark retrieving banished void essences to unleash devastating concentrated elemental beams.",
    50000113: "The sacred transmutation formula channeled through the Spellspires, enabling duelists to weave separate essences into majestic Fusion entities.",
    50000114: "The forbidden rift spell that pierced the banishment void, unsealing Mohousha the Accursed after his fragmented shadow had already manifested across the world.",
    50000115: "A wicked shadow cast along LeSpookie Street—the lingering manifestation of Mohousha's malice while banished by Divine Justice, dancing in the dark before his unsealing by Contact from Beyond."
}


def run_update():
    with open(JSON_DECK_PATH, "r", encoding="utf-8") as f:
        deck_data = json.load(f)

    all_cards = deck_data["main"] + deck_data["extra"] + deck_data["side"]
    print(f"[*] Processing {len(all_cards)} authoritative cards from Duelingbook deck {deck_data.get('id')}...")

    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()

    updated_map = {}

    for c in all_cards:
        name = c["name"].strip()
        passcode = NAME_TO_PASSCODE.get(name)
        if not passcode:
            print(f"[!] Warning: Name '{name}' not found in known Set 1 passcodes.")
            continue

        raw_cat = c.get("card_type", "Monster")
        mcol = (c.get("monster_color") or "").strip()
        raw_type = (c.get("type") or "").strip()
        attr = c.get("attribute") if raw_cat == "Monster" and c.get("attribute") else None

        if raw_cat == "Monster":
            if "Fusion" in mcol:
                subtype = "Fusion / Effect"
            elif "Normal" in mcol:
                subtype = "Normal"
            else:
                subtype = "Effect"
            race = raw_type or "Divine-Beast"
            atk_val = -2 if str(c.get("atk")).strip() == "?" else int(c.get("atk", 0))
            def_val = -2 if str(c.get("def")).strip() == "?" else int(c.get("def", 0))
            level_val = int(c.get("level", 1))
        elif raw_cat == "Spell":
            subtype = raw_type if raw_type in ["Field", "Quick-Play", "Continuous", "Equip", "Normal"] else "Normal"
            race = None
            atk_val = None
            def_val = None
            level_val = None
        elif raw_cat == "Trap":
            subtype = raw_type if raw_type in ["Counter", "Continuous", "Normal"] else "Normal"
            race = None
            atk_val = None
            def_val = None
            level_val = None

        effect = c.get("effect", "").strip()
        lore = UPDATED_LORE.get(passcode, "")

        cur.execute("""
            UPDATE custom_cards
            SET card_type = ?,
                card_subtype = ?,
                attribute = ?,
                monster_type = ?,
                level_or_rank_or_link = ?,
                atk = ?,
                def = ?,
                effect_text = ?,
                lore_text = ?
            WHERE id = ?
        """, (raw_cat, subtype, attr, race, level_val, atk_val, def_val, effect, lore, passcode))

        updated_map[passcode] = {
            "name": name,
            "category": raw_cat,
            "subtype": subtype,
            "race": race or "N/A",
            "attribute": attr or "N/A",
            "level": str(level_val) if level_val is not None else "N/A",
            "atk": str(atk_val) if atk_val is not None else "N/A",
            "def": str(def_val) if def_val is not None else "N/A",
            "effect_text": effect,
            "lore": lore,
            "cdb_bitmask": hex(parse_card_type(raw_cat, subtype))
        }
        print(f"[+] Updated TLOK {passcode} ({name}) -> {raw_cat}/{subtype} [{updated_map[passcode]['cdb_bitmask']}]")

    # Also update A Wicked Shadow lore in custom_cards
    cur.execute("UPDATE custom_cards SET lore_text = ? WHERE id = 50000115", (UPDATED_LORE[50000115],))
    print("[+] Updated TLOK 50000115 (A Wicked Shadow) lore with Mohousha manifestation context.")

    # Rebuild FTS5 index
    cur.execute("INSERT INTO cards_fts(cards_fts) VALUES('rebuild')")

    # Register pre-built deck: "Base of Story (Kas.)"
    main_p = [NAME_TO_PASSCODE[c["name"]] for c in deck_data["main"]]
    extra_p = [NAME_TO_PASSCODE[c["name"]] for c in deck_data["extra"]]
    side_p = [NAME_TO_PASSCODE[c["name"]] for c in deck_data["side"]]

    ydk_lines = ["#created by ProfessorSeanEX", "#main"]
    for p in main_p:
        ydk_lines.append(str(p))
    ydk_lines.append("#extra")
    for p in extra_p:
        ydk_lines.append(str(p))
    ydk_lines.append("!side")
    for p in side_p:
        ydk_lines.append(str(p))
    ydk_lines.append("")
    ydk_content = "\n".join(ydk_lines)

    ydk_file_path = os.path.join(DECKS_DIR, "Base of Story (Kas.).ydk")
    with open(ydk_file_path, "w", encoding="utf-8") as f:
        f.write(ydk_content)
    print(f"[+] Saved YDK deck to {ydk_file_path}")

    cur.execute("""
        INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url, ydk_content)
        VALUES (3, 'Base of Story (Kas.)', 1, 'ProfessorSeanEX',
                'The foundational 14-card Set 1 story deck from Duelingbook (deck 20861703), featuring the creation forces of Kasutamaiza, the Spellspires'' Fusion arts, and the rift unsealing Mohousha.',
                'https://www.duelingbook.com/deck?id=20861703', ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            description = excluded.description,
            duelingbook_deck_url = excluded.duelingbook_deck_url,
            ydk_content = excluded.ydk_content
    """, (ydk_content,))

    cur.execute("DELETE FROM deck_cards WHERE deck_id = 3")
    for p in main_p:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (3, ?, 1, 'MAIN')", (p,))
    for p in extra_p:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (3, ?, 1, 'EXTRA')", (p,))
    for p in side_p:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (3, ?, 1, 'SIDE')", (p,))

    conn.commit()
    conn.close()
    print("[+] Successfully committed database updates.")

    # Update Master Trackers (CSV and TSV)
    update_trackers(updated_map)

    # Recompile custom_cards.cdb
    print("[*] Recompiling custom_cards.cdb...")
    compiled = build_cdb()
    print(f"[+] Successfully compiled {compiled} cards into {CDB_OUTPUT_PATH}!")


def update_trackers(updated_map: Dict[int, Dict[str, Any]]):
    """Updates the rows of passcodes in CSV and TSV trackers."""
    for file_path, delimiter in [(ROOT_TRACKER_CSV, ","), (TRACKER_CSV, ","), (TRACKER_TSV, "\t")]:
        with open(file_path, "r", encoding="utf-8") as f:
            if delimiter == ",":
                rows = list(csv.reader(f))
            else:
                rows = list(csv.reader(f, delimiter="\t"))

        header = rows[0]
        passcode_idx = header.index("Passcode (ID)")
        cat_idx = header.index("Card Category")
        sub_idx = header.index("Card Subtype")
        race_idx = header.index("Monster Race")
        attr_idx = header.index("Attribute")
        lvl_idx = header.index("Level/Rank/Link")
        atk_idx = header.index("ATK")
        def_idx = header.index("DEF")
        effect_idx = header.index("Effect Text")
        lore_idx = header.index("Story/Lore Context")
        bitmask_idx = header.index("CDB Bitmask Type")

        for row in rows[1:]:
            if not row:
                continue
            raw_p = row[passcode_idx].strip()
            if not raw_p.isdigit():
                continue
            passcode = int(raw_p)

            if passcode in updated_map:
                u = updated_map[passcode]
                row[cat_idx] = u["category"]
                row[sub_idx] = u["subtype"]
                row[race_idx] = u["race"]
                row[attr_idx] = u["attribute"]
                row[lvl_idx] = u["level"]
                row[atk_idx] = u["atk"]
                row[def_idx] = u["def"]
                row[effect_idx] = re.sub(r'[\r\n]+', ' ', u["effect_text"]).strip()
                row[lore_idx] = u["lore"]
                row[bitmask_idx] = u["cdb_bitmask"]
            elif passcode == 50000115:
                row[lore_idx] = UPDATED_LORE[50000115]

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            if delimiter == ",":
                writer = csv.writer(f)
            else:
                writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            writer.writerows(rows)

        print(f"[+] Updated tracker file: {file_path}")


if __name__ == "__main__":
    run_update()
