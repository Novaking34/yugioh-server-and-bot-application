# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.domain.mutators
Description:
    Sub-Block 3.4: Live Duel Event Tracking Mutators.
    Atomically updates card draws, on-field activations, match wins/losses,
    and deck inclusions in SQLite within high-performance batch transactions.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import aiosqlite
from typing import Optional, Dict, Sequence

from production.main.logger import get_logger

logger = get_logger("discord_bot.services.card.mutators")

# =============================================================================
# BLOCK 3: BODY BLOCK (Event Tracking Mutator Functions)
# =============================================================================

async def track_card_draw(db_path: str, card_id: int, count: int = 1) -> None:
    """Increments draw count for a card during live duels."""
    if count <= 0:
        return
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, times_drawn, last_used_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    times_drawn = times_drawn + ?,
                    last_used_at = CURRENT_TIMESTAMP
            """, (card_id, count, count))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to record card draw for ID {card_id}: {e}")


async def track_cards_drawn(db_path: str, card_ids: Sequence[int]) -> None:
    """
    Atomically records multi-card draws (e.g. 5-card opening hand) in a single transaction.
    """
    if not card_ids:
        return
    counts: Dict[int, int] = {}
    for cid in card_ids:
        counts[cid] = counts.get(cid, 0) + 1
    try:
        async with aiosqlite.connect(db_path) as db:
            for cid, count in counts.items():
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_drawn, last_used_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_drawn = times_drawn + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (cid, count, count))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to batch record card draws: {e}")


async def track_card_play(db_path: str, card_id: int, count: int = 1) -> None:
    """Increments play count for a card when summoned or activated."""
    if count <= 0:
        return
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, times_played, last_used_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    times_played = times_played + ?,
                    last_used_at = CURRENT_TIMESTAMP
            """, (card_id, count, count))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to record card play for ID {card_id}: {e}")


async def track_cards_played(db_path: str, card_ids: Sequence[int]) -> None:
    """
    Atomically records multi-card plays in a single transaction.
    """
    if not card_ids:
        return
    counts: Dict[int, int] = {}
    for cid in card_ids:
        counts[cid] = counts.get(cid, 0) + 1
    try:
        async with aiosqlite.connect(db_path) as db:
            for cid, count in counts.items():
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_played, last_used_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_played = times_played + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (cid, count, count))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to batch record card plays: {e}")


async def track_card_match_result(db_path: str, card_id: int, is_win: bool) -> None:
    """
    Records a match win or loss for a single card in an active deck.
    """
    w = 1 if is_win else 0
    l = 0 if is_win else 1
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    wins = wins + ?,
                    losses = losses + ?,
                    last_used_at = CURRENT_TIMESTAMP
            """, (card_id, w, l, w, l))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to record match result for card ID {card_id}: {e}")


async def track_cards_match_result(db_path: str, card_ids: Sequence[int], is_win: bool) -> None:
    """
    Atomically records match outcome for all distinct cards in a player's deck.
    Deduplicates card IDs so each distinct card receives 1 win or 1 loss per match.
    """
    if not card_ids:
        return
    unique_ids = set(card_ids)
    w = 1 if is_win else 0
    l = 0 if is_win else 1
    try:
        async with aiosqlite.connect(db_path) as db:
            for cid in unique_ids:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        wins = wins + ?,
                        losses = losses + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (cid, w, l, w, l))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to batch record match results for cards: {e}")


async def track_deck_inclusion(db_path: str, card_id: int, delta: int) -> None:
    """Updates the count of player decks including this card."""
    if delta == 0:
        return
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                VALUES (?, MAX(0, ?), CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    times_decked = MAX(0, times_decked + ?),
                    last_used_at = CURRENT_TIMESTAMP
            """, (card_id, delta, delta))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to track deck inclusion for ID {card_id}: {e}")


async def batch_track_deck_inclusions(db_path: str, card_deltas: Dict[int, int]) -> None:
    """
    Atomically updates deck inclusion counts for multiple cards in a single transaction.
    """
    if not card_deltas:
        return
    try:
        async with aiosqlite.connect(db_path) as db:
            for cid, delta in card_deltas.items():
                if delta != 0:
                    await db.execute("""
                        INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                        VALUES (?, MAX(0, ?), CURRENT_TIMESTAMP)
                        ON CONFLICT(card_id) DO UPDATE SET
                            times_decked = MAX(0, times_decked + ?),
                            last_used_at = CURRENT_TIMESTAMP
                    """, (cid, delta, delta))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to batch track deck inclusions: {e}")


async def reset_card_telemetry(db_path: str, card_id: Optional[int] = None) -> None:
    """
    Resets telemetry counters to zero for a specific card or all cards (maintenance/testing).
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            if card_id is not None:
                await db.execute("""
                    UPDATE card_usage_stats
                    SET times_decked = 0, times_drawn = 0, times_played = 0,
                        wins = 0, losses = 0, last_used_at = CURRENT_TIMESTAMP
                    WHERE card_id = ?
                """, (card_id,))
            else:
                await db.execute("""
                    UPDATE card_usage_stats
                    SET times_decked = 0, times_drawn = 0, times_played = 0,
                        wins = 0, losses = 0, last_used_at = CURRENT_TIMESTAMP
                """)
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to reset card telemetry: {e}")


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "track_card_draw",
    "track_cards_drawn",
    "track_card_play",
    "track_cards_played",
    "track_card_match_result",
    "track_cards_match_result",
    "track_deck_inclusion",
    "batch_track_deck_inclusions",
    "reset_card_telemetry",
]
