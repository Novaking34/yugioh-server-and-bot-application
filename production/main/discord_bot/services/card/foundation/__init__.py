# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.card.foundation
Description:
    Foundation primitives, constants, structs, and formatting routines for CardService.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .constants import (
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

from .types import (
    CardRecordDict,
    CardSummaryDict,
    CardUsageStatsDict,
    MetaOverviewDict,
    ArchetypeMetaDict,
    CardpoolTelemetrySummaryDict,
)

from .formatters import (
    build_card_descriptor_tag,
    format_card_autocomplete_choice,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
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
    "CardRecordDict",
    "CardSummaryDict",
    "CardUsageStatsDict",
    "MetaOverviewDict",
    "ArchetypeMetaDict",
    "CardpoolTelemetrySummaryDict",
    "build_card_descriptor_tag",
    "format_card_autocomplete_choice",
]
