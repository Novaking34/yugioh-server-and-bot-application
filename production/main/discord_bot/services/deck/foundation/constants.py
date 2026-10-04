# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.foundation.constants
Description:
    Bottom-Up Foundation: Master Rule limits, hand size thresholds,
    official game state zones, banlist mappings, and legacy Set 1 constants.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Optional, Set, Dict

# =============================================================================
# BLOCK 3: BODY BLOCK (Constants & Boundary Primitives)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Official Master Rule Construction Limits
# -----------------------------------------------------------------------------
STANDARD_MIN_MAIN_DECK: int = 40       # Official tournament minimum Main Deck cards
STANDARD_MAX_MAIN_DECK: int = 60       # Official tournament maximum Main Deck cards
STANDARD_MAX_EXTRA_DECK: int = 15      # Official tournament maximum Extra Deck cards
STANDARD_MAX_SIDE_DECK: int = 15       # Official tournament maximum Side Deck cards
MAX_COPIES_PER_CARD: int = 3           # Official maximum copies of any card by name
MAX_USER_DECK_SLOTS: int = 20          # Maximum saved named deck slots per user

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Hand Size Limits & Turn Turnstile Constants
# -----------------------------------------------------------------------------
MIN_HAND_SIZE: int = 0                 # Hand minimum (player has 0 cards in hand)
DEFAULT_END_PHASE_HAND_LIMIT: int = 6  # Standard Master Rule End Phase discard threshold
HIEROGLYPH_HAND_LIMIT: int = 7         # Card-modified limit (e.g., Hieroglyph Lithograph)
NO_HAND_LIMIT: Optional[int] = None    # Card-modified limit (e.g., Infinite Cards - no hand limit)
MAX_HAND_SIZE: int = 7                 # Standard modified ceiling (retained for backward compatibility)
DEFAULT_OPENING_HAND_P1: int = 5       # Turn 1 (Going First: 5 cards, no draw phase)
DEFAULT_OPENING_HAND_P2: int = 6       # Turn 2 (Going Second: 5 + 1 draw phase card)

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Official Yu-Gi-Oh! Game State Zones
# -----------------------------------------------------------------------------
ZONE_MAIN_DECK: str = "MAIN_DECK"                     # Main Deck (Face-down draw pile)
ZONE_EXTRA_DECK: str = "EXTRA_DECK"                   # Extra Deck (Face-down, or face-up Pendulums)
ZONE_HAND: str = "HAND"                               # In-hand cards (Private knowledge)
ZONE_FIELD_SPELL: str = "FIELD_SPELL"                 # Field Zone (Dedicated Field Spell slot)
ZONE_GRAVEYARD: str = "GRAVEYARD"                     # Graveyard / GY (Public resource pile)
ZONE_BANISHMENT: str = "BANISHMENT"                   # Banished Pile (Face-up or Face-down)
ZONE_EXTRA_MONSTER: str = "EXTRA_MONSTER_ZONE"         # Extra Monster Zone (EMZ, Left / Right)
ZONE_PENDULUM: str = "PENDULUM_ZONE"                  # Pendulum Zone (PZ, Left / Right scales)
ZONE_MAIN_MONSTER: str = "MAIN_MONSTER_ZONE"           # Main Monster Zones 1-5
ZONE_SPELL_TRAP: str = "SPELL_TRAP_ZONE"               # Spell & Trap Zones 1-5

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Official Banlist Limits Mapping
# -----------------------------------------------------------------------------
BANLIST_LIMITS: Dict[str, int] = {
    "Forbidden": 0,
    "Limited": 1,
    "Semi-Limited": 2,
    "Unlimited": 3,
}

# -----------------------------------------------------------------------------
# Sub-Block 3.5: Backward-Compatibility Aliases
# -----------------------------------------------------------------------------
SET_1_CARD_COUNT: int = 64             # Total canonical cards in Set 1: The Land of Kustomazi
SET_1_MAIN_DECK_EXPECTED: int = 34     # Legacy Kasutamaiza Creation Control main count
SET_1_EXTRA_DECK_EXPECTED: int = 6     # Legacy Kasutamaiza Creation Control extra count
SET_1_EXTRA_DECK_IDS: Set[int] = {50000106, 50000107}


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

