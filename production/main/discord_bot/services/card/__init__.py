# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.card
Description:
    Modular Custom Card Management Subsystem for Yu-Gi-Oh! Discord Bot & Story Server.
    Organized with Top-Down / Bottom-Up C-style compilation unit architecture:
    - foundation/: Bottom-Up Foundation (Constants, Struct Types, Label Formatters)
    - domain/    : Domain Engines (Discovery, Autocomplete, Analytics, Mutators)
    - core.py    : Top-Down Orchestrator Facade Engine (CardService)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Foundation Primitives (foundation/)
# -----------------------------------------------------------------------------
from .foundation.constants import (
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

from .foundation.types import (
    CardRecordDict,
    CardSummaryDict,
    CardUsageStatsDict,
    MetaOverviewDict,
    ArchetypeMetaDict,
    CardpoolTelemetrySummaryDict,
)

from .foundation.formatters import (
    build_card_descriptor_tag,
    format_card_autocomplete_choice,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Domain Operations (domain/)
# -----------------------------------------------------------------------------
from .domain.discovery import (
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

from .domain.autocomplete import (
    format_autocomplete_label,
    search_cards,
)

from .domain.analytics import (
    get_card_usage_stats,
    get_meta_overview,
    get_card_win_rates,
    get_archetype_meta_stats,
    get_cardpool_telemetry_summary,
    get_underused_cards,
)

from .domain.mutators import (
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

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Core Facade Orchestrator (core.py)
# -----------------------------------------------------------------------------
from .core import CardService

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
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
