# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.rating.domain
Description:
    Domain compilation unit re-exporting player profile management,
    concluded match telemetry recording, and leaderboard queries.

Architectural Classification:
    Layer 1 (L1) - Domain Layer Manifest
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .leaderboard import get_leaderboard
from .matches import ensure_duel_matches_schema, record_duel_match
from .player import get_or_create_player, reset_player_rating

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "get_or_create_player",
    "reset_player_rating",
    "record_duel_match",
    "ensure_duel_matches_schema",
    "get_leaderboard",
]
