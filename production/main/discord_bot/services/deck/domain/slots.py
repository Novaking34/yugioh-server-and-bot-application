# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.domain.slots
Description:
    Section 3.3: Multi-Deck Slots & Named Deck Storage Subsystem.
    Manages named deck profiles saved by players in SQLite (player_saved_decks).
    Enforces a strict MAX_USER_DECK_SLOTS (20) ceiling, serializes to/from
    standard .YDK format, and computes telemetry and legality for saved slots.
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
    MAX_USER_DECK_SLOTS,
)
from .ydk import parse_ydk, export_to_ydk, import_ydk_to_player_deck
from ..foundation.types import SavedDeckSlot

# =============================================================================
# BLOCK 3: BODY BLOCK (Multi-Deck Named Slot Engine & Lifecycle)
# =============================================================================


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Database Schema Initialization
# -----------------------------------------------------------------------------

async def ensure_saved_deck_tables(db_path: str) -> None:
    """Ensures the player_saved_decks table exists for multi-deck support."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS player_saved_decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                deck_name TEXT NOT NULL,
                ydk_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, deck_name)
            )
        """)
        await db.commit()


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Named Deck Profile Saving & Slot Limit Enforcer
# -----------------------------------------------------------------------------

async def save_named_deck_slot(
    db_path: str,
    user_id: str,
    deck_name: str,
    cards: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    Saves the user's active deck as a named deck profile slot.
    - Enforces MAX_USER_DECK_SLOTS (20) ceiling per player.
    - Validates deck name length (1 to 50 characters).
    - Validates active deck is not empty.
    - Serializes current deck to standard .ydk format.
    """
    await ensure_saved_deck_tables(db_path)
    clean_name = deck_name.strip()
    if not clean_name:
        return False, "Deck name cannot be blank."
    if len(clean_name) > 50:
        return False, "Deck name must be 50 characters or fewer."

    if not cards:
        return False, "Cannot save an empty deck."

    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "SELECT deck_name FROM player_saved_decks WHERE user_id = ?",
            (user_id_str,)
        )
        saved_names = [r[0] for r in await cur.fetchall()]
        if clean_name not in saved_names and len(saved_names) >= MAX_USER_DECK_SLOTS:
            return False, f"Deck slot limit reached ({MAX_USER_DECK_SLOTS} slots maximum). Delete or overwrite an existing deck."

        ydk_content = export_to_ydk(cards, deck_title=clean_name)

        await db.execute("""
            INSERT INTO player_saved_decks (user_id, deck_name, ydk_content)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, deck_name) DO UPDATE SET
                ydk_content = excluded.ydk_content,
                created_at = CURRENT_TIMESTAMP
        """, (user_id_str, clean_name, ydk_content))
        await db.commit()

    return True, clean_name


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Named Profile Loading to Active Deck
# -----------------------------------------------------------------------------

async def load_named_deck_slot(
    db_path: str,
    user_id: str,
    deck_name: str
) -> Tuple[bool, str, int]:
    """Loads a previously saved named deck into the user's active deck."""
    await ensure_saved_deck_tables(db_path)
    user_id_str = str(user_id)
    clean_name = deck_name.strip()
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "SELECT ydk_content FROM player_saved_decks WHERE user_id = ? AND deck_name = ?",
            (user_id_str, clean_name)
        )
        row = await cur.fetchone()
        if not row:
            return False, f"Deck '{clean_name}' not found in your saved slots.", 0

        ydk_text = row[0]

    return await import_ydk_to_player_deck(db_path, user_id_str, ydk_text)


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Profile Telemetry Listing & Single Retrieval
# -----------------------------------------------------------------------------

async def list_user_deck_slots(db_path: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Returns all named decks saved by the specified user with enriched telemetry:
    - Card counts: Main, Extra, Side, and Total.
    - Master Rule 5 legality status and badge.
    - Timestamp and profile identifiers.
    """
    await ensure_saved_deck_tables(db_path)
    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT id, deck_name, ydk_content, created_at 
            FROM player_saved_decks 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id_str,))
        rows = await cur.fetchall()

        decks: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            ydk_text = d.get("ydk_content") or ""
            parsed = parse_ydk(ydk_text)

            main_c = parsed["main_count"]
            extra_c = parsed["extra_count"]
            side_c = parsed["side_count"]
            total_c = parsed["total_count"]

            is_legal = (
                main_c >= STANDARD_MIN_MAIN_DECK and
                main_c <= STANDARD_MAX_MAIN_DECK and
                extra_c <= STANDARD_MAX_EXTRA_DECK and
                side_c <= STANDARD_MAX_SIDE_DECK
            )
            if is_legal:
                legality_badge = f"✅ Legal (MR5: {main_c} Main | {extra_c} Extra)"
            elif main_c < STANDARD_MIN_MAIN_DECK:
                legality_badge = f"⚠️ Under Min ({main_c}/{STANDARD_MIN_MAIN_DECK} Main)"
            elif main_c > STANDARD_MAX_MAIN_DECK:
                legality_badge = f"⚠️ Over Max ({main_c}/{STANDARD_MAX_MAIN_DECK} Main)"
            elif extra_c > STANDARD_MAX_EXTRA_DECK:
                legality_badge = f"⚠️ Extra Full ({extra_c}/{STANDARD_MAX_EXTRA_DECK})"
            else:
                legality_badge = f"⚠️ Format Violation ({total_c} Cards)"

            d["main_count"] = main_c
            d["extra_count"] = extra_c
            d["side_count"] = side_c
            d["total_count"] = total_c
            d["is_legal"] = is_legal
            d["legality_badge"] = legality_badge
            decks.append(d)

        return decks


async def get_saved_deck_slot(
    db_path: str,
    user_id: str,
    deck_name: str
) -> Optional[Dict[str, Any]]:
    """Retrieves a single saved named deck with full telemetry."""
    decks = await list_user_deck_slots(db_path, user_id)
    clean = deck_name.strip().lower()
    for d in decks:
        if d["deck_name"].lower() == clean:
            return d
    return None


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Profile Renaming & Deletion Operations
# -----------------------------------------------------------------------------

async def rename_saved_deck_slot(
    db_path: str,
    user_id: str,
    old_name: str,
    new_name: str
) -> Tuple[bool, str]:
    """Renames a saved deck slot profile."""
    await ensure_saved_deck_tables(db_path)
    user_id_str = str(user_id)
    old_clean = old_name.strip()
    new_clean = new_name.strip()
    if not new_clean:
        return False, "New deck name cannot be blank."
    if len(new_clean) > 50:
        return False, "New deck name must be 50 characters or fewer."

    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "SELECT id FROM player_saved_decks WHERE user_id = ? AND deck_name = ?",
            (user_id_str, new_clean)
        )
        if await cur.fetchone():
            return False, f"A saved deck named '{new_clean}' already exists."

        cur = await db.execute(
            "UPDATE player_saved_decks SET deck_name = ? WHERE user_id = ? AND deck_name = ?",
            (new_clean, user_id_str, old_clean)
        )
        await db.commit()
        if cur.rowcount > 0:
            return True, new_clean
        return False, f"Deck '{old_clean}' not found."


async def delete_saved_deck_slot(
    db_path: str,
    user_id: str,
    deck_name: str
) -> bool:
    """Deletes a saved named deck profile."""
    await ensure_saved_deck_tables(db_path)
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute(
            "DELETE FROM player_saved_decks WHERE user_id = ? AND deck_name = ?",
            (str(user_id), deck_name.strip())
        )
        await db.commit()
        return cur.rowcount > 0


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "ensure_saved_deck_tables",
    "save_named_deck_slot",
    "load_named_deck_slot",
    "list_user_deck_slots",
    "get_saved_deck_slot",
    "rename_saved_deck_slot",
    "delete_saved_deck_slot",
]

