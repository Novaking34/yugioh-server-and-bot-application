# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.utils.foundation
Description:
    Foundation Package for Discord Bot Formatting & UI Subsystem.
    Provides bottom-up constants, card frame color palettes, educational metadata,
    tribute rules, combat damage calculations, and simulator formatters.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .colors import (
    FRAME_COLORS,
    get_card_color,
)

from .types_guide_data import (
    SPELL_CARD_TYPES,
    TRAP_CARD_TYPES,
    MONSTER_CARD_FRAMES,
    MONSTER_SUBTYPES,
    ALL_26_MONSTER_RACES,
    CARD_ATTRIBUTES,
    LEVELS_AND_RANKS_DATA,
    SPELL_SPEEDS_DATA,
)

from .duel_math import (
    get_tribute_requirement,
    is_tribute_summon,
    calculate_battle_damage,
    calculate_piercing_damage,
    is_valid_level,
    is_valid_rank,
    is_valid_link_rating,
    is_valid_scale,
)

from .formatters import (
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

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Colors
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
]
