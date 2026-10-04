# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.foundation.types
Description:
    Foundation Type Contracts, Enumerations & Data Structures for Duel Subsystem.
    Defines strict TypedDict contracts, turn phase enums, and match outcome
    structs ensuring predictable, strongly-typed state transitions across matches.

Architectural Classification:
    Layer 0 (L0) - Foundation Types & Contracts
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

# =============================================================================
# BLOCK 3: BODY BLOCK (Enums & Type Contracts)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Turn Phase & Match Mode Enumerations
# -----------------------------------------------------------------------------

class TurnPhase(str, Enum):
    """Canonical Yu-Gi-Oh! turn phases under Master Rule 2020."""
    DRAW = "DRAW"
    STANDBY = "STANDBY"
    MAIN_1 = "MAIN_1"
    BATTLE = "BATTLE"
    MAIN_2 = "MAIN_2"
    END = "END"


class MatchMode(str, Enum):
    """Supported match modes for duel sessions."""
    RANKED = "RANKED"
    CASUAL = "CASUAL"
    STORY = "STORY"
    PRACTICE = "PRACTICE"


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Participant & Player State Contracts
# -----------------------------------------------------------------------------

class DuelParticipantDict(TypedDict, total=False):
    """Structured representation of a match participant."""
    user_id: int
    display_name: str
    deck_name: Optional[str]
    is_ai: bool
    avatar_url: Optional[str]


class PlayerBattleStateDict(TypedDict):
    """Live state of an individual player's board and hand."""
    user_id: int
    current_lp: int
    hand_count: int
    deck_count: int
    gy_count: int
    banished_count: int
    has_normal_summoned: bool


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Duel State Snapshots & Action Logs
# -----------------------------------------------------------------------------

class DuelActionRecord(TypedDict, total=False):
    """Audit log entry for a specific action taken during a match."""
    turn: int
    phase: str
    player_id: int
    action_type: str            # e.g. "SUMMON", "ATTACK", "DAMAGE", "DRAW", "SURRENDER"
    description: str
    lp_delta: Optional[int]


class DuelStateSnapshot(TypedDict):
    """Serializable snapshot of the full live duel state."""
    session_id: str
    match_type: str
    turn_count: int
    current_phase: str
    turn_player_id: int
    p1_id: int
    p2_id: int
    p1_lp: int
    p2_lp: int
    duel_over: bool
    winner_id: Optional[int]


class MatchResultPayload(TypedDict, total=False):
    """Standardized result dictionary emitted upon match conclusion."""
    p1_id: str
    p2_id: str
    winner_id: Optional[str]
    is_draw: bool
    match_type: str
    turns: int
    summary: str
    p1_elo_before: Optional[int]
    p1_elo_after: Optional[int]
    p1_elo_delta: Optional[int]
    p2_elo_before: Optional[int]
    p2_elo_after: Optional[int]
    p2_elo_delta: Optional[int]


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "TurnPhase",
    "MatchMode",
    "DuelParticipantDict",
    "PlayerBattleStateDict",
    "DuelActionRecord",
    "DuelStateSnapshot",
    "MatchResultPayload",
]
