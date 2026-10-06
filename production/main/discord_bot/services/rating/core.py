# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.core
Description:
    Central Rating Service Engine & Competitive ELO Orchestrator.
    Coordinates duelist profiles, FIDE Elo calculations, division progression,
    micro/macro card and deck telemetry recording, and seasonal leaderboards.

Architectural Classification:
    Layer 1 (L1) - Core Service Orchestrator
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional, Tuple

from bot_config import BOT_CONFIG
from production.main.logger import get_logger
from .foundation.constants import (
    DEFAULT_LEADERBOARD_LIMIT,
    DEFAULT_SEASON_ID,
    DEFAULT_STARTING_ELO,
    MATCH_TYPE_RANKED,
    TIER_BRACKETS,
)
from .foundation.math import compute_elo_change as _compute_elo_change
from .foundation.math import resolve_tier_info as _resolve_tier_info
from .foundation.types import (
    LeaderboardEntryDict,
    MatchRecordDict,
    PlayerRatingDict,
)
from .domain.leaderboard import get_leaderboard as _get_leaderboard
from .domain.matches import record_duel_match as _record_duel_match
from .domain.player import get_or_create_player as _get_or_create_player
from .domain.player import reset_player_rating as _reset_player_rating

logger = get_logger("discord_bot.services.rating.core")

# =============================================================================
# BLOCK 3: BODY BLOCK (Core Rating Service Engine)
# =============================================================================

class RatingService:
    """
    Central orchestrator service handling competitive Elo ratings, tier classification,
    win-streak tracking, and duel match recording.
    """

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Constructor & Database Binding
    # -------------------------------------------------------------------------
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path: str = db_path or BOT_CONFIG.get("telemetry_db_path") or BOT_CONFIG["db_path"]

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Static ELO & Tier Utilities (Public API Compatibility)
    # -------------------------------------------------------------------------
    @staticmethod
    def get_tier_info(elo: int) -> Tuple[str, str, int]:
        """
        Returns (tier_name, badge_icon, embed_color) for a given Elo rating.

        Args:
            elo: Numerical duelist rating.

        Returns:
            Tuple containing tier name, emoji icon badge, and hexadecimal color.
        """
        return _resolve_tier_info(elo)

    @staticmethod
    def compute_elo_change(
        p1_elo: int,
        p2_elo: int,
        p1_score: float,
        p1_matches: int = 15,
        p2_matches: int = 15
    ) -> Tuple[int, int]:
        """
        Calculates new Elo ratings using standard logistic Elo formula.

        Args:
            p1_elo: Current rating of Player 1.
            p2_elo: Current rating of Player 2.
            p1_score: Match score for P1 (1.0 = win, 0.5 = draw, 0.0 = loss).
            p1_matches: Matches played by P1.
            p2_matches: Matches played by P2.

        Returns:
            Tuple of (new_p1_elo, new_p2_elo).
        """
        return _compute_elo_change(p1_elo, p2_elo, p1_score, p1_matches, p2_matches)

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Player Profile Management
    # -------------------------------------------------------------------------
    async def get_or_create_player(
        self,
        user_id: str,
        username: Optional[str] = None,
        season_id: str = DEFAULT_SEASON_ID
    ) -> PlayerRatingDict:
        """
        Retrieves an existing duelist's rating profile or initializes a fresh record
        with baseline 1200 Elo.
        """
        return await _get_or_create_player(
            db_path=self.db_path,
            user_id=str(user_id),
            username=username,
            season_id=season_id
        )

    async def reset_player_rating(
        self,
        user_id: str,
        target_elo: int = DEFAULT_STARTING_ELO,
        season_id: str = DEFAULT_SEASON_ID
    ) -> bool:
        """Resets a duelist's Elo and streaks to starting baselines."""
        return await _reset_player_rating(
            db_path=self.db_path,
            user_id=str(user_id),
            target_elo=target_elo,
            season_id=season_id
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Match History & Telemetry Recording
    # -------------------------------------------------------------------------
    async def record_duel_match(
        self,
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
        Processes a concluded match:
        - Updates Elo and stats for both players if RANKED.
        - Updates win/loss telemetry in card_usage_stats (micro) and player_saved_decks (macro).
        - Records match in duel_matches.
        """
        return await _record_duel_match(
            db_path=self.db_path,
            p1_id=str(p1_id),
            p2_id=str(p2_id),
            winner_id=winner_id,
            match_type=match_type,
            turns=turns,
            summary=summary,
            p1_deck=p1_deck,
            p2_deck=p2_deck,
            p1_name=p1_name,
            p2_name=p2_name,
            p1_deck_name=p1_deck_name,
            p2_deck_name=p2_deck_name,
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.5: Competitive Leaderboards
    # -------------------------------------------------------------------------
    async def get_leaderboard(
        self,
        limit: int = DEFAULT_LEADERBOARD_LIMIT,
        season_id: str = DEFAULT_SEASON_ID
    ) -> List[LeaderboardEntryDict]:
        """Returns the top duelists ordered by ELO and victory count."""
        return await _get_leaderboard(
            db_path=self.db_path,
            limit=limit,
            season_id=season_id
        )


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "RatingService",
    "TIER_BRACKETS",
]
