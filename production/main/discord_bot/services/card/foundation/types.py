# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.foundation.types
Description:
    C-Style Struct Contracts (TypedDicts) for Custom Card Service Subsystem.
    Provides strict type schemas for database record projections, telemetry
    summaries, and meta leaderboard snapshots.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Optional, List, TypedDict

# =============================================================================
# BLOCK 3: BODY BLOCK (C-Style Struct Contracts / TypedDicts)
# =============================================================================

# Functional TypedDict syntax is required because the database column is named
# `def` (a Python keyword) — the contract must match the row keys exactly.
CardRecordDict = TypedDict("CardRecordDict", {
    # Identity
    "id": int,                              # 8-digit passcode (e.g. 50000101)
    "name": str,
    "set_number": Optional[str],            # e.g. TLOK-001
    "set_code": Optional[str],              # e.g. TLOK
    # Frame & Classification
    "card_type": str,                       # Monster | Spell | Trap
    "card_subtype": Optional[str],          # Normal, Effect, Ritual, Fusion, Synchro, Xyz, Link, Pendulum, Field...
    "attribute": Optional[str],
    "monster_type": Optional[str],          # Species / race (Warrior, Dragon, ...)
    "archetype": Optional[str],
    # Battle Stats
    "level_or_rank_or_link": Optional[int],
    "level": Optional[int],                 # Alias of level_or_rank_or_link (duel engine tributes)
    "scale": Optional[int],                 # Pendulum scale 0-13
    "atk": Optional[int],                   # STAT_UNKNOWN (-2) == "?"
    "def": Optional[int],                   # STAT_UNKNOWN (-2) == "?"; NULL for Link monsters
    "link_arrows": Optional[str],           # Comma-separated, e.g. "BL,BR,T"
    # Rules Text
    "effect_text": str,
    "pendulum_effect": Optional[str],
    # Legality & Release
    "rarity": Optional[str],
    "banlist_status": Optional[str],        # Unlimited | Semi-Limited | Limited | Forbidden
    "playtesting_status": Optional[str],
    # Scripting (EDOPro / Project Ignis)
    "script_file": Optional[str],
    "script_status": Optional[str],         # Implemented | Draft | Stub | Vanilla
    # Assets & External Integration
    "image_url": Optional[str],
    "local_image_path": Optional[str],
    "duelingbook_id": Optional[str],
    "duelingbook_url": Optional[str],
    "creator_name": Optional[str],
    # Story & Lore Relations
    "lore_text": Optional[str],
    "story_significance": Optional[str],
    "faction_id": Optional[int],
    "faction_name": Optional[str],          # Joined from factions
    "signature_character_id": Optional[int],
    "character_name": Optional[str],        # Joined from characters
    # Audit
    "created_at": Optional[str],
}, total=False)


class CardSummaryDict(TypedDict, total=False):
    """Lightweight card shape for autocomplete and recent-additions lists."""
    id: int
    set_number: Optional[str]
    name: str
    card_type: str
    card_subtype: Optional[str]
    rarity: Optional[str]
    created_at: Optional[str]


class CardUsageStatsDict(TypedDict, total=False):
    """card_usage_stats row joined with card identity, plus derived win_rate."""
    card_id: int
    name: str
    set_number: Optional[str]
    card_type: str
    card_subtype: Optional[str]
    rarity: Optional[str]
    attribute: Optional[str]
    monster_type: Optional[str]
    archetype: Optional[str]
    level: Optional[int]
    scale: Optional[int]
    times_decked: int
    times_drawn: int
    times_played: int
    wins: int
    losses: int
    total_matches: int
    last_used_at: Optional[str]
    win_rate: float                          # Derived: wins / (wins + losses) * 100
    play_to_draw_ratio: float                # Derived: times_played / times_drawn * 100


class MetaOverviewDict(TypedDict, total=False):
    """Format meta snapshot covering popularity, playrate, and victory metrics."""
    most_popular: List[CardUsageStatsDict]
    most_victorious: List[CardUsageStatsDict]
    most_played: List[CardUsageStatsDict]
    highest_win_rate: List[CardUsageStatsDict]
    most_drawn: List[CardUsageStatsDict]


class ArchetypeMetaDict(TypedDict, total=False):
    """Aggregated meta performance metrics for a specific archetype."""
    archetype: str
    total_cards: int
    times_decked: int
    times_drawn: int
    times_played: int
    wins: int
    losses: int
    total_matches: int
    win_rate: float
    top_card_name: Optional[str]
    top_card_id: Optional[int]


class CardpoolTelemetrySummaryDict(TypedDict, total=False):
    """High-level cardpool health and participation statistics."""
    total_registered_cards: int
    distinct_cards_decked: int
    distinct_cards_drawn: int
    distinct_cards_played: int
    total_deck_inclusions: int
    total_card_draws: int
    total_card_plays: int
    total_card_wins: int
    total_card_losses: int


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "CardRecordDict",
    "CardSummaryDict",
    "CardUsageStatsDict",
    "MetaOverviewDict",
    "ArchetypeMetaDict",
    "CardpoolTelemetrySummaryDict",
]
