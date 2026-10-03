# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck
Description:
    Root Deck Service Entry Point & Translation Bridge.
    Re-exports the central DeckService engine, foundation primitives,
    domain storage operations, and visual analytics from the modular
    subsystem at `services.deck`.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Layered Package Imports)
# =============================================================================

# 2.1 Core Orchestrator Unit
from .deck.core import DeckService

# 2.2 Foundation Constants & Master Rule Limits
from .deck.foundation.constants import (
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

# 2.3 Foundation Type Contracts & Structs
from .deck.foundation.types import (
    CardDict,
    DeckPartition,
    ParsedYDK,
    SavedDeckSlot,
    StoryDeckRecord,
    DeckAnalysisResult,
    LegalityResult,
)

# 2.4 Foundation Classifiers & PSCT Zone Detectors
from .deck.foundation.classifier import (
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

# 2.5 Foundation Math & Probability Engines
from .deck.foundation.math import (
    is_deckout_condition,
    validate_hand_size,
    check_end_phase_discard_requirement,
    calculate_draw_prob,
    calculate_opening_hand_prob,
    calculate_combo_prob,
    fair_shuffle,
    simulate_fair_draw,
)

# 2.6 Domain Engines (Cardpool, Storage, Slots, Story, YDK)
from .deck.domain.cardpool import (
    query_cardpool_cards,
    calculate_cardpool_stats,
    format_cardpool_summary,
)
from .deck.domain.storage import (
    fetch_player_deck,
    fetch_player_card_ids,
    partition_player_deck,
    add_card_to_player_deck,
    remove_card_from_player_deck,
    clear_player_deck,
)
from .deck.domain.slots import (
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
from .deck.domain.story import (
    fetch_character_decks,
    fetch_character_deck_by_id,
    copy_character_deck_to_player_deck,
    match_ai_deck_for_elo,
    format_character_deck_summary,
)
from .deck.domain.ydk import (
    parse_ydk,
    export_to_ydk,
    validate_ydk_passcodes,
    save_ydk_file,
    load_ydk_file,
    import_ydk_to_player_deck,
)

# 2.7 Visual & Tactical Presentation Engines
from .deck.visual.canvas import (
    render_deck_canvas,
    render_player_deck_canvas,
    render_character_deck_canvas,
)
from .deck.visual.analytics import (
    analyze_deck_structure,
    validate_deck_legality,
)


# =============================================================================
# BLOCK 3: BODY BLOCK (Bridge Re-Exports & Sub-Block Routing)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Core Orchestrator Bridge
# -----------------------------------------------------------------------------
# Primary service engine instance creation and interface routing:
# DeckService acts as the central translation unit managing active state.

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Foundation & Game Rule Contracts Bridge
# -----------------------------------------------------------------------------
# Re-exports official Master Rule limits, hand boundaries, zone tokens,
# TypedDict contracts, and PSCT classifier/math algorithms.

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Domain Operations & Persistence Bridge
# -----------------------------------------------------------------------------
# Re-exports data layer operations: live cardpool telemetry, active player deck
# CRUD, 20-slot named profile management, pre-built story AI ELO matchmaking,
# and bidirectional .YDK ingestion/export.

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Visual Presentation & Tactical Profiling Bridge
# -----------------------------------------------------------------------------
# Re-exports Pillow 10-column visual deck canvas generation and deep tactical
# ratio analysis engines.


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    # Sub-Block 3.1: Core Orchestrator
    "DeckService",
    # Sub-Block 3.2: Foundation Constants
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
    # Sub-Block 3.2: Foundation Types
    "CardDict",
    "DeckPartition",
    "ParsedYDK",
    "SavedDeckSlot",
    "StoryDeckRecord",
    "DeckAnalysisResult",
    "LegalityResult",
    # Sub-Block 3.2: Foundation Classifiers & Math
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
    "is_deckout_condition",
    "validate_hand_size",
    "check_end_phase_discard_requirement",
    "calculate_draw_prob",
    "calculate_opening_hand_prob",
    "calculate_combo_prob",
    "fair_shuffle",
    "simulate_fair_draw",
    # Sub-Block 3.3: Domain Operations
    "query_cardpool_cards",
    "calculate_cardpool_stats",
    "format_cardpool_summary",
    "fetch_player_deck",
    "fetch_player_card_ids",
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
    # Sub-Block 3.4: Visual Presentation & Analytics
    "render_deck_canvas",
    "render_player_deck_canvas",
    "render_character_deck_canvas",
    "analyze_deck_structure",
    "validate_deck_legality",
]
