# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel
Description:
    Root Duel Service Entry Point & Translation Bridge.
    Re-exports the central DuelService engine, foundation primitives,
    domain state machines, and concurrency managers from the modular
    subsystem at `services.duel`.

Architectural Classification:
    Layer 1 (L1) - Domain Service Root Bridge
    Subsystem: Duel Management & State Isolation
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Layered Package Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Core Orchestrator Unit
# -----------------------------------------------------------------------------
from .duel.core import DuelService

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Foundation Constants & Master Rule Invariants
# -----------------------------------------------------------------------------
from .duel.foundation.constants import (
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
)

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Foundation Type Contracts & Structs
# -----------------------------------------------------------------------------
from .duel.foundation.types import (
    TurnPhase,
    MatchMode,
    DuelParticipantDict,
    PlayerBattleStateDict,
    DuelActionRecord,
    DuelStateSnapshot,
    MatchResultPayload,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.4: Domain Registry & Session State Machine
# -----------------------------------------------------------------------------
from .duel.domain.manager import DuelManager
from .duel.domain.session import DuelSession

# -----------------------------------------------------------------------------
# Sub-Block 2.5: Global Subsystem Singletons
# -----------------------------------------------------------------------------
from .duel import duel_service, duel_manager


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DuelService",
    "duel_service",
    "DuelManager",
    "duel_manager",
    "DuelSession",
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
    "TurnPhase",
    "MatchMode",
    "DuelParticipantDict",
    "PlayerBattleStateDict",
    "DuelActionRecord",
    "DuelStateSnapshot",
    "MatchResultPayload",
]
