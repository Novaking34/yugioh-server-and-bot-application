# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.foundation.constants
Description:
    Foundation Constants & FIDE ELO Rating Configuration.
    Defines tier brackets, baseline ratings, K-factor weightings, season identifiers,
    and leaderboard constraints for competitive Yu-Gi-Oh! match tracking.

Architectural Classification:
    Layer 0 (L0) - Foundation Layer
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import List, Tuple

# =============================================================================
# BLOCK 3: BODY BLOCK (Constants & Invariants)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Competitive Tier Brackets (Min ELO, Name, Badge, Color)
# -----------------------------------------------------------------------------
TIER_BRACKETS: List[Tuple[int, str, str, int]] = [
    (2100, "King of Games", "👑", 0xFFD700),
    (1900, "Diamond Duelist", "💠", 0x00E5FF),
    (1700, "Platinum Duelist", "💎", 0x00E676),
    (1500, "Gold Duelist", "🥇", 0xF59E0B),
    (1300, "Silver Duelist", "🥈", 0x94A3B8),
    (1100, "Bronze Duelist", "🥉", 0xCD7F32),
    (0,    "Novice Duelist", "🔰", 0x6B7280),
]

# -----------------------------------------------------------------------------
# Sub-Block 3.2: ELO Rating Invariants & Algorithm Configuration
# -----------------------------------------------------------------------------
DEFAULT_STARTING_ELO: int = 1200
MIN_ELO_FLOOR: int = 100
MAX_ELO_CEILING: int = 4000

# K-Factor Weights (FIDE Standards)
PROVISIONAL_MATCHES_THRESHOLD: int = 10
PROVISIONAL_K_FACTOR: int = 40
ESTABLISHED_K_FACTOR: int = 32

# Match Scoring Constants
SCORE_WIN: float = 1.0
SCORE_DRAW: float = 0.5
SCORE_LOSS: float = 0.0

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Seasons & Leaderboard Limits
# -----------------------------------------------------------------------------
DEFAULT_SEASON_ID: str = "Season 1"
DEFAULT_LEADERBOARD_LIMIT: int = 10
MAX_LEADERBOARD_LIMIT: int = 100

# Match Types Permitted in ELO Calculations
MATCH_TYPE_RANKED: str = "RANKED"
MATCH_TYPE_CASUAL: str = "CASUAL"


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
]
