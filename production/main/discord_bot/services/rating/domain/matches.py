# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.domain.matches
Description:
    Domain Operations for Concluded Match Telemetry & Competitive ELO Resolution.
    Coordinates rating updates, match history recording (`duel_matches`),
    individual card usage telemetry (`card_usage_stats`), and macro deck
    performance stats (`player_saved_decks`).

Architectural Classification:
    Layer 1 (L1) - Domain Layer
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional
import aiosqlite

from production.main.logger import get_logger
from ..foundation.constants import MATCH_TYPE_RANKED, SCORE_DRAW, SCORE_LOSS, SCORE_WIN
from ..foundation.math import compute_elo_change, resolve_tier_info
from ..foundation.types import MatchRecordDict
from .player import get_or_create_player

logger = get_logger("discord_bot.services.rating.domain.matches")

# =============================================================================
# BLOCK 3: BODY BLOCK (Match Recording Operations)
# =============================================================================

async def ensure_duel_matches_schema(db: aiosqlite.Connection) -> None:
    """
    Ensures duel_matches schema compatibility.
    Note: Schema is authoritatively defined in schema_telemetry.sql and schema.sql.
    """
    pass


async def record_duel_match(
    db_path: str,
    p1_id: str,
    p2_id: str,
    winner_id: Optional[str],
    match_type: str = MATCH_TYPE_RANKED,
    turns: int = 1,
    summary: str = "",
    p1_deck: Optional[List[int]] = None,
    p2_deck: Optional[List[int]] = None,
    p1_name: Optional[str] = None,
    p2_name: Optional[str] = None,
    p1_deck_name: Optional[str] = None,
    p2_deck_name: Optional[str] = None,
) -> MatchRecordDict:
    """
    Processes a concluded duel match:
    1. Retrieves profiles for both duelists.
    2. Calculates updated Elo ratings and deltas if the match is RANKED.
    3. Commits updated stats, streaks, and tiers to `player_ratings`.
    4. Inserts historical match row into `duel_matches`.
    5. Updates micro telemetry in `card_usage_stats` (wins/losses per unique card).
    6. Updates macro telemetry in `player_saved_decks` (times used, wins, losses).

    Returns:
        MatchRecordDict payload with match ID, ELO deltas, and outcome details.
    """
    p1 = await get_or_create_player(db_path, p1_id, p1_name)
    p2 = await get_or_create_player(db_path, p2_id, p2_name)

    p1_elo_before = p1["elo"]
    p2_elo_before = p2["elo"]
    p1_elo_after = p1_elo_before
    p2_elo_after = p2_elo_before

    is_draw = (winner_id is None or winner_id == "DRAW")
    is_p1_win = (winner_id == str(p1_id))
    is_p2_win = (winner_id == str(p2_id))

    if match_type.upper() == MATCH_TYPE_RANKED:
        p1_total = p1["wins"] + p1["losses"] + p1["draws"]
        p2_total = p2["wins"] + p2["losses"] + p2["draws"]

        score = SCORE_DRAW if is_draw else (SCORE_WIN if is_p1_win else SCORE_LOSS)
        p1_elo_after, p2_elo_after = compute_elo_change(
            p1_elo_before, p2_elo_before, score, p1_total, p2_total
        )

    async with aiosqlite.connect(db_path) as db:
        # 1. Update Player 1 Profile
        p1_tier, _, _ = resolve_tier_info(p1_elo_after)
        p1_streak = (p1["win_streak"] + 1) if is_p1_win else 0
        p1_highest_streak = max(p1["highest_streak"], p1_streak)
        p1_highest_elo = max(p1["highest_elo"], p1_elo_after)

        await db.execute("""
            UPDATE player_ratings SET
                elo = ?,
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                win_streak = ?,
                highest_streak = ?,
                highest_elo = ?,
                tier = ?,
                last_match_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            p1_elo_after,
            1 if is_p1_win else 0,
            1 if is_p2_win else 0,
            1 if is_draw else 0,
            p1_streak,
            p1_highest_streak,
            p1_highest_elo,
            p1_tier,
            str(p1_id)
        ))

        # 2. Update Player 2 Profile
        p2_tier, _, _ = resolve_tier_info(p2_elo_after)
        p2_streak = (p2["win_streak"] + 1) if is_p2_win else 0
        p2_highest_streak = max(p2["highest_streak"], p2_streak)
        p2_highest_elo = max(p2["highest_elo"], p2_elo_after)

        await db.execute("""
            UPDATE player_ratings SET
                elo = ?,
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                win_streak = ?,
                highest_streak = ?,
                highest_elo = ?,
                tier = ?,
                last_match_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            p2_elo_after,
            1 if is_p2_win else 0,
            1 if is_p1_win else 0,
            1 if is_draw else 0,
            p2_streak,
            p2_highest_streak,
            p2_highest_elo,
            p2_tier,
            str(p2_id)
        ))

        # 3. Schema Check & Match Recording
        await ensure_duel_matches_schema(db)
        cur = await db.execute("""
            INSERT INTO duel_matches (
                match_type, p1_user_id, p2_user_id, winner_user_id,
                p1_elo_before, p1_elo_after, p2_elo_before, p2_elo_after,
                turns, summary, p1_deck_name, p2_deck_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_type.upper(), str(p1_id), str(p2_id),
            winner_id or "DRAW",
            p1_elo_before, p1_elo_after, p2_elo_before, p2_elo_after,
            turns, summary, p1_deck_name, p2_deck_name
        ))
        match_id = cur.lastrowid

        # 4. Micro Telemetry: Update card wins/losses in card_usage_stats
        if p1_deck:
            for cid in set(p1_deck):
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        wins = wins + ?,
                        losses = losses + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (
                    cid,
                    1 if is_p1_win else 0,
                    1 if is_p2_win else 0,
                    1 if is_p1_win else 0,
                    1 if is_p2_win else 0
                ))

        if p2_deck:
            for cid in set(p2_deck):
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        wins = wins + ?,
                        losses = losses + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (
                    cid,
                    1 if is_p2_win else 0,
                    1 if is_p1_win else 0,
                    1 if is_p2_win else 0,
                    1 if is_p1_win else 0
                ))

        # 5. Macro Telemetry: Update saved deck slot usage in player_saved_decks
        if p1_deck_name:
            await db.execute("""
                UPDATE player_saved_decks
                SET times_used = times_used + 1,
                    wins = wins + ?,
                    losses = losses + ?,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND deck_name = ?
            """, (1 if is_p1_win else 0, 1 if is_p2_win else 0, str(p1_id), p1_deck_name))

        if p2_deck_name:
            await db.execute("""
                UPDATE player_saved_decks
                SET times_used = times_used + 1,
                    wins = wins + ?,
                    losses = losses + ?,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND deck_name = ?
            """, (1 if is_p2_win else 0, 1 if is_p1_win else 0, str(p2_id), p2_deck_name))

        await db.commit()

    logger.info(
        f"Recorded {match_type} duel #{match_id}: P1 {p1_elo_before}->{p1_elo_after}, "
        f"P2 {p2_elo_before}->{p2_elo_after} | Winner: {winner_id or 'DRAW'}"
    )

    return {
        "match_id": match_id,
        "match_type": match_type.upper(),
        "p1_id": str(p1_id),
        "p2_id": str(p2_id),
        "p1_deck_name": p1_deck_name,
        "p2_deck_name": p2_deck_name,
        "p1_elo_before": p1_elo_before,
        "p1_elo_after": p1_elo_after,
        "p1_elo_delta": p1_elo_after - p1_elo_before,
        "p2_elo_before": p2_elo_before,
        "p2_elo_after": p2_elo_after,
        "p2_elo_delta": p2_elo_after - p2_elo_before,
        "winner_id": winner_id or "DRAW",
        "turns": turns,
        "summary": summary,
    }


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "record_duel_match",
    "ensure_duel_matches_schema",
]
