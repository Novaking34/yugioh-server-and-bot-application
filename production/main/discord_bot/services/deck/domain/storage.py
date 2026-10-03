# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.domain.storage
Description:
    Section 3.2: Player Active Deck CRUD, Partitioning & Persistence Subsystem.
    Manages active deck records in SQLite (player_decks), enforces section
    capacity limits (Main <= 60, Extra <= 15), checks banlist caps, and
    maintains card usage telemetry.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import aiosqlite
from typing import List, Dict, Any, Tuple, Optional

from ..foundation.constants import (
    STANDARD_MIN_MAIN_DECK,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
    STANDARD_MAX_SIDE_DECK,
    MAX_COPIES_PER_CARD,
    BANLIST_LIMITS,
)
from ..foundation.classifier import is_extra_deck_card
from ..foundation.types import DeckPartition

# =============================================================================
# BLOCK 3: BODY BLOCK (Active Deck Storage Engine & Operations)
# =============================================================================


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Active Deck Query & Flat ID Retrieval
# -----------------------------------------------------------------------------

async def fetch_player_deck(db_path: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all cards in a player's personal deck, sorted by category and name.
    Pulls comprehensive stats: Level, Attribute, Species, Rarity, Effect Text.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT pd.quantity, c.id, c.name, c.set_number, c.card_type, c.card_subtype, 
                   c.attribute, c.level_or_rank_or_link, c.level_or_rank_or_link AS level,
                   c.atk, c.def, c.rarity, c.monster_type, c.effect_text, c.archetype, 
                   c.banlist_status, c.local_image_path, c.image_url
            FROM player_decks pd
            JOIN custom_cards c ON pd.card_id = c.id
            WHERE pd.user_id = ?
            ORDER BY 
                CASE c.card_type 
                    WHEN 'Monster' THEN 1 
                    WHEN 'Spell' THEN 2 
                    WHEN 'Trap' THEN 3 
                    ELSE 4 
                END,
                c.name ASC
        """, (str(user_id),))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def fetch_player_card_ids(db_path: str, user_id: str) -> List[int]:
    """Returns flat list of card IDs (expanded by quantity) for duel initialization."""
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "SELECT card_id, quantity FROM player_decks WHERE user_id = ?",
            (str(user_id),)
        )
        rows = await cur.fetchall()
        cards = []
        for cid, qty in rows:
            cards.extend([cid] * qty)
        return cards


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Partitioning & Master Rule Min/Max Boundary Checks
# -----------------------------------------------------------------------------

async def partition_player_deck(db_path: str, user_id: str) -> DeckPartition:
    """
    Partitions the player's deck into Main Deck, Extra Deck, and Side Deck sections.
    Enforces Master Rule 5 Min/Max boundary checks and flags legality status:
    - Main Deck: 40 to 60 cards
    - Extra Deck: 0 to 15 cards
    - Side Deck: 0 to 15 cards
    - Max copies: <= 3 (or banlist ceiling)
    """
    cards = await fetch_player_deck(db_path, user_id)
    
    main_cards: List[Dict[str, Any]] = []
    extra_cards: List[Dict[str, Any]] = []
    side_cards: List[Dict[str, Any]] = []

    main_count = 0
    extra_count = 0
    side_count = 0

    violations: List[str] = []

    for c in cards:
        qty = c.get("quantity", 1)
        if is_extra_deck_card(c):
            extra_cards.append(c)
            extra_count += qty
        else:
            main_cards.append(c)
            main_count += qty

        # Check individual card limits
        banlist = c.get("banlist_status") or "Unlimited"
        max_c = BANLIST_LIMITS.get(banlist, MAX_COPIES_PER_CARD)
        if qty > max_c:
            violations.append(f"Card '{c['name']}' has {qty} copies (Banlist limit: {max_c}).")

    total_count = main_count + extra_count + side_count

    # Master Rule 5 Legality Checks
    main_min_met = main_count >= STANDARD_MIN_MAIN_DECK
    main_max_met = main_count <= STANDARD_MAX_MAIN_DECK
    extra_max_met = extra_count <= STANDARD_MAX_EXTRA_DECK
    side_max_met = side_count <= STANDARD_MAX_SIDE_DECK

    if not main_min_met:
        needed = STANDARD_MIN_MAIN_DECK - main_count
        violations.append(f"Main Deck has only {main_count} cards (Minimum 40 required, need {needed} more).")
    if not main_max_met:
        excess = main_count - STANDARD_MAX_MAIN_DECK
        violations.append(f"Main Deck has {main_count} cards (Maximum 60 allowed, {excess} over limit).")
    if not extra_max_met:
        excess_extra = extra_count - STANDARD_MAX_EXTRA_DECK
        violations.append(f"Extra Deck has {extra_count} cards (Maximum 15 allowed, {excess_extra} over limit).")
    if not side_max_met:
        excess_side = side_count - STANDARD_MAX_SIDE_DECK
        violations.append(f"Side Deck has {side_count} cards (Maximum 15 allowed, {excess_side} over limit).")

    is_legal = (main_min_met and main_max_met and extra_max_met and side_max_met and len(violations) == 0)

    if is_legal:
        legality_badge = f"✅ Tournament Legal (MR5: {main_count} Main | {extra_count} Extra)"
    elif not main_min_met:
        legality_badge = f"⚠️ Illegal Deck (Under Minimum: {main_count}/40 cards)"
    elif not main_max_met:
        legality_badge = f"⚠️ Illegal Deck (Over Maximum: {main_count}/60 cards)"
    elif not extra_max_met:
        legality_badge = f"⚠️ Illegal Deck (Extra Deck Full: {extra_count}/15 cards)"
    else:
        legality_badge = f"⚠️ Illegal Deck ({len(violations)} Violation(s))"

    return {
        "main_deck": main_cards,
        "extra_deck": extra_cards,
        "side_deck": side_cards,
        "main_count": main_count,
        "extra_count": extra_count,
        "side_count": side_count,
        "total_count": total_count,
        "is_legal": is_legal,
        "legality_badge": legality_badge,
        "violations": violations,
        "limits": {
            "min_main": STANDARD_MIN_MAIN_DECK,
            "max_main": STANDARD_MAX_MAIN_DECK,
            "max_extra": STANDARD_MAX_EXTRA_DECK,
            "max_side": STANDARD_MAX_SIDE_DECK,
        }
    }


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Card Insertion & Capacity Enforcement
# -----------------------------------------------------------------------------

async def add_card_to_player_deck(
    db_path: str,
    user_id: str,
    card_id: int,
    quantity: int = 1
) -> Tuple[bool, str, int]:
    """
    Adds 1 to 3 copies of a card to the player's deck.
    Respects individual card Banlist limits (Forbidden = 0, Limited = 1, etc.)
    and enforces Deck Section Capacity guardrails (Main <= 60, Extra <= 15).
    """
    user_id_str = str(user_id)
    qty = max(1, quantity)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        # 1. Check card data and banlist status
        cur = await db.execute("""
            SELECT id, name, set_number, card_type, card_subtype, banlist_status 
            FROM custom_cards WHERE id = ?
        """, (card_id,))
        card_row = await cur.fetchone()
        if not card_row:
            return False, "Unknown Card", 0

        card = dict(card_row)
        cname = card["name"]
        set_num = card["set_number"]
        banlist = card.get("banlist_status") or "Unlimited"

        max_allowed = BANLIST_LIMITS.get(banlist, MAX_COPIES_PER_CARD)
        if max_allowed == 0:
            return False, f"{cname} is Forbidden", 0

        # 2. Check current quantity of this card in deck
        cur = await db.execute(
            "SELECT quantity FROM player_decks WHERE user_id = ? AND card_id = ?",
            (user_id_str, card_id)
        )
        row = await cur.fetchone()
        current_qty = row[0] if row else 0

        new_qty = min(max_allowed, current_qty + qty)
        qty_to_add = new_qty - current_qty

        # 3. Enforce Deck Section Capacity
        is_extra = is_extra_deck_card(card)
        cur = await db.execute("""
            SELECT pd.quantity, c.card_type, c.card_subtype 
            FROM player_decks pd
            JOIN custom_cards c ON pd.card_id = c.id
            WHERE pd.user_id = ?
        """, (user_id_str,))
        active_rows = await cur.fetchall()

        current_extra_total = sum(
            r["quantity"] for r in active_rows if is_extra_deck_card(dict(r))
        )
        current_main_total = sum(
            r["quantity"] for r in active_rows if not is_extra_deck_card(dict(r))
        )

        if is_extra:
            if current_extra_total >= STANDARD_MAX_EXTRA_DECK and qty_to_add > 0:
                return False, f"Cannot add {cname}: Extra Deck is already full ({current_extra_total}/{STANDARD_MAX_EXTRA_DECK} cards).", current_qty
            if (current_extra_total + qty_to_add) > STANDARD_MAX_EXTRA_DECK:
                qty_to_add = max(0, STANDARD_MAX_EXTRA_DECK - current_extra_total)
        else:
            if current_main_total >= STANDARD_MAX_MAIN_DECK and qty_to_add > 0:
                return False, f"Cannot add {cname}: Main Deck is already full ({current_main_total}/{STANDARD_MAX_MAIN_DECK} cards).", current_qty
            if (current_main_total + qty_to_add) > STANDARD_MAX_MAIN_DECK:
                qty_to_add = max(0, STANDARD_MAX_MAIN_DECK - current_main_total)

        new_qty = current_qty + qty_to_add

        # 4. Upsert record into player_decks
        await db.execute("""
            INSERT INTO player_decks (user_id, card_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = ?
        """, (user_id_str, card_id, new_qty, new_qty))

        # 5. Record card usage telemetry
        delta = new_qty - current_qty
        if delta > 0:
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    times_decked = times_decked + ?,
                    last_used_at = CURRENT_TIMESTAMP
            """, (card_id, delta, delta))

        await db.commit()
        display_name = f"{cname} [{set_num}]" if set_num else cname
        return True, display_name, new_qty


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Card Decrement & Removal
# -----------------------------------------------------------------------------

async def remove_card_from_player_deck(
    db_path: str,
    user_id: str,
    card_id: int,
    quantity: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Removes a card from the player's active deck.
    - If `quantity` is None or >= current quantity: completely deletes the card entry.
    - If `quantity` is specified and < current quantity: decrements the copies.
    Accurately decrements card usage telemetry.
    """
    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT c.name, pd.quantity 
            FROM player_decks pd 
            JOIN custom_cards c ON pd.card_id = c.id 
            WHERE pd.user_id = ? AND pd.card_id = ?
        """, (user_id_str, card_id))
        row = await cur.fetchone()
        if not row:
            return False, "Card not found in deck"

        cname, current_qty = row[0], row[1]
        qty_to_remove = current_qty if quantity is None or quantity >= current_qty else max(1, quantity)
        new_qty = current_qty - qty_to_remove

        if new_qty <= 0:
            await db.execute(
                "DELETE FROM player_decks WHERE user_id = ? AND card_id = ?",
                (user_id_str, card_id)
            )
        else:
            await db.execute(
                "UPDATE player_decks SET quantity = ? WHERE user_id = ? AND card_id = ?",
                (new_qty, user_id_str, card_id)
            )

        await db.execute("""
            UPDATE card_usage_stats 
            SET times_decked = MAX(0, times_decked - ?) 
            WHERE card_id = ?
        """, (qty_to_remove, card_id))
        await db.commit()

        msg = f"{cname} (-{qty_to_remove})" if new_qty > 0 else cname
        return True, msg


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Active Deck Flush & Telemetry Cleanup
# -----------------------------------------------------------------------------

async def clear_player_deck(db_path: str, user_id: str) -> int:
    """Clears all cards from the player's active deck and updates telemetry."""
    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "SELECT card_id, quantity FROM player_decks WHERE user_id = ?",
            (user_id_str,)
        )
        rows = await cur.fetchall()
        count = len(rows)

        for cid, qty in rows:
            await db.execute("""
                UPDATE card_usage_stats 
                SET times_decked = MAX(0, times_decked - ?) 
                WHERE card_id = ?
            """, (qty, cid))

        await db.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id_str,))
        await db.commit()
        return count


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "fetch_player_deck",
    "fetch_player_card_ids",
    "partition_player_deck",
    "add_card_to_player_deck",
    "remove_card_from_player_deck",
    "clear_player_deck",
]

