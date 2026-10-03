# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card
Description:
    Root Card Service Entry Point & Translation Bridge.
    Re-exports the central CardService engine, foundation primitives,
    and domain operations from the modular subsystem at `services.card`.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Layered Package Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Core Orchestrator Unit
# -----------------------------------------------------------------------------
from .card.core import CardService

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Foundation Constants & Master Rule Invariants
# -----------------------------------------------------------------------------
from .card.foundation.constants import (
    DEFAULT_AUTOCOMPLETE_LIMIT,
    DEFAULT_RECENT_LIMIT,
    DEFAULT_META_LIMIT,
    MIN_WINRATE_SAMPLE_MATCHES,
    CARD_TYPE_MONSTER,
    CARD_TYPE_SPELL,
    CARD_TYPE_TRAP,
    CARD_TYPES,
    CARD_ATTRIBUTES,
    STAT_UNKNOWN,
    CARD_RECORD_PROJECTION,
    CARD_RECORD_JOINS,
    EXTRA_DECK_SQL_CONDITION,
    TELEMETRY_COUNTERS,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Foundation Type Contracts & Structs
# -----------------------------------------------------------------------------
from .card.foundation.types import (
    CardRecordDict,
    CardSummaryDict,
    CardUsageStatsDict,
    MetaOverviewDict,
    ArchetypeMetaDict,
    CardpoolTelemetrySummaryDict,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.4: Foundation Label Formatters
# -----------------------------------------------------------------------------
from .card.foundation.formatters import (
    build_card_descriptor_tag,
    format_card_autocomplete_choice,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.5: Domain Operations (Discovery, Autocomplete, Analytics, Mutators)
# -----------------------------------------------------------------------------
from .card.domain.discovery import (
    get_card_by_id,
    get_card_by_set_number,
    get_card_by_query,
    get_cards_by_filter,
    get_extra_deck_cards,
    get_main_deck_cards,
    get_field_spells,
    get_ritual_monsters,
    get_cards_by_archetype,
    get_all_cards,
    get_all_cards_partitioned,
    get_random_card,
    get_recent_cards,
)

from .card.domain.autocomplete import (
    format_autocomplete_label,
    search_cards,
)

from .card.domain.analytics import (
    get_card_usage_stats,
    get_meta_overview,
    get_card_win_rates,
    get_archetype_meta_stats,
    get_cardpool_telemetry_summary,
    get_underused_cards,
)

from .card.domain.mutators import (
    track_card_draw,
    track_cards_drawn,
    track_card_play,
    track_cards_played,
    track_card_match_result,
    track_cards_match_result,
    track_deck_inclusion,
    batch_track_deck_inclusions,
    reset_card_telemetry,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    # Core Engine Facade
    "CardService",
    # Formatters
    "build_card_descriptor_tag",
    "format_card_autocomplete_choice",
    "format_autocomplete_label",
    # Constants
    "DEFAULT_AUTOCOMPLETE_LIMIT",
    "DEFAULT_RECENT_LIMIT",
    "DEFAULT_META_LIMIT",
    "MIN_WINRATE_SAMPLE_MATCHES",
    "CARD_TYPE_MONSTER",
    "CARD_TYPE_SPELL",
    "CARD_TYPE_TRAP",
    "CARD_TYPES",
    "CARD_ATTRIBUTES",
    "STAT_UNKNOWN",
    "CARD_RECORD_PROJECTION",
    "CARD_RECORD_JOINS",
    "EXTRA_DECK_SQL_CONDITION",
    "TELEMETRY_COUNTERS",
    # Types / Structs
    "CardRecordDict",
    "CardSummaryDict",
    "CardUsageStatsDict",
    "MetaOverviewDict",
    "ArchetypeMetaDict",
    "CardpoolTelemetrySummaryDict",
    # Domain Discovery
    "get_card_by_id",
    "get_card_by_set_number",
    "get_card_by_query",
    "get_cards_by_filter",
    "get_extra_deck_cards",
    "get_main_deck_cards",
    "get_field_spells",
    "get_ritual_monsters",
    "get_cards_by_archetype",
    "get_all_cards",
    "get_all_cards_partitioned",
    "get_random_card",
    "get_recent_cards",
    # Domain Autocomplete
    "search_cards",
    # Domain Analytics
    "get_card_usage_stats",
    "get_meta_overview",
    "get_card_win_rates",
    "get_archetype_meta_stats",
    "get_cardpool_telemetry_summary",
    "get_underused_cards",
    # Domain Mutators
    "track_card_draw",
    "track_cards_drawn",
    "track_card_play",
    "track_cards_played",
    "track_card_match_result",
    "track_cards_match_result",
    "track_deck_inclusion",
    "batch_track_deck_inclusions",
    "reset_card_telemetry",
]
