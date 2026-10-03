# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.domain.story
Description:
    Section 3.4: Pre-Constructed Character Decks & Story Integration Subsystem.
    Retrieves story decks constructed from the database (`decks` and `deck_cards`),
    computes partition counts, enforces MR5 legality badges, provides dynamic
    AI ELO matchmaking for story encounters without hardcoding, and copies
    archetype builds to player decks with full telemetry tracking.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import re
import aiosqlite
from typing import List, Dict, Any, Tuple, Optional

from ..foundation.constants import (
    STANDARD_MIN_MAIN_DECK,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
    STANDARD_MAX_SIDE_DECK,
)
from ..foundation.types import StoryDeckRecord

# =============================================================================
# BLOCK 3: BODY BLOCK (Story Decks & Dynamic AI Matchmaking Engine)
# =============================================================================


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Pre-Constructed Character Decks Retrieval & Telemetry
# -----------------------------------------------------------------------------

async def fetch_character_decks(db_path: str) -> List[Dict[str, Any]]:
    """
    Returns all pre-constructed story character decks with enriched telemetry:
    - Duelist and character metadata
    - Partitioned card counts (Main, Extra, Side, Total)
    - Master Rule 5 legality status
    - Story Chapter / ELO rating for AI progression
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT d.*, c.name AS duelist_name, c.alias AS duelist_alias
            FROM decks d
            LEFT JOIN characters c ON d.character_id = c.id
            ORDER BY d.id ASC
        """)
        deck_rows = await cur.fetchall()

        cur = await db.execute("""
            SELECT dc.deck_id,
                   SUM(CASE WHEN UPPER(dc.section) = 'MAIN' THEN dc.quantity ELSE 0 END) AS main_count,
                   SUM(CASE WHEN UPPER(dc.section) = 'EXTRA' THEN dc.quantity ELSE 0 END) AS extra_count,
                   SUM(CASE WHEN UPPER(dc.section) = 'SIDE' THEN dc.quantity ELSE 0 END) AS side_count,
                   SUM(dc.quantity) AS total_count
            FROM deck_cards dc
            GROUP BY dc.deck_id
        """)
        counts_map = {r["deck_id"]: dict(r) for r in await cur.fetchall()}

        result: List[Dict[str, Any]] = []
        for r in deck_rows:
            d = dict(r)
            d_id = d["id"]
            counts = counts_map.get(d_id, {"main_count": 0, "extra_count": 0, "side_count": 0, "total_count": 0})

            main_c = counts["main_count"] or 0
            extra_c = counts["extra_count"] or 0
            side_c = counts["side_count"] or 0
            total_c = counts["total_count"] or 0

            is_legal = (
                main_c >= STANDARD_MIN_MAIN_DECK and
                main_c <= STANDARD_MAX_MAIN_DECK and
                extra_c <= STANDARD_MAX_EXTRA_DECK and
                side_c <= STANDARD_MAX_SIDE_DECK
            )

            if is_legal:
                legality_badge = f"✅ Legal (MR5: {main_c} Main | {extra_c} Extra)"
            else:
                legality_badge = f"⚠️ Story / Alpha Format ({main_c} Main | {extra_c} Extra)"

            desc = d.get("description") or ""
            elo_match = re.search(r'ELO\s*(\d+)', desc)
            if elo_match:
                ai_elo = int(elo_match.group(1))
            elif d_id == 1:
                ai_elo = 1000
            elif d_id == 2:
                ai_elo = 1200
            elif d_id == 3:
                ai_elo = 1000
            elif d_id == 4:
                ai_elo = 1100
            elif d_id == 5:
                ai_elo = 1450
            elif d_id == 6:
                ai_elo = 1600
            elif d_id >= 7:
                ai_elo = 1800
            else:
                ai_elo = 1200

            chapter_match = re.search(r'(Chapter\s*\d+|Apex Boss)', desc)
            story_chapter = chapter_match.group(1) if chapter_match else "Story Deck"

            d["main_count"] = main_c
            d["extra_count"] = extra_c
            d["side_count"] = side_c
            d["total_count"] = total_c
            d["is_legal"] = is_legal
            d["legality_badge"] = legality_badge
            d["ai_elo"] = ai_elo
            d["story_chapter"] = story_chapter
            result.append(d)

        return result


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Single Character Deck Retrieval with Partitioning
# -----------------------------------------------------------------------------

async def fetch_character_deck_by_id(
    db_path: str,
    deck_id: int
) -> Optional[Dict[str, Any]]:
    """Fetches a character deck along with all registered deck_cards and complete telemetry."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT d.*, c.name AS duelist_name, c.alias AS duelist_alias
            FROM decks d
            LEFT JOIN characters c ON d.character_id = c.id
            WHERE d.id = ?
        """, (deck_id,))
        row = await cur.fetchone()
        if not row:
            return None
        deck = dict(row)

        cur = await db.execute("""
            SELECT dc.section, dc.quantity, c.id, c.name, c.set_number, c.card_type, c.card_subtype,
                   c.attribute, c.level_or_rank_or_link, c.atk, c.def, c.rarity,
                   c.monster_type, c.effect_text, c.archetype
            FROM deck_cards dc
            JOIN custom_cards c ON dc.card_id = c.id
            WHERE dc.deck_id = ?
            ORDER BY 
                CASE UPPER(dc.section) 
                    WHEN 'MAIN' THEN 1 
                    WHEN 'EXTRA' THEN 2 
                    WHEN 'SIDE' THEN 3 
                    ELSE 4 
                END,
                c.name ASC
        """, (deck_id,))
        cards = [dict(r) for r in await cur.fetchall()]
        deck["cards"] = cards

        main_c = sum(c.get("quantity", 1) for c in cards if (c.get("section") or "").upper() == "MAIN")
        extra_c = sum(c.get("quantity", 1) for c in cards if (c.get("section") or "").upper() == "EXTRA")
        side_c = sum(c.get("quantity", 1) for c in cards if (c.get("section") or "").upper() == "SIDE")
        total_c = main_c + extra_c + side_c

        is_legal = (
            main_c >= STANDARD_MIN_MAIN_DECK and
            main_c <= STANDARD_MAX_MAIN_DECK and
            extra_c <= STANDARD_MAX_EXTRA_DECK and
            side_c <= STANDARD_MAX_SIDE_DECK
        )
        legality_badge = f"✅ Legal (MR5: {main_c} Main | {extra_c} Extra)" if is_legal else f"⚠️ Story / Alpha Format ({main_c} Main | {extra_c} Extra)"

        desc = deck.get("description") or ""
        elo_match = re.search(r'ELO\s*(\d+)', desc)
        ai_elo = int(elo_match.group(1)) if elo_match else 1200

        deck["main_count"] = main_c
        deck["extra_count"] = extra_c
        deck["side_count"] = side_c
        deck["total_count"] = total_c
        deck["is_legal"] = is_legal
        deck["legality_badge"] = legality_badge
        deck["ai_elo"] = ai_elo

        return deck


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Archetype Deck Cloning to Player Active Deck
# -----------------------------------------------------------------------------

async def copy_character_deck_to_player_deck(
    db_path: str,
    user_id: str,
    deck_id: int
) -> Tuple[bool, str, int]:
    """Copies all cards from a character deck into the player's active deck."""
    user_id_str = str(user_id)
    deck = await fetch_character_deck_by_id(db_path, deck_id)
    if not deck:
        return False, "Story Deck not found", 0

    async with aiosqlite.connect(db_path) as db:
        # Decrement card_usage_stats for cards being replaced to prevent telemetry drift
        cur = await db.execute("SELECT card_id, quantity FROM player_decks WHERE user_id = ?", (user_id_str,))
        old_cards = await cur.fetchall()
        for old_cid, old_qty in old_cards:
            await db.execute("""
                UPDATE card_usage_stats
                SET times_decked = MAX(0, times_decked - ?)
                WHERE card_id = ?
            """, (old_qty, old_cid))

        await db.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id_str,))
        total_added = 0
        for card in deck.get("cards", []):
            cid = card["id"]
            qty = card["quantity"]
            await db.execute("""
                INSERT INTO player_decks (user_id, card_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id_str, cid, qty))
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    times_decked = times_decked + ?,
                    last_used_at = CURRENT_TIMESTAMP
            """, (cid, qty, qty))
            total_added += qty
        await db.commit()

    return True, deck["name"], total_added


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Dynamic AI ELO Matchmaking Engine
# -----------------------------------------------------------------------------

async def match_ai_deck_for_elo(
    db_path: str,
    target_elo: int
) -> Optional[Dict[str, Any]]:
    """
    Dynamically selects the optimal pre-built story deck closest to a given AI ELO rating.
    Allows AI dueling engines and story encounters to pick tournament-viable or progression
    decks calibrated to player matchmaking and difficulty without hardcoding.
    """
    decks = await fetch_character_decks(db_path)
    if not decks:
        return None

    best_match = min(decks, key=lambda d: abs(d.get("ai_elo", 1200) - target_elo))
    return best_match


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Story Summary Formatting & Presentation
# -----------------------------------------------------------------------------

def format_character_deck_summary(deck: Dict[str, Any]) -> str:
    """Formats a character deck into a clean, markdown discord embed/text summary."""
    name = deck.get("name", "Unknown Deck")
    duelist = deck.get("duelist_name") or "Story Character"
    elo = deck.get("ai_elo", 1200)
    main_c = deck.get("main_count", 0)
    extra_c = deck.get("extra_count", 0)
    badge = deck.get("legality_badge", "")
    desc = deck.get("description", "")

    lines = [
        f"**{name}** (Duelist: {duelist} | ELO: {elo})",
        f"• **Dimensions:** {main_c} Main | {extra_c} Extra ({badge})",
        f"• **Strategy:** {desc}"
    ]
    return "\n".join(lines)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "fetch_character_decks",
    "fetch_character_deck_by_id",
    "copy_character_deck_to_player_deck",
    "match_ai_deck_for_elo",
    "format_character_deck_summary",
]

