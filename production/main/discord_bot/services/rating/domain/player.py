# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.domain.player
Description:
    Domain Operations for Duelist Rating Profile Lifecycle.
    Handles retrieving, initializing, updating, and resetting competitive player
    profiles in SQLite (`player_ratings`).

Architectural Classification:
    Layer 1 (L1) - Domain Layer
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, Optional
import aiosqlite

from production.main.logger import get_logger
from ..foundation.constants import DEFAULT_SEASON_ID, DEFAULT_STARTING_ELO
from ..foundation.math import resolve_tier_info
from ..foundation.types import PlayerRatingDict

logger = get_logger("discord_bot.services.rating.domain.player")

# =============================================================================
# BLOCK 3: BODY BLOCK (Player Rating Domain Operations)
# =============================================================================

async def get_or_create_player(
    db_path: str,
    user_id: str,
    username: Optional[str] = None,
    season_id: str = DEFAULT_SEASON_ID
) -> PlayerRatingDict:
    """
    Retrieves an existing duelist's rating profile or initializes a fresh record
    with baseline 1200 Elo.

    Args:
        db_path: Absolute SQLite database path.
        user_id: Discord snowflake user ID as a string.
        username: Optional updated duelist display name.
        season_id: Season identifier (default: "Season 1").

    Returns:
        PlayerRatingDict dictionary containing the duelist's current profile.
    """
    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM player_ratings WHERE user_id = ?",
            (user_id_str,)
        )
        row = await cur.fetchone()
        if row:
            data = dict(row)
            if username and data.get("username") != username:
                await db.execute(
                    "UPDATE player_ratings SET username = ? WHERE user_id = ?",
                    (username, user_id_str)
                )
                await db.commit()
                data["username"] = username
            return data

        # Initialize new duelist profile with baseline rating
        default_elo = DEFAULT_STARTING_ELO
        tier_name, _, _ = resolve_tier_info(default_elo)
        display_name = username or f"Duelist_{user_id_str[:6]}"

        await db.execute("""
            INSERT INTO player_ratings (
                user_id, username, elo, wins, losses, draws, win_streak, highest_streak, highest_elo, tier, season_id
            ) VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?, ?, ?)
        """, (user_id_str, display_name, default_elo, default_elo, tier_name, season_id))
        await db.commit()

        logger.info(f"Initialized new player rating profile for {display_name} ({user_id_str}) at {default_elo} Elo.")
        return {
            "user_id": user_id_str,
            "username": display_name,
            "elo": default_elo,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_streak": 0,
            "highest_streak": 0,
            "highest_elo": default_elo,
            "tier": tier_name,
            "season_id": season_id,
        }


async def reset_player_rating(
    db_path: str,
    user_id: str,
    target_elo: int = DEFAULT_STARTING_ELO,
    season_id: str = DEFAULT_SEASON_ID
) -> bool:
    """
    Resets a duelist's Elo and streaks to starting baselines (administrative rescue tool).

    Args:
        db_path: Absolute SQLite database path.
        user_id: Discord snowflake user ID.
        target_elo: Starting Elo baseline (default: 1200).
        season_id: Current active season.

    Returns:
        True if the profile was found and updated, False otherwise.
    """
    tier_name, _, _ = resolve_tier_info(target_elo)
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            UPDATE player_ratings SET
                elo = ?,
                win_streak = 0,
                tier = ?,
                season_id = ?
            WHERE user_id = ?
        """, (target_elo, tier_name, season_id, str(user_id)))
        await db.commit()
        return cur.rowcount > 0


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "get_or_create_player",
    "reset_player_rating",
]
