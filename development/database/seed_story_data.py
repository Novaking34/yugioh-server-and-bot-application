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
                'Before the cosmos took form, the primordial void whispered into the infinite darkness. Kasutamaiza awakened to shape existence, forging celestial temples, divine decrees, and the eternal laws of creation.',
                'Genesis Era')
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            synopsis = excluded.synopsis,
            era_or_season = excluded.era_or_season
    """)
    
    # 2. Seed Canonical Faction: The Creators of Kustomazi
    cur.execute("""
        INSERT INTO factions (id, name, lore_description, playstyle_overview, arc_id)
        VALUES (1, 'The Creators of Kustomazi', 
                'The supreme primordial pantheon and cosmic architects of the Land of Kustomazi.',
                'Tribute and Fusion summoning centered on high-stat DIVINE Divine-Beast deities and void recursion.', 1)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            lore_description = excluded.lore_description,
            playstyle_overview = excluded.playstyle_overview
    """)
    
    # 3. Seed Canonical Character: ProfessorSeanEX
    cur.execute("""
        INSERT INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
        VALUES (1, 'ProfessorSeanEX', 'The Supreme Architect', 
                'Master creator and overseer of the Kustomazi universe and custom card chronicle.',
                1, 1, 'https://images.duelingbook.com/custom-pics/2200000/2282769.jpg')
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            alias = excluded.alias,
            bio = excluded.bio,
            avatar_url = excluded.avatar_url
    """)

    # 3b. Seed Canonical Character: Magnolia, Ghost of LeSpookie Street
    cur.execute("""
        INSERT INTO factions (id, name, lore_description, playstyle_overview, arc_id)
        VALUES (2, 'The LeSpookiest Night',
                'In a quiet town on Halloween night, where costumed youths trick-or-treat under bright streetlights and the shadows dance, ordinary mortals awaken as supernatural entities.',
                'Gemini and Trick-or-Treat Counter strategy that transitions Normal Monsters into supernatural Effect, Synchro, and Link evolutions.', 1)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            lore_description = excluded.lore_description,
            playstyle_overview = excluded.playstyle_overview
    """)
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

    # 4d. Seed Progressive Story Decks (4-7) from .ydk files
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

    # 6. Seed Story Chapters 1 & 2
    cur.execute("""
        INSERT INTO story_chapters (id, chapter_number, title, arc_id, synopsis)
        VALUES (1, 1, 'The Genesis of Kustomazi', 1, 
                'Kasutamaiza awakens to forge the celestial laws of creation. Duelists must navigate the primordial void, witness the rites of the temple, and face the Supreme Architect in the ultimate trial.')
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            synopsis = excluded.synopsis
    """)
    cur.execute("""
        INSERT INTO story_chapters (id, chapter_number, title, arc_id, synopsis)
        VALUES (2, 2, 'The LeSpookiest Night', 1,
                'On a quiet Halloween night when Magnolia dances and shadows are a fright, costumed mortals awaken their inner spirits. Duel through the haunted streets and face the mysterious shadows.')
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            synopsis = excluded.synopsis
    """)

    import json

    stage1_script = json.dumps({
        "turns": {
            "1": {
                "play": "The dark abyss churns. Echo activates **The Seed of Creation** (`TLOK-003`), Special Summoning **The Void of Creation** (`TLOK-002`)!",
                "damage": 500,
                "quote": "\"We are the silence before the first word...\""
            },
            "2": {
                "play": "Echo banishes materials to Special Summon **Formless the True Void of Creation** (`TLOK-005`)! A wave of void distortion strikes!",
                "damage": 1000,
                "quote": "\"Can your spirit maintain form against infinity?\""
            },
            "3": {
                "play": "Echo casts **The Spark of Creation** (`TLOK-012`), retrieving void essences and unleashing a concentrated beam!",
                "damage": 1200,
                "quote": "\"From nothingness, the spark ignites!\""
            }
        },
        "repeat": {
            "play": "Echo lashes out with residual primordial void energy!",
            "damage": 800,
            "quote": "\"The void never sleeps...\""
        },
        "threshold_4000": "🌌 *Echo of the Void falters as its cosmic density collapses! \"You... withstand the void?!\"*"
    })

    stage3_script = json.dumps({
        "turns": {
            "1": {
                "play": "ProfessorSeanEX steps forward as the skies radiate brilliant DIVINE amber. \"Let us begin with the foundation of all things.\" Normal Summons **Kasutamaiza, the Creator of Kustomazi** (`TLOK-001`) with 4000 ATK!",
                "damage": 1000,
                "quote": "\"Observe the power that crafted the stars!\""
            },
            "2": {
                "play": "ProfessorSeanEX casts **Alchemical Bonds** (`TLOK-013`), conducting a contact summon of **Mohousha the Accursed of the Great Kasutamaiza** (`TLOK-006`)! A dark reflection strikes!",
                "damage": 1500,
                "quote": "\"Creation and corruption walk hand in hand. How will you respond?\""
            },
            "3": {
                "play": "ProfessorSeanEX channels the cosmos: \"Ascend to the pinnacle!\" Contact Fuses into **The Great Kasutamaiza** (`TLOK-007`)! Celestial wrath strikes your field!",
                "damage": 2000,
                "quote": "\"Stand firm, duelist! Show me your bond with Kustomazi!\""
            }
        },
        "repeat": {
            "play": "The Great Kasutamaiza commands supreme elemental force!",
            "damage": 1500,
            "quote": "\"The chronicle must continue!\""
        },
        "threshold_4000": "👑 *ProfessorSeanEX laughs heartily with profound respect! \"Splendid! Few have pushed my Kasutamaiza deck this far! Let us see this duel through to its magnificent conclusion!\"*"
    })

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

    stages = [
        (1, 1, 1, 'Whispers of the Primordial Void',
         'The darkness stretches infinitely. Before the stars ignited, formless currents of cosmic energy churned in silence. A spiritual echo of The Void of Creation manifests before you, testing if your spirit possesses the spark to wield the custom cards of Kustomazi.',
         'The void recedes with a gentle hum. A faint glimmer ignites within your deck—you have proven your resolve against the formless void.',
         'Echo of the Void', 'Primordial Emanation', 1, 1, 'SCRIPTED', 8000, stage1_script, 'Void Walker', 50000102),
        (2, 1, 2, 'Rites of the Celestial Temple',
         'Golden spires pierce the starry gloom. You stand before the Temple of the Great Kasutamaiza. The Servants of the Great Kasutamaiza step forward, their eyes blazing with divine fire. Only those who master the delicate balance between sacrifice and creation may approach the grand altar!',
         'The temple doors swing wide with resonant thunder. The acolytes bow in solemn reverence. You are deemed worthy to enter the inner sanctum.',
         'Acolytes of Kustomazi', 'Temple Guardians', 1, 1, 'AI', 8000, None, 'Temple Guardian', 50000111),
        (3, 1, 3, 'Trial of the Supreme Architect',
         '"Welcome, duelist," a resonant voice proclaims. ProfessorSeanEX, the Supreme Architect himself, descends from the cosmic throne. "You have braved the void and walked the sacred temple grounds. Now, show me if your bond with your deck can withstand the might of the Great Kasutamaiza! Let the creation duel begin!"',
         '"Astounding!" ProfessorSeanEX smiles with deep admiration. "You have harmonized with the primordial forces and mastered the customs of this realm. The Land of Kustomazi has found its true champion!" The heavens shine in celebration of your victory.',
         'ProfessorSeanEX', 'The Supreme Architect', 1, 1, 'SCRIPTED', 8000, stage3_script, "Architect's Champion", 50000101),
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

    for s in stages:
        cur.execute("""
            INSERT INTO story_stages (id, chapter_id, stage_number, title, intro_dialogue, outro_dialogue,
                                     opponent_name, opponent_title, opponent_character_id, opponent_deck_id,
                                     encounter_type, boss_hp, script_data,
                                     reward_title, reward_card_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
