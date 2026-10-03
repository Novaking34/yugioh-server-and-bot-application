# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.core
Description:
    Core Translation Unit: Central Engine Orchestrator coordinating player decks,
    character story progression, named slots, YDK format parsing, and tactical
    analytics. Modularly delegates concrete operations to specialized subsystems.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Imports, Type Contracts & Logger)
# =============================================================================

from typing import Optional, List, Dict, Any, Tuple, Union

from bot_config import BOT_CONFIG
from production.main.logger import get_logger

from .foundation.types import (
    CardDict,
    DeckPartition,
    ParsedYDK,
    SavedDeckSlot,
    StoryDeckRecord,
    DeckAnalysisResult,
    LegalityResult,
)

from .domain.cardpool import (
    query_cardpool_cards,
    calculate_cardpool_stats,
    format_cardpool_summary,
)

from .domain.storage import (
    fetch_player_deck,
    fetch_player_card_ids,
    partition_player_deck,
    add_card_to_player_deck,
    remove_card_from_player_deck,
    clear_player_deck,
)

from .domain.slots import (
    ensure_saved_deck_tables,
    save_named_deck_slot,
    load_named_deck_slot,
    list_user_deck_slots,
    get_saved_deck_slot,
    rename_saved_deck_slot,
    delete_saved_deck_slot,
)

from .domain.story import (
    fetch_character_decks,
    fetch_character_deck_by_id,
    copy_character_deck_to_player_deck,
    match_ai_deck_for_elo,
    format_character_deck_summary,
)

from .domain.ydk import (
    parse_ydk,
    export_to_ydk,
    validate_ydk_passcodes,
    save_ydk_file,
    load_ydk_file,
    import_ydk_to_player_deck,
)

from .visual.canvas import (
    render_deck_canvas,
    render_player_deck_canvas,
    render_character_deck_canvas,
)

from .visual.analytics import (
    analyze_deck_structure,
    validate_deck_legality,
)

logger = get_logger("discord_bot.services.deck")


# =============================================================================
# BLOCK 3: BODY BLOCK (Core DeckService Engine Translation Unit)
# =============================================================================

class DeckService:
    """
    Primary full deck server core coordinating player decks, character
    story progression, named slots, YDK format parsing, and tactical analytics.
    Modularly delegates concrete operations to specialized subsystems.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initializes service with database path from config if not provided."""
        self.db_path = db_path or BOT_CONFIG.get("db_path")

    async def ensure_tables(self) -> None:
        """Ensures the player_saved_decks table exists for multi-deck support."""
        await ensure_saved_deck_tables(self.db_path)

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Dynamic Cardpool Telemetry
    # -------------------------------------------------------------------------

    async def get_cardpool_cards(self, archetype_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries the live custom_cards database for all cards in the cardpool."""
        return await query_cardpool_cards(self.db_path, archetype_filter=archetype_filter)

    async def get_cardpool_stats(self, archetype_filter: Optional[str] = None) -> Dict[str, Any]:
        """Queries live cardpool dimensions, rarities, mechanics, and zone telemetry."""
        return await calculate_cardpool_stats(self.db_path, archetype_filter=archetype_filter)

    def format_cardpool_summary(self, stats: Dict[str, Any]) -> str:
        """Formats cardpool telemetry statistics into a structured, human-readable report."""
        return format_cardpool_summary(stats)

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Player Active Deck CRUD, Partitioning & Visual Rendering
    # -------------------------------------------------------------------------

    async def get_player_deck(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves all cards in a player's personal deck, sorted by category and name."""
        return await fetch_player_deck(self.db_path, user_id)

    async def get_player_card_ids(self, user_id: str) -> List[int]:
        """Returns flat list of card IDs (expanded by quantity) for duel initialization."""
        return await fetch_player_card_ids(self.db_path, user_id)

    async def get_player_deck_partitioned(self, user_id: str) -> DeckPartition:
        """Partitions the player's deck and enforces MR5 Min/Max boundary checks."""
        return await partition_player_deck(self.db_path, user_id)

    async def add_card_to_deck(
        self,
        user_id: str,
        card_id: int,
        quantity: int = 1
    ) -> Tuple[bool, str, int]:
        """Adds copies of a card to the deck with banlist and capacity clamps."""
        return await add_card_to_player_deck(self.db_path, user_id, card_id, quantity)

    async def remove_card_from_deck(
        self,
        user_id: str,
        card_id: int,
        quantity: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Removes or decrements a card in the player's active deck."""
        return await remove_card_from_player_deck(self.db_path, user_id, card_id, quantity)

    async def clear_deck(self, user_id: str) -> int:
        """Clears all cards from the player's active deck."""
        return await clear_player_deck(self.db_path, user_id)

    async def generate_deck_visual(
        self,
        user_id: str,
        deck_title: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """Renders an official visual deck canvas using PIL."""
        return await render_player_deck_canvas(
            self.db_path,
            user_id,
            deck_title=deck_title,
            output_path=output_path
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Multi-Deck Slots & Named Deck Storage
    # -------------------------------------------------------------------------

    async def save_named_deck(self, user_id: str, deck_name: str) -> Tuple[bool, str]:
        """Saves the user's active deck as a named deck profile slot (up to 20 slots)."""
        cards = await self.get_player_deck(user_id)
        return await save_named_deck_slot(self.db_path, user_id, deck_name, cards)

    async def load_named_deck(self, user_id: str, deck_name: str) -> Tuple[bool, str, int]:
        """Loads a previously saved named deck into the user's active deck."""
        return await load_named_deck_slot(self.db_path, user_id, deck_name)

    async def list_user_decks(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns all named decks saved by the user with enriched telemetry."""
        return await list_user_deck_slots(self.db_path, user_id)

    async def get_saved_deck(self, user_id: str, deck_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single saved named deck with full telemetry."""
        return await get_saved_deck_slot(self.db_path, user_id, deck_name)

    async def rename_saved_deck(self, user_id: str, old_name: str, new_name: str) -> Tuple[bool, str]:
        """Renames a saved deck slot profile."""
        return await rename_saved_deck_slot(self.db_path, user_id, old_name, new_name)

    async def delete_named_deck(self, user_id: str, deck_name: str) -> bool:
        """Deletes a saved named deck profile."""
        return await delete_saved_deck_slot(self.db_path, user_id, deck_name)

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Pre-Constructed Character Decks & Story Integration
    # -------------------------------------------------------------------------

    async def get_character_decks(self) -> List[Dict[str, Any]]:
        """Returns all pre-constructed story character decks with enriched telemetry."""
        return await fetch_character_decks(self.db_path)

    async def get_character_deck_by_id(self, deck_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a character deck along with registered deck_cards and telemetry."""
        return await fetch_character_deck_by_id(self.db_path, deck_id)

    async def copy_character_deck_to_player(
        self,
        user_id: str,
        deck_id: int
    ) -> Tuple[bool, str, int]:
        """Copies all cards from a character deck into the player's active deck."""
        return await copy_character_deck_to_player_deck(self.db_path, user_id, deck_id)

    async def get_ai_deck_for_elo(self, target_elo: int) -> Optional[Dict[str, Any]]:
        """Dynamically selects the optimal story deck closest to an AI ELO rating."""
        return await match_ai_deck_for_elo(self.db_path, target_elo)

    async def generate_character_deck_visual(
        self,
        deck_id: int,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """Renders an official visual canvas for a story character deck."""
        return await render_character_deck_canvas(
            self.db_path,
            deck_id,
            output_path=output_path
        )

    def format_character_deck_summary(self, deck: Dict[str, Any]) -> str:
        """Formats a character deck into a clean, markdown discord embed/text summary."""
        return format_character_deck_summary(deck)

    # -------------------------------------------------------------------------
    # Sub-Block 3.5: .YDK Serialization & Ingestion Subsystem
    # -------------------------------------------------------------------------

    def parse_ydk(self, ydk_text: str) -> ParsedYDK:
        """Parses standard .ydk text into main, extra, and side sections."""
        return parse_ydk(ydk_text)

    def export_to_ydk(
        self,
        cards: Union[List[Dict[str, Any]], Dict[str, Any]],
        deck_title: str = "Custom Deck"
    ) -> str:
        """Serializes cards or partitioned deck into standard .ydk format."""
        return export_to_ydk(cards, deck_title=deck_title)

    async def export_player_deck_to_ydk(
        self,
        user_id: str,
        deck_title: Optional[str] = None
    ) -> str:
        """Exports a player's active deck directly to standard .ydk format."""
        cards = await self.get_player_deck(user_id)
        d_name = deck_title or f"Player_{user_id}_Deck"
        return self.export_to_ydk(cards, deck_title=d_name)

    async def import_from_ydk(self, user_id: str, ydk_text: str) -> Tuple[bool, str, int]:
        """Ingests a standard .ydk text representation into the player's active deck."""
        return await import_ydk_to_player_deck(self.db_path, user_id, ydk_text)

    def save_ydk_file(
        self,
        file_path: str,
        cards: Union[List[Dict[str, Any]], Dict[str, Any]],
        deck_title: str = "Custom Deck"
    ) -> str:
        """Writes deck to a .ydk file on disk."""
        return save_ydk_file(file_path, cards, deck_title=deck_title)

    def load_ydk_file(self, file_path: str) -> ParsedYDK:
        """Reads and parses a .ydk file from disk."""
        return load_ydk_file(file_path)

    # -------------------------------------------------------------------------
    # Sub-Block 3.6: Tactical Analytics & Master Rule Validation
    # -------------------------------------------------------------------------

    def analyze_deck_structure(self, cards: List[Dict[str, Any]]) -> DeckAnalysisResult:
        """Performs in-depth tactical telemetry and legal structure validation."""
        return analyze_deck_structure(cards)

    def validate_deck_legality(self, cards: List[Dict[str, Any]]) -> LegalityResult:
        """Validates whether a deck adheres to official Master Rule construction constraints."""
        return validate_deck_legality(cards)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = ["DeckService"]
