#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Story Database Seeder & Bootstrap Pipeline
=============================================================================
Initializes the SQLite Story Database (`production/main/web/ygo_story.db`)
with standard schemas, canonical lore sagas, duelist profiles, archetypes/factions,
custom card entries from Set 1: The Land of Kustomazi, and pre-made decks.

Usage:
    python3 development/database/seed_story_data.py
    # Or via master CLI:
    ./manage.sh sync
=============================================================================
"""

import sqlite3
import os
import sys

# Resolve project paths with config.paths fallback
try:
    from config.paths import STORY_DB_PATH, SCHEMA_PATH, BASE_DIR
    DB_PATH = STORY_DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(BASE_DIR, "production", "main", "web", "ygo_story.db")
    SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from development.tools.tracker_sync import parse_raw_tracker, sync_tracker_to_database, DEFAULT_ROOT_CSV


def initialize_database():
    """Initializes SQLite tables and seeds Set 1: The Land of Kustomazi."""
    print(f"[*] Initializing database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
        
    print("[+] Database schema verified.")

    # 1. Seed Canonical Saga: The Genesis of Kustomazi
    cur.execute("""
        INSERT INTO lore_arcs (id, title, synopsis, era_or_season)
        VALUES (1, 'The Genesis of Kustomazi', 
                'Before Planet Kustomazi was created, there was a quiet void. Formless, without shape, teeming with potential, this void was unmoved and aimless, carrying the stories to start worlds. Suddenly, there was a spark, and shining through the light was Kasutamaiza, the Customizer. Accompanied by his devout servants—heralds to the sacred work he was about to do—Kasutamaiza shaped the void into a seed, springing forth Planet Kustomazi and establishing the foundational orders of creation: the Spellspires, the Counsel of Time, the Teeming Fields of Springtime, the Snares, and the Hidden Treasures. As the world shaped, the dimensional rift opened space for a counterworld of Toontastic sights—the LeSpookies.',
                'Genesis Era')
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            synopsis = excluded.synopsis,
            era_or_season = excluded.era_or_season
    """)
    
    # 2. Seed Canonical Factions: The 7 Orders of Creation
    factions_data = [
        (1, 'The Creators of Kustomazi',
         'Kasutamaiza the Customizer and his devout Servants, heralds of genesis who shaped the quiet void into a seed to birth Planet Kustomazi.',
         'Tribute and Fusion summoning centered on high-stat DIVINE Divine-Beast deities and void recursion.'),
        (2, 'The LeSpookies',
         'Born from the dimensional rift left by the shaping of Planet Kustomazi, the LeSpookies inhabit a counterworld of Toontastic sights where lovers of Halloween awaken their inner supernatural spirits under glowing streetlights.',
         'Gemini and Trick-or-Treat Counter strategy transitioning costumed Normal mortals into supernatural Effect, Synchro, and Link evolutions.'),
        (3, 'The Spellspires',
         'The first order founded upon Planet Kustomazi: a team of brilliant alchemists gifted a piece of the primordial void by Kasutamaiza to study, dissect, and create arcane magic with.',
         'Alchemical Fusion arts and spellbook transmutations (Alchemical Bonds), weaving void essence into ascended Fusion forms.'),
        (4, 'The Counsel of Time',
         'A revered assembly of dimensional manipulators entrusted by Kasutamaiza to govern and balance the phases of time, taught ancient ritual arts.',
         'Ritual Summoning, temporal phase control, dimensional manipulation, and turn-pacing disruption.'),
        (5, 'The Teeming Fields of Springtime',
         'A lush collective of diverse plant and insect beings created to populate the new world, cultivating flourishing vegetation, life, and ecological vitality across Planet Kustomazi.',
         'Swarm field presence, Plant/Insect token generation, nature-based resource ramp, and ecological swarming.'),
        (6, 'The Snares',
         'A cunning reptilian fiend race guided directly by Kasutamaiza in the tactical arts of trap setting, perimeter defense, and the unyielding enforcement of celestial rule and order.',
         'Continuous Trap control, counter-punishment, Reptile/Fiend tactical disruption, and lock-down mechanics.'),
        (7, 'The Hidden Treasures',
         'Gem-infused beasts questing deep within the subterranean mines of Planet Kustomazi to uncover the ultimate source of energy for the world: The Hidden Treasure.',
         'Subterranean excavation from Deck/GY, mineral and gem counter accumulation, energy charging, and explosive resource recovery.')
    ]
    for fid, fname, fdesc, fplay in factions_data:
        cur.execute("""
            INSERT INTO factions (id, name, lore_description, playstyle_overview, arc_id)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                lore_description = excluded.lore_description,
                playstyle_overview = excluded.playstyle_overview
        """, (fid, fname, fdesc, fplay))

    # 2b. Seed Canonical Worldbuilding Lore Elements (Up to Planet Creation)
    worldbuilding_data = [
        (1, 'Cosmology', 'The Quiet Void',
         'Before Planet Kustomazi was created, there was a quiet void. Formless, without shape, teeming with potential, this cosmic abyss was unmoved and aimless, carrying the stories to start worlds.',
         'The primordial state of existence preceding all celestial creation and order.', 1),
        (2, 'Cosmology', 'The Sudden Spark',
         'A brilliant, sudden flash of celestial light that cut through the darkness of the quiet void, heralding the emergence of the Customizer.',
         'The catalyst event initiating the Genesis of Planet Kustomazi.', 1),
        (3, 'Cosmology', 'Kasutamaiza, the Customizer',
         'The supreme divine architect who emerged through the primordial spark, capable of shaping raw unformed void essence into living worlds, custom cards, and celestial laws.',
         'The architect and sovereign creator of the entire Kustomazi universe.', 1),
        (4, 'Artifact', 'The Seed of Creation',
         'Kasutamaiza gathered the unshaped void into his hands and concentrated its boundless potential into a luminous celestial seed.',
         'The cosmic catalyst from which Planet Kustomazi sprang forth into physical reality.', 1),
        (5, 'Landmark', 'Planet Kustomazi',
         'The celestial world sprung forth from the Seed of Creation. A realm of oceans, continents, and golden auroras, forged as the stage for all creation orders.',
         'The foundational world setting of the Land of Kustomazi.', 1),
        (6, 'Order', 'The Spellspires',
         'The first order founded upon Planet Kustomazi: a guild of brilliant alchemists gifted a piece of the void by Kasutamaiza to study, dissect, and create arcane magic with.',
         'Pioneers of alchemical transmutations and Fusion summoning arts.', 1),
        (7, 'Order', 'The Counsel of Time',
         'A revered assembly of dimensional manipulators entrusted by Kasutamaiza to govern and balance the phases of time, taught ancient ritual arts.',
         'Guardians of temporal equilibrium and ritual summoning arts.', 1),
        (8, 'Order', 'The Teeming Fields of Springtime',
         'A lush collective of diverse plant and insect beings created to populate the new world, cultivating flourishing vegetation and ecological vitality.',
         'Cultivators of natural life and ecological swarming on Planet Kustomazi.', 1),
        (9, 'Order', 'The Snares',
         'A cunning reptilian fiend race guided directly by Kasutamaiza in the tactical arts of trap setting, perimeter defense, and the unyielding enforcement of celestial rule.',
         'Defenders of celestial order and tactical continuous trap disruption.', 1),
        (10, 'Order', 'The Hidden Treasures',
         'Gem-infused subterranean beasts questing deep within the subterranean mines of Planet Kustomazi to unearth the world\'s ultimate energy source: The Hidden Treasure.',
         'Excavators of subterranean mineral power and resource energy cores.', 1),
        (11, 'Realm', 'The LeSpookie Commons & The Dimensional Rift',
         'As Planet Kustomazi was forged, the celestial shaping tore a dimensional rift into a whimsical counterworld of Toontastic sights—where lovers of Halloween celebrate the boundary where mortal imagination and supernatural spirits intertwine.',
         'A parallel whimsical counterworld born of the creation rift, governed by Gemini awakening.', 1)
    ]
    for wid, wcat, wname, wdesc, wsig, warc in worldbuilding_data:
        cur.execute("""
            INSERT INTO worldbuilding_elements (id, category, name, lore_description, significance, arc_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                category = excluded.category,
                name = excluded.name,
                lore_description = excluded.lore_description,
                significance = excluded.significance,
                arc_id = excluded.arc_id
        """, (wid, wcat, wname, wdesc, wsig, warc))

    # 3. Seed Canonical Characters
    characters_data = [
        (1, 'Kasutamaiza, the Creator of Kustomazi', 'The Supreme Architect',
         'The divine sovereign who emerged through the primordial spark, shaped the quiet void into a seed, and brought forth Planet Kustomazi.',
         1, 1, 'https://images.duelingbook.com/custom-pics/800000/831545.jpg?version=3'),
        (2, 'Magnolia, Ghost of LeSpookie Street', 'The Lantern Maiden',
         'A wandering spirit of LeSpookie Street who guides the costumed children and dances when the shadows awaken under the streetlights.',
         2, 1, 'https://images.duelingbook.com/custom-pics/800000/831546.jpg?version=3'),
        (4, 'ProfessorSeanEX', 'The Creator',
         'The Supreme Architect behind Set 1: The Land of Kustomazi and master of creation decks.',
         1, 1, 'https://images.duelingbook.com/custom-pics/800000/831545.jpg?version=3')
    ]
    cur.execute("DELETE FROM characters WHERE id IN (1, 2, 4) OR name IN ('Kasutamaiza, the Creator of Kustomazi', 'Magnolia, Ghost of LeSpookie Street', 'ProfessorSeanEX')")
    for cid, cname, calias, cbio, cfac, carc, cavatar in characters_data:
        cur.execute("""
            INSERT INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cid, cname, calias, cbio, cfac, carc, cavatar))

    # 4. Seed Canonical Deck: Kasutamaiza - Creation Control
    ydk_content = """#created by ProfessorSeanEX
#main
50000101
50000101
50000101
50000102
50000102
50000102
50000103
50000103
50000103
50000104
50000104
50000104
50000105
50000105
50000108
50000108
50000108
50000109
50000109
50000109
50000110
50000110
50000110
50000111
50000111
50000111
50000112
50000112
50000112
50000113
50000113
50000113
50000114
50000114
#extra
50000106
50000106
50000106
50000107
50000107
50000107
!side
"""
    cur.execute("""
        INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url, ydk_content)
        VALUES (1, 'Kasutamaiza - Creation Control', 1, 'ProfessorSeanEX',
                'High-level Divine-Beast control strategy utilizing Void recursion, Seed of Creation, and contact Fusion into The Great Kasutamaiza.',
                'https://www.duelingbook.com', ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            character_id = excluded.character_id,
            creator_name = excluded.creator_name,
            description = excluded.description,
            ydk_content = excluded.ydk_content
    """, (ydk_content,))

    # Seed deck_cards
    cur.execute("DELETE FROM deck_cards WHERE deck_id = 1")
    deck_cards_data = [
        (1, 50000101, 3, 'MAIN'),
        (1, 50000102, 3, 'MAIN'),
        (1, 50000103, 3, 'MAIN'),
        (1, 50000104, 3, 'MAIN'),
        (1, 50000105, 2, 'MAIN'),
        (1, 50000108, 3, 'MAIN'),
        (1, 50000109, 3, 'MAIN'),
        (1, 50000110, 3, 'MAIN'),
        (1, 50000111, 3, 'MAIN'),
        (1, 50000112, 3, 'MAIN'),
        (1, 50000113, 3, 'MAIN'),
        (1, 50000114, 2, 'MAIN'),
        (1, 50000106, 3, 'EXTRA'),
        (1, 50000107, 3, 'EXTRA'),
    ]
    for row in deck_cards_data:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (?, ?, ?, ?)", row)

    # 4b. Seed Canonical Deck: LeSpookie Singles
    lespookie_main = list(range(50000115, 50000151))
    lespookie_extra = list(range(50000151, 50000165))
    lespookie_ydk = "#created by ProfessorSeanEX\n#main\n" + "\n".join(str(p) for p in lespookie_main) + "\n#extra\n" + "\n".join(str(p) for p in lespookie_extra) + "\n!side\n"

    cur.execute("""
        INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url, ydk_content)
        VALUES (2, 'LeSpookie Singles', 2, 'ProfessorSeanEX',
                'A 50-card Gemini and trick-or-treat counter strategy featuring costumed children who enter as Normal Monsters and awaken with Gemini summon, dancing shadows, and spooky extra deck evolutions.',
                'https://www.duelingbook.com/deck?id=8114120', ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            character_id = excluded.character_id,
            creator_name = excluded.creator_name,
            description = excluded.description,
            ydk_content = excluded.ydk_content
    """, (lespookie_ydk,))

    cur.execute("DELETE FROM deck_cards WHERE deck_id = 2")
    for p in lespookie_main:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (2, ?, 1, 'MAIN')", (p,))
    for p in lespookie_extra:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (2, ?, 1, 'EXTRA')", (p,))

    # 4c. Seed Canonical Deck: Base of Story (Kas.)
    base_story_main = [50000105, 50000101, 50000104, 50000102, 50000110, 50000111, 50000108, 50000103, 50000112, 50000109]
    base_story_extra = [50000106, 50000107]
    base_story_side = [50000113, 50000114]
    base_story_ydk = "#created by ProfessorSeanEX\n#main\n" + "\n".join(str(p) for p in base_story_main) + "\n#extra\n" + "\n".join(str(p) for p in base_story_extra) + "\n!side\n" + "\n".join(str(p) for p in base_story_side) + "\n"

    cur.execute("""
        INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url, ydk_content)
        VALUES (3, 'Base of Story (Kas.)', 1, 'ProfessorSeanEX',
                'The foundational 14-card Set 1 story deck from Duelingbook (deck 20861703), featuring the creation forces of Kasutamaiza, the Spellspires'' Fusion arts, and the rift unsealing Mohousha.',
                'https://www.duelingbook.com/deck?id=20861703', ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            character_id = excluded.character_id,
            creator_name = excluded.creator_name,
            description = excluded.description,
            duelingbook_deck_url = excluded.duelingbook_deck_url,
            ydk_content = excluded.ydk_content
    """, (base_story_ydk,))

    cur.execute("DELETE FROM deck_cards WHERE deck_id = 3")
    for p in base_story_main:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (3, ?, 1, 'MAIN')", (p,))
    for p in base_story_extra:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (3, ?, 1, 'EXTRA')", (p,))
    for p in base_story_side:
        cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (3, ?, 1, 'SIDE')", (p,))

    # 4d. Seed Progressive Story Decks (4-11) from .ydk files
    progressive_decks = [
        (4, 'Kasutamaiza: Genesis & The Mortal Realm', 1, 'ProfessorSeanEX',
         'Chapter 1 (ELO 1100): The dawn of Kustomazi. Primordial creator forces alongside mortal realm observers before the rift opened.',
         'creation_and_mortal_realm.ydk'),
        (5, 'The Forbidden Sect (Rift Turbo)', 1, 'ProfessorSeanEX',
         'Chapter 2 (ELO 1450): Forbidden experiments unearth the Seed of Creation. A rift is torn via Contact from Beyond, unsealing Mohousha and invoking The Great Kasutamaiza.',
         'forbidden_sect_rift.ydk'),
        (6, 'Night of the LeSpookie (The Haunting)', 2, 'Magnolia',
         'Chapter 3 (ELO 1600): The ancient ghost legend manifested into reality by A Wicked Shadow. Costumed trick-or-treaters awaken their Gemini powers under LeSpookiest Night.',
         'night_of_the_lespookie.ydk'),
        (7, 'The Lantern Ascension (Apex Boss)', 2, 'Magnolia',
         'Apex Boss (ELO 1800+): The dimensional breach peaks. High-tempo Link and Synchro climb with Magnolia Lantern Ascended and A Wicked Shadow.',
         'lantern_ascension.ydk'),
        (8, 'Quiet Void - Formless Potential', 1, 'ProfessorSeanEX',
         'Chapter 1 Stage 1 AI Deck: The formless quiet void before creation. Defensive stall and void spirit echoes.',
         'quiet_void_potential.ydk'),
        (9, 'The Spark of Genesis', 1, 'ProfessorSeanEX',
         'Chapter 1 Stage 2 AI Deck: The sudden cosmic spark cutting through the void. Nascent flames and burn disruption.',
         'spark_of_genesis.ydk'),
        (10, 'Servants of Genesis', 1, 'ProfessorSeanEX',
         'Chapter 1 Stage 3 AI Deck: Devout servants preparing the sacred altar of creation for the Customizer.',
         'servants_of_genesis.ydk'),
        (11, 'Kasutamaiza - Dawn of Planet Kustomazi', 1, 'Kasutamaiza',
         'Chapter 1 Stage 4 Scripted Boss Deck: Kasutamaiza weaving the celestial seed to spring forth Planet Kustomazi into existence.',
         'kasutamaiza_dawn_planet.ydk'),
    ]

    for d_id, d_name, d_char, d_creator, d_desc, d_filename in progressive_decks:
        ydk_path = os.path.join(BASE_DIR, "production", "shared", "decks", d_filename)
        if os.path.exists(ydk_path):
            with open(ydk_path, "r", encoding="utf-8") as yf:
                ydk_text = yf.read()

            cur.execute("""
                INSERT INTO decks (id, name, character_id, creator_name, description, ydk_content)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    character_id = excluded.character_id,
                    creator_name = excluded.creator_name,
                    description = excluded.description,
                    ydk_content = excluded.ydk_content
            """, (d_id, d_name, d_char, d_creator, d_desc, ydk_text))

            cur.execute("DELETE FROM deck_cards WHERE deck_id = ?", (d_id,))
            sec = "MAIN"
            card_counts = {}
            for line in ydk_text.splitlines():
                line = line.strip()
                if line.startswith("#main"):
                    sec = "MAIN"
                elif line.startswith("#extra"):
                    sec = "EXTRA"
                elif line.startswith("!side"):
                    sec = "SIDE"
                elif line.isdigit():
                    cid = int(line)
                    key = (cid, sec)
                    card_counts[key] = card_counts.get(key, 0) + 1

            for (cid, sec_name), qty in card_counts.items():
                cur.execute("""
                    INSERT INTO deck_cards (deck_id, card_id, quantity, section)
                    VALUES (?, ?, ?, ?)
                """, (d_id, cid, qty, sec_name))


    # 5. Seed Duel Log
    cur.execute("""
        INSERT INTO duel_logs (id, arc_id, chapter_or_episode, duelist_1_id, duelist_2_id, winner_id, duel_summary)
        VALUES (1, 1, 'Chapter 1: The Shaping of the Void', 1, 1, 1,
                'ProfessorSeanEX Normal Summons Kasutamaiza, the Creator of Kustomazi by Tributing 3 Divine-Beast acolytes, establishing the eternal reign of Kustomazi.')
        ON CONFLICT(id) DO UPDATE SET
            duel_summary = excluded.duel_summary
    """)

    # 6. Seed Story Chapters & Stages directly from scenario JSON files (Single Source of Truth)
    import glob
    import json
    story_dir = os.path.join(BASE_DIR, "production", "main", "discord_bot", "data", "story")
    if os.path.exists(story_dir):
        json_files = sorted(glob.glob(os.path.join(story_dir, "*.json")))
        for json_path in json_files:
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
        print(f"[+] Loaded story chapters and stages from {len(json_files)} scenario JSON files in {story_dir}")

    conn.commit()


    # 7. Synchronize all 14 custom cards from Master Tracker
    print("[*] Synchronizing Set 1 cards from Master Tracker...")
    records = parse_raw_tracker(DEFAULT_ROOT_CSV)
    synced = sync_tracker_to_database(records, db_path=DB_PATH)
    print(f"[+] Successfully seeded database with {synced} custom cards from The Land of Kustomazi!")

    # 8. Seed initial card_usage_stats for all synced custom cards
    cur = conn.cursor()
    cur.execute("SELECT id FROM custom_cards")
    for (cid,) in cur.fetchall():
        cur.execute("""
            INSERT OR IGNORE INTO card_usage_stats (card_id, times_decked, times_drawn, times_played, wins, losses)
            VALUES (?, 0, 0, 0, 0, 0)
        """, (cid,))
    conn.commit()
    conn.close()



if __name__ == "__main__":
    initialize_database()
