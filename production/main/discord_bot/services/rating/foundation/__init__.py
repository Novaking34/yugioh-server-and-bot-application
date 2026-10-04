# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.rating.foundation
Description:
    Foundation compilation unit re-exporting rating invariants, constants,
    type contracts, and pure mathematical algorithms.

Architectural Classification:
    Layer 0 (L0) - Foundation Layer Manifest
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .constants import (
    DEFAULT_LEADERBOARD_LIMIT,
    DEFAULT_SEASON_ID,
    DEFAULT_STARTING_ELO,
    ESTABLISHED_K_FACTOR,
    MATCH_TYPE_CASUAL,
    MATCH_TYPE_RANKED,
    MAX_ELO_CEILING,
    MAX_LEADERBOARD_LIMIT,
    MIN_ELO_FLOOR,
    PROVISIONAL_K_FACTOR,
    PROVISIONAL_MATCHES_THRESHOLD,
    SCORE_DRAW,
    SCORE_LOSS,
    SCORE_WIN,
    TIER_BRACKETS,
)
from .math import (
    calculate_expected_score,
    calculate_win_rate,
    compute_elo_change,
    resolve_tier_info,
)
from .types import (
    EloCalculationResultDict,
    LeaderboardEntryDict,
    MatchRecordDict,
    PlayerRatingDict,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "TIER_BRACKETS",
    "DEFAULT_STARTING_ELO",
    "MIN_ELO_FLOOR",
    "MAX_ELO_CEILING",
    "PROVISIONAL_MATCHES_THRESHOLD",
    "PROVISIONAL_K_FACTOR",
    "ESTABLISHED_K_FACTOR",
    "SCORE_WIN",
    "SCORE_DRAW",
    "SCORE_LOSS",
    "DEFAULT_SEASON_ID",
    "DEFAULT_LEADERBOARD_LIMIT",
    "MAX_LEADERBOARD_LIMIT",
    "MATCH_TYPE_RANKED",
    "MATCH_TYPE_CASUAL",
    "resolve_tier_info",
    "calculate_expected_score",
    "compute_elo_change",
    "calculate_win_rate",
    "PlayerRatingDict",
    "EloCalculationResultDict",
    "MatchRecordDict",
    "LeaderboardEntryDict",
]
