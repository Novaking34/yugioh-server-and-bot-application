# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.foundation.constants
Description:
    Foundation Constants & Master Rule Invariants for the Duel Subsystem.
    Defines starting Life Points, opening hand sizes, turn phases, match modes,
    timeout limits, and zone identifiers for live Yu-Gi-Oh! match execution.

Architectural Classification:
    Layer 0 (L0) - Foundation Constants
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Final, List, Tuple

# =============================================================================
# BLOCK 3: BODY BLOCK (Constants & Invariants)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Life Point Standards & Hand Size Limits
# -----------------------------------------------------------------------------
DEFAULT_STARTING_LP: Final[int] = 8000
SPEED_DUEL_STARTING_LP: Final[int] = 4000
MIN_LIFE_POINTS: Final[int] = 0
MAX_LIFE_POINTS: Final[int] = 999999

DEFAULT_OPENING_HAND_SIZE: Final[int] = 5
MAX_HAND_SIZE_DEFAULT: Final[int] = 6
MIN_DECK_SIZE_REQUIRED: Final[int] = 40

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Turn Phase Identifiers (Master Rule 2020)
# -----------------------------------------------------------------------------
PHASE_DRAW: Final[str] = "DRAW"
PHASE_STANDBY: Final[str] = "STANDBY"
PHASE_MAIN_1: Final[str] = "MAIN_1"
PHASE_BATTLE: Final[str] = "BATTLE"
PHASE_MAIN_2: Final[str] = "MAIN_2"
PHASE_END: Final[str] = "END"

ALL_TURN_PHASES: Final[Tuple[str, ...]] = (
    PHASE_DRAW,
    PHASE_STANDBY,
    PHASE_MAIN_1,
    PHASE_BATTLE,
    PHASE_MAIN_2,
    PHASE_END,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Match Mode Classifications
# -----------------------------------------------------------------------------
MATCH_TYPE_RANKED: Final[str] = "RANKED"
MATCH_TYPE_CASUAL: Final[str] = "CASUAL"
MATCH_TYPE_STORY: Final[str] = "STORY"
MATCH_TYPE_PRACTICE: Final[str] = "PRACTICE"

ALL_MATCH_TYPES: Final[Tuple[str, ...]] = (
    MATCH_TYPE_RANKED,
    MATCH_TYPE_CASUAL,
    MATCH_TYPE_STORY,
    MATCH_TYPE_PRACTICE,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Field Zone Constraints & Limits
# -----------------------------------------------------------------------------
MMZ_SLOT_COUNT: Final[int] = 5
STZ_SLOT_COUNT: Final[int] = 5
EMZ_SLOT_COUNT: Final[int] = 2
FIELD_SPELL_SLOT_COUNT: Final[int] = 1

ZONE_MAIN_MONSTER: Final[str] = "main_monster"
ZONE_SPELL_TRAP: Final[str] = "spell_trap"
ZONE_FIELD_SPELL: Final[str] = "field_spell"
ZONE_EXTRA_MONSTER: Final[str] = "extra_monster"
ZONE_GRAVEYARD: Final[str] = "graveyard"
ZONE_BANISHMENT: Final[str] = "banishment"
ZONE_HAND: Final[str] = "hand"
ZONE_MAIN_DECK: Final[str] = "main_deck"
ZONE_EXTRA_DECK: Final[str] = "extra_deck"

# -----------------------------------------------------------------------------
# Sub-Block 3.5: Timeouts & Operational Invariants
# -----------------------------------------------------------------------------
DEFAULT_DUEL_TIMEOUT_SECONDS: Final[int] = 600      # 10 minutes max idle
TURN_ACTION_TIMEOUT_SECONDS: Final[int] = 180       # 3 minutes per turn action
INTERACTION_DEBOUNCE_SECONDS: Final[float] = 0.5


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Life Points & Hands
    "DEFAULT_STARTING_LP",
    "SPEED_DUEL_STARTING_LP",
    "MIN_LIFE_POINTS",
    "MAX_LIFE_POINTS",
    "DEFAULT_OPENING_HAND_SIZE",
    "MAX_HAND_SIZE_DEFAULT",
    "MIN_DECK_SIZE_REQUIRED",
    # Turn Phases
    "PHASE_DRAW",
    "PHASE_STANDBY",
    "PHASE_MAIN_1",
    "PHASE_BATTLE",
    "PHASE_MAIN_2",
    "PHASE_END",
    "ALL_TURN_PHASES",
    # Match Types
    "MATCH_TYPE_RANKED",
    "MATCH_TYPE_CASUAL",
    "MATCH_TYPE_STORY",
    "MATCH_TYPE_PRACTICE",
    "ALL_MATCH_TYPES",
    # Zones
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
    # Timeouts
    "DEFAULT_DUEL_TIMEOUT_SECONDS",
    "TURN_ACTION_TIMEOUT_SECONDS",
    "INTERACTION_DEBOUNCE_SECONDS",
]
