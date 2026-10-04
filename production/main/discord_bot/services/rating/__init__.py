# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.rating
Description:
    Modular Competitive Rating & ELO Management Subsystem for Yu-Gi-Oh! Discord Bot.
    Organized with Top-Down / Bottom-Up C-style compilation unit architecture:
    - foundation/: Bottom-Up Foundation (Constants, Struct Types, Math Algorithms)
    - domain/    : Domain Engines (Player Profiles, Match Recording, Leaderboards)
    - core.py    : Top-Down Orchestrator Facade Engine (RatingService)

Architectural Classification:
    Layer 1 (L1) - Domain Subsystem Package
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Foundation Primitives (foundation/)
# -----------------------------------------------------------------------------
from .foundation.constants import (
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

from .foundation.types import (
    EloCalculationResultDict,
    LeaderboardEntryDict,
    MatchRecordDict,
    PlayerRatingDict,
)

from .foundation.math import (
    calculate_expected_score,
    calculate_win_rate,
    compute_elo_change,
    resolve_tier_info,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Domain Operations (domain/)
# -----------------------------------------------------------------------------
from .domain.leaderboard import get_leaderboard
from .domain.matches import ensure_duel_matches_schema, record_duel_match
from .domain.player import get_or_create_player, reset_player_rating

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Core Orchestrator (core.py)
# -----------------------------------------------------------------------------
from .core import RatingService

# Global Singleton
rating_service = RatingService()


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Core Orchestrator & Singleton
    "RatingService",
    "rating_service",
    # Constants
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
    # Mathematical Primitives
    "resolve_tier_info",
    "calculate_expected_score",
    "compute_elo_change",
    "calculate_win_rate",
    # Types
    "PlayerRatingDict",
    "EloCalculationResultDict",
    "MatchRecordDict",
    "LeaderboardEntryDict",
    # Domain Handlers
    "get_or_create_player",
    "reset_player_rating",
    "record_duel_match",
    "ensure_duel_matches_schema",
    "get_leaderboard",
]
