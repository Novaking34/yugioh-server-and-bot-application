# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.foundation.constants
Description:
    Bottom-Up Foundation: Master Rule limits, hand size thresholds,
    official game state zones, banlist mappings, and legacy Set 1 constants.
    Re-exports canonical game rules from `config.game_rules`.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Optional, Set, Dict

from config.game_rules import (
    STANDARD_MIN_MAIN_DECK,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
    STANDARD_MAX_SIDE_DECK,
    MAX_COPIES_PER_CARD,
    MAX_USER_DECK_SLOTS,
    MIN_HAND_SIZE,
    DEFAULT_END_PHASE_HAND_LIMIT,
    HIEROGLYPH_HAND_LIMIT,
    NO_HAND_LIMIT,
    MAX_HAND_SIZE,
    DEFAULT_OPENING_HAND_P1,
    DEFAULT_OPENING_HAND_P2,
    ZONE_MAIN_DECK,
    ZONE_EXTRA_DECK,
    ZONE_HAND,
    ZONE_FIELD_SPELL,
    ZONE_GRAVEYARD,
    ZONE_BANISHMENT,
    ZONE_EXTRA_MONSTER,
    ZONE_PENDULUM,
    ZONE_MAIN_MONSTER,
    ZONE_SPELL_TRAP,
    BANLIST_LIMITS,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Constants & Boundary Primitives)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Set 1 Specific Game Constants
# -----------------------------------------------------------------------------
SET_1_CARD_COUNT: int = 64             # Total canonical cards in Set 1: The Land of Kustomazi
SET_1_MAIN_DECK_EXPECTED: int = 34     # Legacy Kasutamaiza Creation Control main count
SET_1_EXTRA_DECK_EXPECTED: int = 6     # Legacy Kasutamaiza Creation Control extra count
SET_1_EXTRA_DECK_IDS: Set[int] = {
    50000106, 50000107,  # Kasutamaiza Fusions (Mohousha, The Great Kasutamaiza)
    50000151, 50000152, 50000153, 50000154, 50000155, 50000156, 50000157, 50000158, 50000159,  # LeSpookie Synchros
    50000160, 50000161, 50000162, 50000163, 50000164,  # LeSpookie Links
}

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "STANDARD_MIN_MAIN_DECK",
    "STANDARD_MAX_MAIN_DECK",
    "STANDARD_MAX_EXTRA_DECK",
    "STANDARD_MAX_SIDE_DECK",
    "MAX_COPIES_PER_CARD",
    "MAX_USER_DECK_SLOTS",
    "MIN_HAND_SIZE",
    "DEFAULT_END_PHASE_HAND_LIMIT",
    "HIEROGLYPH_HAND_LIMIT",
    "NO_HAND_LIMIT",
    "MAX_HAND_SIZE",
    "DEFAULT_OPENING_HAND_P1",
    "DEFAULT_OPENING_HAND_P2",
    "ZONE_MAIN_DECK",
    "ZONE_EXTRA_DECK",
    "ZONE_HAND",
    "ZONE_FIELD_SPELL",
    "ZONE_GRAVEYARD",
    "ZONE_BANISHMENT",
    "ZONE_EXTRA_MONSTER",
    "ZONE_PENDULUM",
    "ZONE_MAIN_MONSTER",
    "ZONE_SPELL_TRAP",
    "BANLIST_LIMITS",
    "SET_1_CARD_COUNT",
    "SET_1_MAIN_DECK_EXPECTED",
    "SET_1_EXTRA_DECK_EXPECTED",
    "SET_1_EXTRA_DECK_IDS",
]
