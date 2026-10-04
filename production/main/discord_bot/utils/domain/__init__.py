# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.utils.domain
Description:
    Domain Operations Package for Discord Bot Formatting & UI Subsystem.
    Provides presentation embed builders, real-time autocomplete handlers,
    duelist license renderers, story RPG encounter profiles, and live ASCII duel field visualization.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .card_embeds import (
    build_card_embed,
    build_card_stats_embed,
    build_card_types_guide_embed,
    format_cardpool_catalog_line,
    build_meta_telemetry_embed,
    build_cardpool_catalog_embed,
    add_chunked_catalog_fields,
    build_recent_cards_embed,
    format_passcode,
    format_stat_value,
    format_link_arrows,
    format_spell_trap_property,
)

from .autocomplete import (
    DISCORD_MAX_AUTOCOMPLETE_CHOICES,
    build_card_autocomplete_choices,
    card_name_autocomplete,
    create_card_autocomplete,
)

from .duel_board import (
    DuelBoard,
    render_duel_field_ascii,
    build_board_guide_embed,
)

from .ranking_embeds import (
    build_rank_embed,
    build_leaderboard_embed,
)

from .story_embeds import (
    build_story_stage_embed,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Card Presentation
    "build_card_embed",
    "build_card_stats_embed",
    "build_card_types_guide_embed",
    "format_cardpool_catalog_line",
    "build_meta_telemetry_embed",
    "build_cardpool_catalog_embed",
    "add_chunked_catalog_fields",
    "build_recent_cards_embed",
    "format_passcode",
    "format_stat_value",
    "format_link_arrows",
    "format_spell_trap_property",
    # Autocomplete Handlers
    "DISCORD_MAX_AUTOCOMPLETE_CHOICES",
    "build_card_autocomplete_choices",
    "card_name_autocomplete",
    "create_card_autocomplete",
    # Duel Field & Board
    "DuelBoard",
    "render_duel_field_ascii",
    "build_board_guide_embed",
    # Ranking & Leaderboards
    "build_rank_embed",
    "build_leaderboard_embed",
    # Story Campaign
    "build_story_stage_embed",
]
