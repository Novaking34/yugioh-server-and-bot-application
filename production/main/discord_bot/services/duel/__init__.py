# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel
Description:
    Live Yu-Gi-Oh! Duel Management, Matchmaking & Session Engine Package.
    Exposes the central DuelService orchestrator, DuelManager concurrency guard,
    DuelSession state machine, Master Rule constants, and TypedDict contracts.

Architectural Classification:
    Layer 1 (L1) - Domain Service Package
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Core Service Orchestrator
# -----------------------------------------------------------------------------
from .core import DuelService

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Domain Components
# -----------------------------------------------------------------------------
from .domain.manager import DuelManager
from .domain.session import DuelSession

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Foundation Constants
# -----------------------------------------------------------------------------
from .foundation.constants import (
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

# -----------------------------------------------------------------------------
# Sub-Block 2.4: Foundation Type Contracts
# -----------------------------------------------------------------------------
from .foundation.types import (
    TurnPhase,
    MatchMode,
    DuelParticipantDict,
    PlayerBattleStateDict,
    DuelActionRecord,
    DuelStateSnapshot,
    MatchResultPayload,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Singleton Instantiation)
# =============================================================================

# Global singleton instance for shared Cog and Engine access
duel_manager = DuelManager()
duel_service = DuelService(manager=duel_manager)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Core Orchestrator & Singletons
    "DuelService",
    "duel_service",
    "DuelManager",
    "duel_manager",
    "DuelSession",
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
