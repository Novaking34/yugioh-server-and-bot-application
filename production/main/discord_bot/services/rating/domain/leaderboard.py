# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.domain.leaderboard
Description:
    Domain Operations for Ranked Season Leaderboard Queries.
    Retrieves top-ranked duelists ordered by ELO score and victory counts,
    enriching records with win percentages and competitive division tiers.

Architectural Classification:
    Layer 1 (L1) - Domain Layer
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List
import aiosqlite

from production.main.logger import get_logger
from ..foundation.constants import DEFAULT_LEADERBOARD_LIMIT, DEFAULT_SEASON_ID, MAX_LEADERBOARD_LIMIT
from ..foundation.math import calculate_win_rate
from ..foundation.types import LeaderboardEntryDict

logger = get_logger("discord_bot.services.rating.domain.leaderboard")

# =============================================================================
# BLOCK 3: BODY BLOCK (Leaderboard Query Operations)
# =============================================================================

async def get_leaderboard(
    db_path: str,
    limit: int = DEFAULT_LEADERBOARD_LIMIT,
    season_id: str = DEFAULT_SEASON_ID
) -> List[LeaderboardEntryDict]:
    """
    Returns top-ranked duelists ordered by Elo rating for a specific season.

    Args:
        db_path: Absolute SQLite database path.
        limit: Maximum leaderboard entries to retrieve (clamped between 1 and MAX_LEADERBOARD_LIMIT).
        season_id: Competitive season filter (default: "Season 1").

    Returns:
        List of LeaderboardEntryDict records enriched with calculated win rates.
    """
    safe_limit = max(1, min(limit, MAX_LEADERBOARD_LIMIT))
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT user_id, username, elo, wins, losses, draws, win_streak, highest_elo, tier
            FROM player_ratings
            WHERE season_id = ?
            ORDER BY elo DESC, wins DESC
            LIMIT ?
        """, (season_id, safe_limit))
        rows = await cur.fetchall()

        results: List[LeaderboardEntryDict] = []
        for r in rows:
            d = dict(r)
            d["win_rate"] = calculate_win_rate(
                wins=d.get("wins", 0),
                losses=d.get("losses", 0),
                draws=d.get("draws", 0)
            )
            results.append(d)

        return results


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "get_leaderboard",
]
