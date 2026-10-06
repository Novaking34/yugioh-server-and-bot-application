#!/usr/bin/env python3
"""
=============================================================================
Update Rarities & Complete Categorization for All 64 Cards in Set 1
=============================================================================
Assigns authentic official Yu-Gi-Oh! rarities (Secret Rare, Ultra Rare,
Super Rare, Rare, Common) and enforces exact categorization across:
1. SQLite content database (`content.db`)
2. Master Tracker files (CSV and TSV)
3. Simulator binary CDB (`custom_cards.cdb`)
=============================================================================
"""

import os
import sys
import sqlite3
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, "development", "tools"))

from constants import (
    RARITY_SECRET_RARE, RARITY_ULTRA_RARE, RARITY_SUPER_RARE,
    RARITY_RARE, RARITY_COMMON
)
from cdb_builder import build_cdb

from config.paths import STORY_DB_PATH, DEFAULT_TRACKER_CSV, DEFAULT_TRACKER_TSV, CDB_OUTPUT_PATH
DEV_CSV_PATH = DEFAULT_TRACKER_CSV
ROOT_CSV_PATH = DEV_CSV_PATH
DEV_TSV_PATH = DEFAULT_TRACKER_TSV

# Official Yu-Gi-Oh! Rarity Assignment Mapping for all 64 Cards:
# Follows booster pack rarity philosophy:
# - Secret Rare: Highest tier boss deities & climax extra deck finishers
# - Ultra Rare: Archetype keystones, dark counterparts, top searchers, omni-counter traps
# - Super Rare: Field spells, extenders, extra deck utility threats
# - Rare: Consistency engines, specialized tuners/geminis, core fusion/spell tech
# - Common: Primordial normal monsters, battle traps, situational spells
OFFICIAL_CARD_RARITIES = {
    # -------------------------------------------------------------
    # 1. Kasutamaiza Archetype (TLOK-001 to TLOK-014)
    # -------------------------------------------------------------
    50000101: RARITY_SECRET_RARE, # Kasutamaiza, the Creator of Kustomazi (Flagship Level 12 Creator God)
    50000102: RARITY_COMMON,      # The Void of Creation (Normal Divine-Beast primordial origin)
    50000103: RARITY_SUPER_RARE,  # The Seed of Creation (Core Quick-Play searcher & GY recursion)
    50000104: RARITY_RARE,        # Servants of the Great Kasutamaiza (3-Tribute engine swarm acolyte)
    50000105: RARITY_RARE,        # Formless the True Void of Creation (Contact summon wipe)
    50000106: RARITY_ULTRA_RARE,  # Mohousha the Accursed of the Great Kasutamaiza (Dark Alchemical Fusion Boss)
    50000107: RARITY_SECRET_RARE, # The Great Kasutamaiza (Pinnacle Celestial Fusion Boss)
    50000108: RARITY_SUPER_RARE,  # The Call of the Great Kasutamaiza (Archetype search & recycle ROTA)
    50000109: RARITY_ULTRA_RARE,  # Divine Justice of the Great Kasutamaiza (Cosmic Counter Trap omni-negate)
    50000110: RARITY_SUPER_RARE,  # Planet Kustomazi (Creation Homeworld Field Spell)
    50000111: RARITY_ULTRA_RARE,  # Temple of the Great Kasutamaiza (Sacred Golden Sanctuary Field Spell)
    50000112: RARITY_RARE,        # The Spark of Creation (Graveyard void-banish payoff)
    50000113: RARITY_RARE,        # Alchemical Bonds (Spellspire Fusion Spell)
    50000114: RARITY_RARE,        # Contact from Beyond (Forbidden unsealing Miracle Fusion)

    # -------------------------------------------------------------
    # 2. LeSpookie Chronicle & Extra Deck (TLOK-015 to TLOK-064)
    # -------------------------------------------------------------
    50000115: RARITY_SECRET_RARE, # A Wicked Shadow (Wandering manifestation of Mohousha, master Tuner bridge)
    50000116: RARITY_RARE,        # Hexla, Witch of the LeSpookie Street (Gemini tutor)
    50000117: RARITY_RARE,        # LeSpookie Count Spookula, Trick-or-Treat Vampire (Gemini revival)
    50000118: RARITY_RARE,        # LeSpookie Disguise Dropper (Hand-trap counter disruption)
    50000119: RARITY_RARE,        # LeSpookie Flareling, Shadow’s Reignite (Tuner extender)
    50000120: RARITY_COMMON,      # LeSpookie Howlsuit Harold, Werewolf Pretender (Gemini beatstick)
    50000121: RARITY_RARE,        # LeSpookie Jack, Ember of the Hollow Smile (Gemini Wicked Shadow searcher)
    50000122: RARITY_RARE,        # LeSpookie Lilith, Mask of the Midnight Veil (Gemini level tutor)
    50000123: RARITY_RARE,        # LeSpookie Mummy Kid, Watcher of Wrappings (Gemini quick negation)
    50000124: RARITY_RARE,        # LeSpookie Patchwork Frank, the Costume Golem (Gemini construct)
    50000125: RARITY_RARE,        # LeSpookie Skelly, Hollow-Bound Twirler (Gemini foolish burial)
    50000126: RARITY_COMMON,      # LeSpookie Specter, The Echo Beneath the Mask (Gemini normal summoner)
    50000127: RARITY_RARE,        # LeSpookie Whisperling (Level modulate Tuner)
    50000128: RARITY_COMMON,      # A Shadow Once Named (Normal Zombie)
    50000129: RARITY_RARE,        # LeSpookie Commons, the Cursed Town of Whimsy (Normal Fiend)
    50000130: RARITY_ULTRA_RARE,  # Magnolia, the Ghost of LeSpookie Street (Flagship Level 8 Normal Spirit)
    50000131: RARITY_COMMON,      # The One Who Watched (Normal Spellcaster)
    50000132: RARITY_RARE,        # Costume Chest from the Attic (Continuous Spell)
    50000133: RARITY_RARE,        # Flicker Between Forms (Quick-Play Spell)
    50000134: RARITY_SUPER_RARE,  # LeSpookie Haunted Mansion (Haunted Field Spell)
    50000135: RARITY_COMMON,      # LeSpookie Lantern Trials (Quick-Play Spell)
    50000136: RARITY_COMMON,      # LeSpookie Midnight Masking (Normal Spell)
    50000137: RARITY_RARE,        # LeSpookie Spirit Trail (Continuous Spell)
    50000138: RARITY_SUPER_RARE,  # LeSpookie Street, Cursed Lane (Core City Field Spell)
    50000139: RARITY_COMMON,      # LeSpookie Sugary Sweets (Quick-Play Spell)
    50000140: RARITY_ULTRA_RARE,  # LeSpookiest Night (Pot of Greed archetypal power spell)
    50000141: RARITY_RARE,        # The Mask of LeSpookie (Equip Spell)
    50000142: RARITY_RARE,        # Trick or Treat: Spirit Pact (Quick-Play Spell)
    50000143: RARITY_COMMON,      # Candlesnuff (Normal Trap)
    50000144: RARITY_COMMON,      # LeSpookie Whisper in the Wrappings (Normal Trap)
    50000145: RARITY_RARE,        # LeSpookiest Scare (Continuous Trap)
    50000146: RARITY_COMMON,      # LeSpookiest Trick! (Normal Trap)
    50000147: RARITY_RARE,        # Mask of the Forgotten Trick (Continuous Trap)
    50000148: RARITY_ULTRA_RARE,  # The End of LeSpookiest Night (Counter Trap climax)
    50000149: RARITY_RARE,        # The Forgotten Invitation (Trap Monster Tuner)
    50000150: RARITY_RARE,        # Trick-or-Treat Return (Counter Trap)
    50000151: RARITY_SUPER_RARE,  # Anubis, Entombed Guardian of LeSpookie (Level 7 Synchro)
    50000152: RARITY_ULTRA_RARE,  # Crimson Cloak of LeSpookie Night (Level 11 Synchro Boss)
    50000153: RARITY_SUPER_RARE,  # Hexla Awakened, Witch of LeSpookie Circles (Level 7 Synchro)
    50000154: RARITY_SUPER_RARE,  # Jack-O-Lantern, Spirit Spark of LeSpookie (Level 5 Synchro)
    50000155: RARITY_SUPER_RARE,  # LeSpookie Lilith Veiled, Whisper of Forgotten Names (Level 7 Synchro)
    50000156: RARITY_SUPER_RARE,  # LeSpookie Specter, Echo Beneath the Lantern (Level 5 Synchro)
    50000157: RARITY_ULTRA_RARE,  # LeSpookiestein, Dread Construct of the Night (Level 9 Synchro)
    50000158: RARITY_SECRET_RARE, # Magnolia, Lantern Eternal of LeSpookie (Level 12 Synchro Climax)
    50000159: RARITY_SUPER_RARE,  # Moonlit Howler, Beast of LeSpookie (Level 9 Synchro)
    50000160: RARITY_SUPER_RARE,  # DaSpookie, Mayor of LeSpookie Street (Link-2)
    50000161: RARITY_SUPER_RARE,  # LeSpookie Costume Vendor (Link-1)
    50000162: RARITY_SUPER_RARE,  # LeSpookie Skeleton, Marrowlink Mischief (Link-2)
    50000163: RARITY_RARE,        # LeSpookie Whisper in the Fog (Link-1)
    50000164: RARITY_SECRET_RARE, # Magnolia, Lantern Ascended (Link-3 Pinnacle Boss)
}


def update_database(conn: sqlite3.Connection):
    cur = conn.cursor()
    print("[*] Updating custom_cards rarities in SQLite database...")
    for cid, rarity in OFFICIAL_CARD_RARITIES.items():
        cur.execute("UPDATE custom_cards SET rarity = ? WHERE id = ?", (rarity, cid))
    
    # Rebuild FTS5
    print("[*] Rebuilding cards_fts index...")
    cur.execute("INSERT INTO cards_fts(cards_fts) VALUES('rebuild')")
    conn.commit()
    print(f"    -> Updated {len(OFFICIAL_CARD_RARITIES)} cards in content.db")


def update_tracker_file(file_path: str, is_tsv: bool = False):
    print(f"[*] Updating tracker file: {os.path.basename(file_path)}...")
    delimiter = '\t' if is_tsv else ','
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated_count = 0
    for row in rows:
        cid_str = row.get("Passcode (ID)")
        if cid_str and cid_str.isdigit():
            cid = int(cid_str)
            if cid in OFFICIAL_CARD_RARITIES:
                old_rarity = row.get("Rarity")
                new_rarity = OFFICIAL_CARD_RARITIES[cid]
                if old_rarity != new_rarity:
                    row["Rarity"] = new_rarity
                    updated_count += 1

    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)

    print(f"    -> Modified {updated_count} rows in {os.path.basename(file_path)}")


def main():
    conn = sqlite3.connect(STORY_DB_PATH)
    try:
        update_database(conn)
    finally:
        conn.close()

    update_tracker_file(DEV_CSV_PATH, is_tsv=False)
    update_tracker_file(DEV_TSV_PATH, is_tsv=True)

    print("[*] Recompiling custom_cards.cdb...")
    cards_compiled = build_cdb(
        story_db_path=STORY_DB_PATH,
        cdb_output_path=CDB_OUTPUT_PATH
    )
    print(f"    -> Compiled {cards_compiled} cards into {os.path.basename(CDB_OUTPUT_PATH)}")
    print("[+] Rarity update and re-categorization complete!")


if __name__ == "__main__":
    main()
