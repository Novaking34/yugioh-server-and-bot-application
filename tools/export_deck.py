#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Deck Exporter (.ydk format)
=============================================================================
This tool exports character and player decks from the Story Database into the
standard `.ydk` (Yu-Gi-Oh! Deck) plain-text format used by all simulator clients:
- EDOPro / Project Ignis
- YGOPro / Koishi
- Duelingbook (import deck)
- Yu-Gi-Oh! Omega

The .ydk File Specification:
----------------------------
A `.ydk` file is a plain UTF-8 text file divided into three main sections:
1. `#main`: Passcodes (8-digit IDs) of cards in the Main Deck (40-60 cards).
2. `#extra`: Passcodes of Extra Deck monsters (Fusion, Synchro, Xyz, Link) (up to 15 cards).
3. `!side`: Passcodes of the Side Deck (up to 15 cards). Note the exclamation mark prefix.

Each card passcode appears on its own line, repeated for each copy in the deck.
=============================================================================
"""

import sqlite3
import os
import sys
import re
from typing import Optional, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
DECKS_DIR = os.path.join(BASE_DIR, "server-data", "decks")


def sanitize_filename(name: str) -> str:
    """Removes filesystem-unsafe characters from deck names."""
    return re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip()


def export_deck(deck_id: int, output_path: Optional[str] = None) -> Optional[str]:
    """
    Exports a character story deck by its database ID to a `.ydk` file.

    Args:
        deck_id: The integer ID in the `decks` table.
        output_path: Optional custom destination path. If None, saves to `server-data/decks/`.

    Returns:
        str: Absolute path of the generated .ydk file, or None if deck not found.
    """
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM decks WHERE id = ?", (deck_id,))
    deck = cur.fetchone()
    if not deck:
        print(f"[-] Story Deck ID {deck_id} not found in database.", file=sys.stderr)
        conn.close()
        return None

    did, dname = deck
    clean_name = sanitize_filename(dname) or f"Deck_{did}"

    if not output_path:
        output_path = os.path.join(DECKS_DIR, f"{clean_name}.ydk")

    # Fetch all cards partitioned by section
    cur.execute("""
        SELECT card_id, quantity, section 
        FROM deck_cards 
        WHERE deck_id = ?
        ORDER BY section DESC, card_id ASC
    """, (deck_id,))
    cards = cur.fetchall()

    main_cards: List[str] = []
    extra_cards: List[str] = []
    side_cards: List[str] = []

    for cid, qty, sec in cards:
        sec_upper = (sec or 'MAIN').upper()
        target = main_cards if sec_upper == 'MAIN' else (extra_cards if sec_upper == 'EXTRA' else side_cards)
        for _ in range(qty):
            target.append(str(cid))

    ydk_lines = [
        "#created by Yu-Gi-Oh Story Platform",
        f"#deck: {dname}",
        "#main",
        *main_cards,
        "#extra",
        *extra_cards,
        "!side",
        *side_cards,
        ""
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ydk_lines))

    print(f"[+] Exported Story Deck '{dname}' ({len(main_cards)} Main, {len(extra_cards)} Extra) -> {output_path}")
    conn.close()
    return output_path


def export_player_deck(user_id: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Exports a Discord player's active deck (from `player_decks`) to a `.ydk` file.
    """
    conn = sqlite3.connect(STORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT pd.quantity, cc.id, cc.name, cc.card_type, cc.card_subtype
        FROM player_decks pd
        JOIN custom_cards cc ON pd.card_id = cc.id
        WHERE pd.user_id = ?
        ORDER BY cc.card_type DESC, cc.name ASC
    """, (str(user_id),))
    cards = cur.fetchall()

    if not cards:
        print(f"[-] No cards found for user {user_id}", file=sys.stderr)
        conn.close()
        return None

    if not output_path:
        output_path = os.path.join(DECKS_DIR, f"player_{user_id}.ydk")

    main_cards: List[str] = []
    extra_cards: List[str] = []

    extra_types = {'fusion', 'synchro', 'xyz', 'link'}
    for row in cards:
        cid = str(row['id'])
        csub = (row['card_subtype'] or '').lower()
        target = extra_cards if csub in extra_types else main_cards
        for _ in range(row['quantity']):
            target.append(cid)

    ydk_lines = [
        f"#created by Discord User {user_id}",
        "#main",
        *main_cards,
        "#extra",
        *extra_cards,
        "!side",
        ""
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ydk_lines))

    print(f"[+] Exported Player Deck for user {user_id} -> {output_path}")
    conn.close()
    return output_path


def export_all_decks():
    """Exports all registered character decks in the database."""
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM decks")
    deck_ids = [row[0] for row in cur.fetchall()]
    conn.close()

    print(f"[*] Exporting {len(deck_ids)} character story decks...")
    for did in deck_ids:
        export_deck(did)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            target_id = int(sys.argv[1])
            export_deck(target_id)
        except ValueError:
            print("Usage: python3 export_deck.py [deck_id]")
    else:
        export_all_decks()
