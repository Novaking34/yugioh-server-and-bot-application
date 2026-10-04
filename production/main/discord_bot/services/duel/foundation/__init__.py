# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.foundation
Description:
    Foundation Package Initialization for the Duel Subsystem.
    Re-exports all core constants, turn phase identifiers, zone boundaries,
    and type contracts.

Architectural Classification:
    Layer 0 (L0) - Foundation Layer
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .constants import (
    DEFAULT_STARTING_LP,
    SPEED_DUEL_STARTING_LP,
    MIN_LIFE_POINTS,
    MAX_LIFE_POINTS,
    DEFAULT_OPENING_HAND_SIZE,
    MAX_HAND_SIZE_DEFAULT,
    MIN_DECK_SIZE_REQUIRED,
    PHASE_DRAW,
    PHASE_STANDBY,
    PHASE_MAIN_1,
    PHASE_BATTLE,
    PHASE_MAIN_2,
    PHASE_END,
    ALL_TURN_PHASES,
    MATCH_TYPE_RANKED,
    MATCH_TYPE_CASUAL,
    MATCH_TYPE_STORY,
    MATCH_TYPE_PRACTICE,
    ALL_MATCH_TYPES,
    MMZ_SLOT_COUNT,
    STZ_SLOT_COUNT,
    EMZ_SLOT_COUNT,
    FIELD_SPELL_SLOT_COUNT,
    ZONE_MAIN_MONSTER,
    ZONE_SPELL_TRAP,
    ZONE_FIELD_SPELL,
    ZONE_EXTRA_MONSTER,
    ZONE_GRAVEYARD,
    ZONE_BANISHMENT,
    ZONE_HAND,
    ZONE_MAIN_DECK,
    ZONE_EXTRA_DECK,
    DEFAULT_DUEL_TIMEOUT_SECONDS,
    TURN_ACTION_TIMEOUT_SECONDS,
    INTERACTION_DEBOUNCE_SECONDS,
)

from .types import (
    TurnPhase,
    MatchMode,
    DuelParticipantDict,
    PlayerBattleStateDict,
    DuelActionRecord,
    DuelStateSnapshot,
    MatchResultPayload,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Constants
    "DEFAULT_STARTING_LP",
    "SPEED_DUEL_STARTING_LP",
    "MIN_LIFE_POINTS",
    "MAX_LIFE_POINTS",
    "DEFAULT_OPENING_HAND_SIZE",
    "MAX_HAND_SIZE_DEFAULT",
    "MIN_DECK_SIZE_REQUIRED",
    "PHASE_DRAW",
    "PHASE_STANDBY",
    "PHASE_MAIN_1",
    "PHASE_BATTLE",
    "PHASE_MAIN_2",
    "PHASE_END",
    "ALL_TURN_PHASES",
    "MATCH_TYPE_RANKED",
    "MATCH_TYPE_CASUAL",
    "MATCH_TYPE_STORY",
    "MATCH_TYPE_PRACTICE",
    "ALL_MATCH_TYPES",
    "MMZ_SLOT_COUNT",
    "STZ_SLOT_COUNT",
    "EMZ_SLOT_COUNT",
    "FIELD_SPELL_SLOT_COUNT",
    "ZONE_MAIN_MONSTER",
    "ZONE_SPELL_TRAP",
    "ZONE_FIELD_SPELL",
    "ZONE_EXTRA_MONSTER",
    "ZONE_GRAVEYARD",
    "ZONE_BANISHMENT",
    "ZONE_HAND",
    "ZONE_MAIN_DECK",
    "ZONE_EXTRA_DECK",
    "DEFAULT_DUEL_TIMEOUT_SECONDS",
    "TURN_ACTION_TIMEOUT_SECONDS",
    "INTERACTION_DEBOUNCE_SECONDS",
    # Types
    "TurnPhase",
    "MatchMode",
    "DuelParticipantDict",
    "PlayerBattleStateDict",
    "DuelActionRecord",
    "DuelStateSnapshot",
    "MatchResultPayload",
]
