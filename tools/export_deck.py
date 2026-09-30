#!/usr/bin/env python3
"""
Deck Exporter
Exports character decks from ygo_story.db to .ydk files compatible with
EDOPro, YGOPro, Duelingbook (import), and Omega.
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
DECKS_DIR = os.path.join(BASE_DIR, "server-data", "decks")

def export_deck(deck_id, output_path=None):
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT id, name FROM decks WHERE id = ?", (deck_id,))
    deck = cur.fetchone()
    if not deck:
        print(f"[-] Deck {deck_id} not found.")
        conn.close()
        return None
        
    did, dname = deck
    clean_name = "".join(c for c in dname if c.isalnum() or c in (' ', '_', '-')).strip()
    if not output_path:
        output_path = os.path.join(DECKS_DIR, f"{clean_name}.ydk")
        
    cur.execute("""
        SELECT card_id, quantity, section 
        FROM deck_cards 
        WHERE deck_id = ?
        ORDER BY section DESC, card_id ASC
    """, (deck_id,))
    
    cards = cur.fetchall()
    
    main_cards = []
    extra_cards = []
    side_cards = []
    
    for cid, qty, sec in cards:
        target_list = main_cards if sec == 'MAIN' else (extra_cards if sec == 'EXTRA' else side_cards)
        for _ in range(qty):
            target_list.append(str(cid))
            
    ydk_content = [
        f"#created by YGO Story Engine",
        f"#main",
        *main_cards,
        f"#extra",
        *extra_cards,
        f"!side",
        *side_cards,
        ""
    ]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ydk_content))
        
    print(f"[+] Exported deck '{dname}' to {output_path}")
    conn.close()
    return output_path

def export_all_decks():
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM decks")
    deck_ids = [row[0] for row in cur.fetchall()]
    conn.close()
    for did in deck_ids:
        export_deck(did)

if __name__ == "__main__":
    export_all_decks()
