# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.foundation.constants
Description:
    Header Constants & Master Rule Invariants for Custom Card Service Subsystem.
    Defines database projections, telemetry counter names, query limits,
    card frame constants, and stat sentinels.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Final, Tuple

# =============================================================================
# BLOCK 3: BODY BLOCK (Constants & Master Rule Invariants)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Query Limits (Discord UI select menus and autocomplete cap at 25)
# -----------------------------------------------------------------------------
DEFAULT_AUTOCOMPLETE_LIMIT: Final[int] = 20   # /card autocomplete suggestions
DEFAULT_RECENT_LIMIT: Final[int] = 10         # /recent newest additions
DEFAULT_META_LIMIT: Final[int] = 5            # /meta top-N leaderboards
MIN_WINRATE_SAMPLE_MATCHES: Final[int] = 3    # Minimum duels required for win-rate leaderboard

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Card Identity Vocabulary (mirrors schema.sql custom_cards)
# -----------------------------------------------------------------------------
# Primary card frames (custom_cards.card_type)
CARD_TYPE_MONSTER: Final[str] = "Monster"
CARD_TYPE_SPELL: Final[str] = "Spell"
CARD_TYPE_TRAP: Final[str] = "Trap"
CARD_TYPES: Final[Tuple[str, ...]] = (CARD_TYPE_MONSTER, CARD_TYPE_SPELL, CARD_TYPE_TRAP)

# Monster attributes (custom_cards.attribute)
CARD_ATTRIBUTES: Final[Tuple[str, ...]] = (
    "DARK", "LIGHT", "EARTH", "WATER", "FIRE", "WIND", "DIVINE"
)

# Stat sentinel: schema stores "?" ATK/DEF as -2. Treated as variable / unknown.
STAT_UNKNOWN: Final[int] = -2

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Canonical Database Projections & Joins
# -----------------------------------------------------------------------------
CARD_RECORD_PROJECTION: Final[str] = """
    c.*,
    c.level_or_rank_or_link AS level,
    f.name  AS faction_name,
    ch.name AS character_name
"""

CARD_RECORD_JOINS: Final[str] = """
    FROM custom_cards c
    LEFT JOIN factions   f  ON c.faction_id = f.id
    LEFT JOIN characters ch ON c.signature_character_id = ch.id
"""

# Extra deck matching SQL expression for custom_cards table
EXTRA_DECK_SQL_CONDITION: Final[str] = """(
    LOWER(c.card_type) IN ('fusion', 'synchro', 'xyz', 'link') OR
    LOWER(c.card_subtype) LIKE '%fusion%' OR
    LOWER(c.card_subtype) LIKE '%synchro%' OR
    LOWER(c.card_subtype) LIKE '%xyz%' OR
    LOWER(c.card_subtype) LIKE '%link%'
)"""

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Telemetry Counter Manifest (card_usage_stats columns)
# -----------------------------------------------------------------------------
TELEMETRY_COUNTERS: Final[Tuple[str, ...]] = (
    "times_decked",   # Included in player decks (deck engine lifecycle)
    "times_drawn",    # Drawn during live duels
    "times_played",   # Summoned / activated during live duels
    "wins",           # Matches won while in the active deck
    "losses",         # Matches lost while in the active deck
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
]
