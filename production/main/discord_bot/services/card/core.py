# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.core
Description:
    Core Translation Unit: Central CardService Facade Orchestrator.
    Coordinates custom card discovery, real-time ranked autocomplete,
    meta analytics, and live duel event telemetry by delegating to specialized
    modular subsystems.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Imports, Type Contracts & Logger)
# =============================================================================

from typing import Optional, List, Dict, Any, Union, Sequence
from bot_config import BOT_CONFIG
from production.main.logger import get_logger

from .foundation.constants import (
    DEFAULT_AUTOCOMPLETE_LIMIT,
    DEFAULT_RECENT_LIMIT,
    DEFAULT_META_LIMIT,
)
from .foundation.formatters import format_card_autocomplete_choice
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
    search_cards,
    format_autocomplete_label,
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

logger = get_logger("discord_bot.services.card")

# =============================================================================
# BLOCK 3: BODY BLOCK (Core CardService Engine Translation Unit)
# =============================================================================

class CardService:
    """
    Central service handling custom card retrieval, search suggestions,
    meta analytics, and usage telemetry across player decks and duels.
    Modularly delegates concrete operations to specialized subsystems.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initializes service with database path from config if not provided."""
        self.db_path = db_path or BOT_CONFIG.get("content_db_path") or BOT_CONFIG["db_path"]

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Card Discovery & Direct Lookups
    # -------------------------------------------------------------------------

    async def get_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Direct O(1) indexed lookup for a single card by its 8-digit passcode ID."""
        return await get_card_by_id(self.db_path, card_id)

    async def get_card_by_set_number(self, set_number: str) -> Optional[Dict[str, Any]]:
        """Direct lookup for a single card by its official set number (e.g. TLOK-001)."""
        return await get_card_by_set_number(self.db_path, set_number)

    async def get_card_by_query(self, query: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Retrieves a custom card by exact or prioritized fuzzy match across passcode, set, or name."""
        return await get_card_by_query(self.db_path, query)

    async def get_cards_by_filter(
        self,
        card_type: Optional[str] = None,
        card_subtype: Optional[str] = None,
        attribute: Optional[str] = None,
        archetype: Optional[str] = None,
        monster_type: Optional[str] = None,
        level: Optional[int] = None,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        scale: Optional[int] = None,
        min_atk: Optional[int] = None,
        max_atk: Optional[int] = None,
        min_def: Optional[int] = None,
        max_def: Optional[int] = None,
        rarity: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Discovers cards matching comprehensive game mechanics and filter criteria."""
        return await get_cards_by_filter(
            self.db_path,
            card_type=card_type,
            card_subtype=card_subtype,
            attribute=attribute,
            archetype=archetype,
            monster_type=monster_type,
            level=level,
            min_level=min_level,
            max_level=max_level,
            scale=scale,
            min_atk=min_atk,
            max_atk=max_atk,
            min_def=min_def,
            max_def=max_def,
            rarity=rarity,
            is_extra_deck=is_extra_deck,
            limit=limit,
        )

    async def get_extra_deck_cards(self) -> List[Dict[str, Any]]:
        """Retrieves all registered Extra Deck cards (Fusion, Synchro, Xyz, Link)."""
        return await get_extra_deck_cards(self.db_path)

    async def get_main_deck_cards(self) -> List[Dict[str, Any]]:
        """Retrieves all registered Main Deck cards (Monsters, Spells, Traps)."""
        return await get_main_deck_cards(self.db_path)

    async def get_field_spells(self) -> List[Dict[str, Any]]:
        """Retrieves all Field Spell cards in the cardpool."""
        return await get_field_spells(self.db_path)

    async def get_ritual_monsters(self) -> List[Dict[str, Any]]:
        """Retrieves all Ritual Monster cards in the cardpool."""
        return await get_ritual_monsters(self.db_path)

    async def get_cards_by_archetype(self, archetype: str) -> List[Dict[str, Any]]:
        """Retrieves all cards belonging to a specific archetype (e.g. Kasutamaiza)."""
        return await get_cards_by_archetype(self.db_path, archetype)

    async def get_all_cards(self) -> List[Dict[str, Any]]:
        """Returns all registered custom cards in Set 1."""
        return await get_all_cards(self.db_path)

    async def get_all_cards_partitioned(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns the complete Set 1 cardpool partitioned into Main Deck and Extra Deck categories."""
        return await get_all_cards_partitioned(self.db_path)

    async def get_random_card(
        self,
        card_type: Optional[str] = None,
        card_subtype: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        archetype: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Selects a random card from the active pool with optional mechanical filters."""
        return await get_random_card(
            self.db_path,
            card_type=card_type,
            card_subtype=card_subtype,
            is_extra_deck=is_extra_deck,
            archetype=archetype,
        )

    async def get_recent_cards(self, limit: int = DEFAULT_RECENT_LIMIT) -> List[Dict[str, Any]]:
        """Returns recently added custom cards with summary identity."""
        return await get_recent_cards(self.db_path, limit=limit)

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Real-time Autocomplete Engine
    # -------------------------------------------------------------------------

    @staticmethod
    def format_autocomplete_label(card: Dict[str, Any]) -> str:
        """Builds a rich, compact single-line label for Discord autocomplete choice menus."""
        return format_autocomplete_label(card)

    async def search_cards(
        self,
        current: str,
        limit: int = DEFAULT_AUTOCOMPLETE_LIMIT,
        card_type: Optional[str] = None,
        card_subtype: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        archetype: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns ranked matching card suggestions for real-time Discord autocomplete."""
        return await search_cards(
            self.db_path,
            current=current,
            limit=limit,
            card_type=card_type,
            card_subtype=card_subtype,
            is_extra_deck=is_extra_deck,
            archetype=archetype,
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Telemetry & Meta Analytics Engine
    # -------------------------------------------------------------------------

    async def get_card_usage_stats(self, card_id: int) -> Dict[str, Any]:
        """Fetches comprehensive telemetry stats for a card joined with card metadata."""
        return await get_card_usage_stats(self.db_path, card_id)

    async def get_meta_overview(
        self,
        limit: int = DEFAULT_META_LIMIT,
        card_type: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        archetype: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Returns competitive format meta leaderboards across multiple axes."""
        return await get_meta_overview(
            self.db_path,
            limit=limit,
            card_type=card_type,
            is_extra_deck=is_extra_deck,
            archetype=archetype,
        )

    async def get_card_win_rates(
        self,
        limit: int = 10,
        min_matches: int = 1,
        card_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns cards ranked by duel win rate percentage with minimum match threshold."""
        return await get_card_win_rates(
            self.db_path,
            limit=limit,
            min_matches=min_matches,
            card_type=card_type,
        )

    async def get_archetype_meta_stats(self, archetype: str) -> Dict[str, Any]:
        """Aggregates meta telemetry across all registered cards in a specific archetype."""
        return await get_archetype_meta_stats(self.db_path, archetype)

    async def get_cardpool_telemetry_summary(self) -> Dict[str, Any]:
        """Returns macro server-wide health and activity metrics for the cardpool."""
        return await get_cardpool_telemetry_summary(self.db_path)

    async def get_underused_cards(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Identifies cards with lowest deck inclusion and play activity."""
        return await get_underused_cards(self.db_path, limit=limit)

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Live Duel Event Tracking Mutators
    # -------------------------------------------------------------------------

    async def track_card_draw(self, card_id: int, count: int = 1) -> None:
        """Increments draw count for a card during live duels."""
        await track_card_draw(self.db_path, card_id, count=count)

    async def track_cards_drawn(self, card_ids: Sequence[int]) -> None:
        """Atomically records multi-card draws in a single transaction."""
        await track_cards_drawn(self.db_path, card_ids)

    async def track_card_play(self, card_id: int, count: int = 1) -> None:
        """Increments play count for a card when summoned or activated."""
        await track_card_play(self.db_path, card_id, count=count)

    async def track_cards_played(self, card_ids: Sequence[int]) -> None:
        """Atomically records multi-card plays in a single transaction."""
        await track_cards_played(self.db_path, card_ids)

    async def track_card_match_result(self, card_id: int, is_win: bool) -> None:
        """Records a match win or loss for a single card in an active deck."""
        await track_card_match_result(self.db_path, card_id, is_win)

    async def track_cards_match_result(self, card_ids: Sequence[int], is_win: bool) -> None:
        """Atomically records match outcome for all distinct cards in a player's deck."""
        await track_cards_match_result(self.db_path, card_ids, is_win)

    async def track_deck_inclusion(self, card_id: int, delta: int) -> None:
        """Updates the count of player decks including this card."""
        await track_deck_inclusion(self.db_path, card_id, delta)

    async def batch_track_deck_inclusions(self, card_deltas: Dict[int, int]) -> None:
        """Atomically updates deck inclusion counts for multiple cards in a single transaction."""
        await batch_track_deck_inclusions(self.db_path, card_deltas)

    async def reset_card_telemetry(self, card_id: Optional[int] = None) -> None:
        """Resets telemetry counters to zero for a specific card or all cards."""
        await reset_card_telemetry(self.db_path, card_id)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "CardService",
    "format_card_autocomplete_choice",
]
