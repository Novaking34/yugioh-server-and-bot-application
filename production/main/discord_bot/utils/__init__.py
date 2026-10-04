# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.utils
Description:
    Modular Discord Bot Formatting & UI Presentation Subsystem.
    Organized with Top-Down / Bottom-Up C-style compilation unit architecture:
    - foundation/: Bottom-Up Foundation (Color Palettes, Guide Metadata, Duel Math, Formatters)
    - domain/    : Presentation Units (Card Embeds, Duel Board, Ranking, Story)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Foundation Primitives (foundation/)
# -----------------------------------------------------------------------------
from .foundation.colors import (
    FRAME_COLORS,
    get_card_color,
)

from .foundation.types_guide_data import (
    SPELL_CARD_TYPES,
    TRAP_CARD_TYPES,
    MONSTER_CARD_FRAMES,
    MONSTER_SUBTYPES,
    ALL_26_MONSTER_RACES,
    CARD_ATTRIBUTES,
    LEVELS_AND_RANKS_DATA,
    SPELL_SPEEDS_DATA,
)

from .foundation.duel_math import (
    get_tribute_requirement,
    is_tribute_summon,
    calculate_battle_damage,
    calculate_piercing_damage,
    is_valid_level,
    is_valid_rank,
    is_valid_link_rating,
    is_valid_scale,
)

from .foundation.formatters import (
    STAT_UNKNOWN,
    LINK_ARROW_GLYPHS,
    LINK_BIT_MAP,
    ATTRIBUTE_ICONS,
    SPELL_TRAP_ICONS,
    format_passcode,
    format_stat_value,
    format_link_arrows,
    format_spell_trap_property,
    get_spell_speed,
    format_monster_classification,
)

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Presentation Operations (domain/)
# -----------------------------------------------------------------------------
from .domain.card_embeds import (
    build_card_embed,
    build_card_stats_embed,
    build_card_types_guide_embed,
    format_cardpool_catalog_line,
    build_meta_telemetry_embed,
    build_cardpool_catalog_embed,
    build_recent_cards_embed,
)

from .domain.autocomplete import (
    DISCORD_MAX_AUTOCOMPLETE_CHOICES,
    build_card_autocomplete_choices,
    card_name_autocomplete,
    create_card_autocomplete,
)

from .domain.duel_board import (
    DuelBoard,
    render_duel_field_ascii,
    build_board_guide_embed,
)

from .domain.ranking_embeds import (
    build_rank_embed,
    build_leaderboard_embed,
)

from .domain.story_embeds import (
    build_story_stage_embed,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Colors & Palettes
    "FRAME_COLORS",
    "get_card_color",
    # Metadata Guides
    "SPELL_CARD_TYPES",
    "TRAP_CARD_TYPES",
    "MONSTER_CARD_FRAMES",
    "MONSTER_SUBTYPES",
    "ALL_26_MONSTER_RACES",
    "CARD_ATTRIBUTES",
    "LEVELS_AND_RANKS_DATA",
    "SPELL_SPEEDS_DATA",
    # Duel Math
    "get_tribute_requirement",
    "is_tribute_summon",
    "calculate_battle_damage",
    "calculate_piercing_damage",
    "is_valid_level",
    "is_valid_rank",
    "is_valid_link_rating",
    "is_valid_scale",
    # Formatting Primitives & Simulator Invariants
    "STAT_UNKNOWN",
    "LINK_ARROW_GLYPHS",
    "LINK_BIT_MAP",
    "ATTRIBUTE_ICONS",
    "SPELL_TRAP_ICONS",
    "format_passcode",
    "format_stat_value",
    "format_link_arrows",
    "format_spell_trap_property",
    "get_spell_speed",
    "format_monster_classification",
    # Card Presentation
    "build_card_embed",
    "build_card_stats_embed",
    "build_card_types_guide_embed",
    "format_cardpool_catalog_line",
    "build_meta_telemetry_embed",
    "build_cardpool_catalog_embed",
    "build_recent_cards_embed",
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
