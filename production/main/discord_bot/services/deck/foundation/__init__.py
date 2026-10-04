# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.deck.foundation
Description:
    Bottom-Up Foundation: Core domain constants, TypedDict data contracts,
    card classification logic, and hypergeometric mathematical primitives.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# =============================================================================
# BLOCK 3: BODY BLOCK (Foundation Primitive Re-Exports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Constants & Boundary Primitives
# -----------------------------------------------------------------------------
from .constants import (
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
    SET_1_CARD_COUNT,
    SET_1_MAIN_DECK_EXPECTED,
    SET_1_EXTRA_DECK_EXPECTED,
    SET_1_EXTRA_DECK_IDS,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Type Contracts
# -----------------------------------------------------------------------------
from .types import (
    CardDict,
    DeckPartition,
    ParsedYDK,
    SavedDeckSlot,
    StoryDeckRecord,
    DeckAnalysisResult,
    LegalityResult,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Card Classifiers & Zone Awareness
# -----------------------------------------------------------------------------
from .classifier import (
    is_extra_deck_card_id,
    partition_card_ids,
    is_extra_deck_card,
    is_extra_deck_pendulum,
    is_main_deck_pendulum,
    get_pendulum_scales,
    is_ritual_monster,
    is_tribute_monster,
    get_tribute_cost,
    is_field_spell,
    has_field_awareness,
    has_graveyard_interaction,
    has_banishment_interaction,
    has_extra_monster_zone_interaction,
    has_pendulum_zone_interaction,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Probability, Shuffle & Hand Math
# -----------------------------------------------------------------------------
from .math import (
    is_deckout_condition,
    validate_hand_size,
    check_end_phase_discard_requirement,
    calculate_draw_prob,
    calculate_opening_hand_prob,
    calculate_combo_prob,
    fair_shuffle,
    simulate_fair_draw,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================
__all__ = [
    # Constants
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
    # Types
    "CardDict",
    "DeckPartition",
    "ParsedYDK",
    "SavedDeckSlot",
    "StoryDeckRecord",
    "DeckAnalysisResult",
    "LegalityResult",
    # Classifier
    "is_extra_deck_card_id",
    "partition_card_ids",
    "is_extra_deck_card",
    "is_extra_deck_pendulum",
    "is_main_deck_pendulum",
    "get_pendulum_scales",
    "is_ritual_monster",
    "is_tribute_monster",
    "get_tribute_cost",
    "is_field_spell",
    "has_field_awareness",
    "has_graveyard_interaction",
    "has_banishment_interaction",
    "has_extra_monster_zone_interaction",
    "has_pendulum_zone_interaction",
    # Math
    "is_deckout_condition",
    "validate_hand_size",
    "check_end_phase_discard_requirement",
    "calculate_draw_prob",
    "calculate_opening_hand_prob",
    "calculate_combo_prob",
    "fair_shuffle",
    "simulate_fair_draw",
]
