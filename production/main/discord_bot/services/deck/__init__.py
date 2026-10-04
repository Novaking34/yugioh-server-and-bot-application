# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.deck
Description:
    Modular Deck Management Subsystem for Yu-Gi-Oh! Discord Bot & Story Server.
    Organized with Top-Down / Bottom-Up architecture:
    - foundation/: Bottom-Up Foundation (Constants, Types, Classifiers, Math)
    - domain/    : Domain Engines (Cardpool, Storage, Slots, Story, YDK)
    - visual/    : Presentation & Tactical Analysis (Canvas, Analytics)
    - core.py    : Top-Down Orchestrator Engine (DeckService)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# =============================================================================
# BLOCK 3: BODY BLOCK (Package Re-Exports & Core Orchestrator Inclusion)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Foundation & Primitives (foundation/)
# -----------------------------------------------------------------------------
from .foundation.constants import (
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

from .foundation.types import (
    CardDict,
    DeckPartition,
    ParsedYDK,
    SavedDeckSlot,
    StoryDeckRecord,
    DeckAnalysisResult,
    LegalityResult,
)

from .foundation.classifier import (
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

from .foundation.math import (
    is_deckout_condition,
    validate_hand_size,
    check_end_phase_discard_requirement,
    calculate_draw_prob,
    calculate_opening_hand_prob,
    calculate_combo_prob,
    fair_shuffle,
    simulate_fair_draw,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Domain Engines (domain/)
# -----------------------------------------------------------------------------
from .domain.cardpool import (
    query_cardpool_cards,
    calculate_cardpool_stats,
    format_cardpool_summary,
)

from .domain.storage import (
    fetch_player_deck,
    fetch_player_card_ids,
    fetch_player_duel_decks,
    partition_player_deck,
    add_card_to_player_deck,
    remove_card_from_player_deck,
    clear_player_deck,
)

from .domain.slots import (
    ensure_saved_deck_tables,
    save_named_deck_slot,
    load_named_deck_slot,
    list_user_deck_slots,
    get_saved_deck_slot,
    rename_saved_deck_slot,
    delete_saved_deck_slot,
    record_deck_slot_match,
    find_matching_saved_deck,
)

from .domain.story import (
    fetch_character_decks,
    fetch_character_deck_by_id,
    copy_character_deck_to_player_deck,
    match_ai_deck_for_elo,
    format_character_deck_summary,
)

from .domain.ydk import (
    parse_ydk,
    export_to_ydk,
    validate_ydk_passcodes,
    save_ydk_file,
    load_ydk_file,
    import_ydk_to_player_deck,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Visual & Tactical Presentation (visual/)
# -----------------------------------------------------------------------------
from .visual.canvas import (
    render_deck_canvas,
    render_player_deck_canvas,
    render_character_deck_canvas,
)

from .visual.analytics import (
    analyze_deck_structure,
    validate_deck_legality,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Core Orchestrator (core.py)
# -----------------------------------------------------------------------------
from .core import DeckService

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================
__all__ = [
    # Core Orchestrator Unit
    "DeckService",
    # Core Constants
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
    # Core Types
    "CardDict",
    "DeckPartition",
    "ParsedYDK",
    "SavedDeckSlot",
    "StoryDeckRecord",
    "DeckAnalysisResult",
    "LegalityResult",
    # Core Classifier
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
    # Core Math
    "is_deckout_condition",
    "validate_hand_size",
    "check_end_phase_discard_requirement",
    "calculate_draw_prob",
    "calculate_opening_hand_prob",
    "calculate_combo_prob",
    "fair_shuffle",
    "simulate_fair_draw",
    # Domain Engines
    "query_cardpool_cards",
    "calculate_cardpool_stats",
    "format_cardpool_summary",
    "fetch_player_deck",
    "fetch_player_card_ids",
    "fetch_player_duel_decks",
    "partition_player_deck",
    "add_card_to_player_deck",
    "remove_card_from_player_deck",
    "clear_player_deck",
    "ensure_saved_deck_tables",
    "save_named_deck_slot",
    "load_named_deck_slot",
    "list_user_deck_slots",
    "get_saved_deck_slot",
    "rename_saved_deck_slot",
    "delete_saved_deck_slot",
    "record_deck_slot_match",
    "find_matching_saved_deck",
    "fetch_character_decks",
    "fetch_character_deck_by_id",
    "copy_character_deck_to_player_deck",
    "match_ai_deck_for_elo",
    "format_character_deck_summary",
    "parse_ydk",
    "export_to_ydk",
    "validate_ydk_passcodes",
    "save_ydk_file",
    "load_ydk_file",
    "import_ydk_to_player_deck",
    # Visual & Analytics
    "render_deck_canvas",
    "render_player_deck_canvas",
    "render_character_deck_canvas",
    "analyze_deck_structure",
    "validate_deck_legality",
]
