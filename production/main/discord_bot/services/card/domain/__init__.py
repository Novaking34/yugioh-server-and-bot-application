# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.card.domain
Description:
    Domain Subsystems for Custom Card Service:
    - discovery: O(1) indexed lookups, multi-criteria filtering, deck partitioning
    - autocomplete: real-time ranked fuzzy autocomplete
    - analytics: meta leaderboards, win-rate rankings, archetype statistics
    - mutators: atomic draw, play, deck inclusion, and match result event trackers
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .discovery import (
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

from .autocomplete import (
    format_autocomplete_label,
    search_cards,
)

from .analytics import (
    get_card_usage_stats,
    get_meta_overview,
    get_card_win_rates,
    get_archetype_meta_stats,
    get_cardpool_telemetry_summary,
    get_underused_cards,
)

from .mutators import (
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
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    # Discovery
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
    # Autocomplete
    "format_autocomplete_label",
    "search_cards",
    # Analytics
    "get_card_usage_stats",
    "get_meta_overview",
    "get_card_win_rates",
    "get_archetype_meta_stats",
    "get_cardpool_telemetry_summary",
    "get_underused_cards",
    # Mutators
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
