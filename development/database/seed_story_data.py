#!/usr/bin/env python3
"""
Seed script to initialize ygo_story.db with sample lore arcs, factions,
story duelists, custom cards (with Duelingbook attributes), and decks.
"""

import sqlite3
import os
import sys

# Resolve project paths
try:
    from config.paths import STORY_DB_PATH, SCHEMA_PATH
    DB_PATH = STORY_DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(BASE_DIR, "production", "main", "web", "ygo_story.db")
    SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

def initialize_database():
    print(f"[*] Initializing database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
        
    print("[+] Database schema created successfully.")
    
    # Check if data already exists
    cur.execute("SELECT COUNT(*) FROM custom_cards")
    if cur.fetchone()[0] > 0:
        print("[!] Database already populated. Skipping seed.")
        conn.close()
        return

    print("[*] Seeding story lore, characters, and custom cards...")
    
    # 1. Lore Arc
    cur.execute("""
        INSERT INTO lore_arcs (id, title, synopsis, era_or_season)
        VALUES (1, 'The Astral Fracture Saga', 
                'When the celestial vault shattered across the cosmos, ancient star-forged relics collided with anomalous void rifts, creating a high-stakes duel across dimensions.',
                'Season 1')
    """)
    
    # 2. Factions
    cur.execute("""
        INSERT INTO factions (id, name, lore_description, playstyle_overview, arc_id)
        VALUES 
        (1, 'Starforged Order', 
            'Custodians of celestial light who channel pure starlight through mechanical and crystalline armor.',
            'Light Warrior/Fairy archetype centered on high ATK, graveyard resurrection, and Rank 8 Xyz summoning.', 1),
        (2, 'Void Sovereigns', 
            'An entity collective born from the emptiness between realities, seeking to unravel all physical matter.',
            'Dark Cyberse/Dragon Link archetype that banishes opponent resources and thrives when hand size is minimal.', 1)
    """)
    
    # 3. Characters
    cur.execute("""
        INSERT INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
        VALUES 
        (1, 'Valen Vance', 'The Solar Vanguard', 
            'A prodigy duelist seeking to restore the celestial constellation before the fracture tears his home realm apart.',
            1, 1, 'https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=400'),
        (2, 'Morgana Vex', 'The Void Weaver', 
            'A rogue duelist whose deck resonates with abyssal frequencies, convinced that entropy is the universe’s natural state.',
            2, 1, 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400')
    """)
    
    # 4. Custom Cards
    cards = [
        (
            50000001,
            'Starforged Paladin Astraea',
            'Monster',
            'Effect',
            'LIGHT',
            'Warrior',
            4,
            None,
            1800,
            1200,
            None,
            'If this card is Normal or Special Summoned: You can add 1 "Starforged" Spell/Trap from your Deck to your hand. During your opponent\'s Main Phase (Quick Effect): You can Tribute this card; Special Summon 1 Level 8 "Starforged" monster from your hand or GY, but negate its effects until the end of this turn. You can only use each effect of "Starforged Paladin Astraea" once per turn.',
            None,
            'db_card_1001',
            'https://www.duelingbook.com/card?id=50000001',
            'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=600',
            'ProfSeanEx',
            'Astraea took the vow at the Citadel of Sol, swearing her blade to keep the astral fracture from swallowing the lower spires.',
            1,
            1,
            'Starter / Searcher'
        ),
        (
            50000002,
            'Starforged Sovereign - Sol Invictus',
            'Monster',
            'Xyz',
            'LIGHT',
            'Warrior',
            8,
            None,
            3000,
            2500,
            None,
            '2 Level 8 LIGHT monsters\nOnce per turn (Quick Effect): You can detach 1 material from this card, then target 1 face-up card on the field; banish it until the End Phase. When this card destroys an opponent\'s monster by battle: You can attach that monster to this card as material. If this card would be destroyed by battle or card effect, you can detach 1 material instead.',
            None,
            'db_card_1002',
            'https://www.duelingbook.com/card?id=50000002',
            'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600',
            'ProfSeanEx',
            'The celestial embodiment of the unshakable sun, forged in the dying core of the First Star.',
            1,
            1,
            'Ace / Boss Monster'
        ),
        (
            50000003,
            'Sanctuary of the Starforge',
            'Spell',
            'Field',
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            'When this card is activated: You can send 1 "Starforged" monster from your Deck to the GY. All "Starforged" monsters you control gain 300 ATK/DEF. Once per turn, if a "Starforged" Xyz Monster you control detaches a material: You can draw 1 card.',
            None,
            'db_card_1003',
            'https://www.duelingbook.com/card?id=50000003',
            'https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=600',
            'ProfSeanEx',
            'The ancient orbital forge where light was hammered into physical form before the cosmos fractured.',
            1,
            1,
            'Archetype Field Spell'
        ),
        (
            50000004,
            'Void Sovereign - Abyssal Ouroboros',
            'Monster',
            'Link',
            'DARK',
            'Dragon',
            4,
            None,
            2800,
            None,
            'BL,BR,T,B',
            '3+ Effect Monsters, including at least 1 DARK monster\nCannot be destroyed by battle with monsters summoned from the Extra Deck. (Quick Effect): You can target 1 card in your opponent\'s GY; banish it, and if you do, this card gains 200 ATK for each banished card until the end of this turn. When this card is Link Summoned: Banish the top 3 cards of both players\' Decks face-down.',
            None,
            'db_card_1004',
            'https://www.duelingbook.com/card?id=50000004',
            'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600',
            'ProfSeanEx',
            'An impossible serpent circling the void rift, devouring timeline branches and returning them to nothingness.',
            2,
            2,
            'Antagonist Boss Monster'
        ),
        (
            50000005,
            'Fracture of the Starlit Sky',
            'Spell',
            'Quick-Play',
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            'Target 1 face-up monster on the field; change its battle position, and if it was a Special Summoned monster, negate its effects until the end of this turn. If you control a "Starforged" or "Void Sovereign" monster, this card\'s activation and effect cannot be negated.',
            None,
            'db_card_1005',
            'https://www.duelingbook.com/card?id=50000005',
            'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600',
            'ProfSeanEx',
            'The moment the sky tore open, forever bridging the realm of starlight with the cold infinite void.',
            1,
            None,
            'Climax Lore Spell'
        )
    ]
    
    cur.executemany("""
        INSERT INTO custom_cards (
            id, name, card_type, card_subtype, attribute, monster_type,
            level_or_rank_or_link, scale, atk, def, link_arrows,
            effect_text, pendulum_effect, duelingbook_id, duelingbook_url,
            image_url, creator_name, lore_text, faction_id,
            signature_character_id, story_significance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cards)
    
    # 5. Populate FTS index
    cur.execute("""
        INSERT INTO cards_fts (rowid, name, effect_text, lore_text, card_type, monster_type)
        SELECT id, name, effect_text, lore_text, card_type, monster_type FROM custom_cards
    """)
    
    # 6. Decks
    cur.execute("""
        INSERT INTO decks (id, name, character_id, creator_name, description, duelingbook_deck_url)
        VALUES 
        (1, 'Sol Radiance - Valen Signature', 1, 'ProfSeanEx', 
         'Valen Vance''s premier deck combining Starforged warriors with Rank 8 celestial engines.', 
         'https://www.duelingbook.com/deck?id=1010101'),
        (2, 'Entropy Cascade - Morgana Deck', 2, 'ProfSeanEx', 
         'Morgana''s control/mill deck focused on Link Summoning the Void Sovereigns.', 
         'https://www.duelingbook.com/deck?id=1010102')
    """)
    
    # 7. Deck cards
    cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (1, 50000001, 3, 'MAIN')")
    cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (1, 50000003, 3, 'MAIN')")
    cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (1, 50000005, 2, 'MAIN')")
    cur.execute("INSERT INTO deck_cards (deck_id, card_id, quantity, section) VALUES (1, 50000002, 2, 'EXTRA')")
    
    # 8. Story Duel Log
    cur.execute("""
        INSERT INTO duel_logs (arc_id, chapter_or_episode, duelist_1_id, duelist_2_id, winner_id, duel_summary)
        VALUES 
        (1, 'Chapter 1: The Sky Weeps Glass', 1, 2, 1, 
         'Valen encounters Morgana near the Astral Observatory. Sol Invictus banishes Abyssal Ouroboros on Turn 6 to secure victory and seal the first localized rift.')
    """)
    
    conn.commit()
    conn.close()
    print("[+] Seeding completed successfully!")

if __name__ == "__main__":
    initialize_database()
