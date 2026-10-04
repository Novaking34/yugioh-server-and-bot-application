# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.foundation.types
Description:
    Foundation Type Contracts & Structs for the Rating Subsystem.
    Defines TypedDict specifications for player rating profiles, match outcomes,
    leaderboard summaries, and ELO computation deltas.

Architectural Classification:
    Layer 0 (L0) - Foundation Layer
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Optional, TypedDict

# =============================================================================
# BLOCK 3: BODY BLOCK (Type Contracts)
# =============================================================================

class PlayerRatingDict(TypedDict, total=False):
    """Schema representing an active duelist's competitive profile."""
    user_id: str
    username: str
    elo: int
    wins: int
    losses: int
    draws: int
    win_streak: int
    highest_streak: int
    highest_elo: int
    tier: str
    season_id: str
    last_match_at: Optional[str]


class EloCalculationResultDict(TypedDict):
    """Schema representing calculated ELO ratings and deltas for two duelists."""
    p1_elo_before: int
    p1_elo_after: int
    p1_elo_delta: int
    p2_elo_before: int
    p2_elo_after: int
    p2_elo_delta: int


class MatchRecordDict(TypedDict, total=False):
    """Schema representing a recorded match in duel_matches."""
    match_id: int
    match_type: str
    p1_id: str
    p2_id: str
    p1_deck_name: Optional[str]
    p2_deck_name: Optional[str]
    p1_elo_before: int
    p1_elo_after: int
    p1_elo_delta: int
    p2_elo_before: int
    p2_elo_after: int
    p2_elo_delta: int
    winner_id: str
    turns: int
    summary: str


class LeaderboardEntryDict(TypedDict):
    """Schema representing an entry on the ranked leaderboard."""
    user_id: str
    username: str
    elo: int
    wins: int
    losses: int
    draws: int
    win_streak: int
    highest_elo: int
    tier: str
    win_rate: float


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "PlayerRatingDict",
    "EloCalculationResultDict",
    "MatchRecordDict",
    "LeaderboardEntryDict",
]
