# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.foundation.types
Description:
    Bottom-Up Foundation: TypedDict declarations, data contracts, and structs
    for player decks, partitions, .ydk serialization, named slots, and analytics.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import TypedDict, Optional, List, Dict, Any, Union

# =============================================================================
# BLOCK 3: BODY BLOCK (Type Contracts & Struct Declarations)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Card Record Type Contract
# -----------------------------------------------------------------------------
class CardDict(TypedDict, total=False):
    """Represents a card record retrieved from custom_cards or player_decks."""
    id: int
    name: str
    set_number: Optional[str]
    card_type: str
    card_subtype: Optional[str]
    attribute: Optional[str]
    monster_type: Optional[str]
    level: Optional[int]
    level_or_rank_or_link: Optional[int]
    scale: Optional[int]
    atk: Optional[Union[int, str]]
    def_: Optional[Union[int, str]]
    link_arrows: Optional[int]
    effect_text: Optional[str]
    pendulum_effect: Optional[str]
    rarity: Optional[str]
    archetype: Optional[str]
    banlist_status: Optional[str]
    quantity: int
    section: Optional[str]
    local_image_path: Optional[str]
    image_url: Optional[str]


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Partitioned Deck Structure
# -----------------------------------------------------------------------------
class DeckPartition(TypedDict):
    """Partitions a deck into official sections with legality validation."""
    main_deck: List[Dict[str, Any]]
    extra_deck: List[Dict[str, Any]]
    side_deck: List[Dict[str, Any]]
    main_count: int
    extra_count: int
    side_count: int
    total_count: int
    is_legal: bool
    legality_badge: str
    violations: List[str]
    limits: Dict[str, int]


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Parsed YDK Struct
# -----------------------------------------------------------------------------
class ParsedYDK(TypedDict):
    """Structured result from parsing standard .YDK file content."""
    creator: Optional[str]
    main_passcodes: List[int]
    extra_passcodes: List[int]
    side_passcodes: List[int]
    main_count: int
    extra_count: int
    side_count: int
    total_count: int
    passcode_counts: Dict[int, int]
    is_valid_format: bool


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Saved Named Deck Slot Profile
# -----------------------------------------------------------------------------
class SavedDeckSlot(TypedDict):
    """Profile telemetry for a user's saved multi-deck slot."""
    id: int
    deck_name: str
    ydk_content: str
    created_at: str
    main_count: int
    extra_count: int
    side_count: int
    total_count: int
    is_legal: bool
    legality_badge: str


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Story Character Deck Record
# -----------------------------------------------------------------------------
class StoryDeckRecord(TypedDict, total=False):
    """Story / Character pre-constructed deck profile and telemetry."""
    id: int
    name: str
    character_id: Optional[int]
    duelist_name: Optional[str]
    duelist_alias: Optional[str]
    description: Optional[str]
    cards: List[Dict[str, Any]]
    main_count: int
    extra_count: int
    side_count: int
    total_count: int
    is_legal: bool
    legality_badge: str
    ai_elo: int
    story_chapter: str


# -----------------------------------------------------------------------------
# Sub-Block 3.6: Tactical Deck Analysis Result
# -----------------------------------------------------------------------------
class DeckAnalysisResult(TypedDict, total=False):
    """Comprehensive analytical report on a deck's tactical and structural profile."""
    total_count: int
    main_count: int
    extra_count: int
    side_count: int
    monsters: int
    spells: int
    traps: int
    main_cards: List[Dict[str, Any]]
    extra_cards: List[Dict[str, Any]]
    side_cards: List[Dict[str, Any]]
    is_set_1_standard: bool
    levels: Dict[str, int]
    tributes: Dict[str, int]
    extra_mechanics: Dict[str, int]
    attributes: Dict[str, int]
    races: Dict[str, int]
    rarities: Dict[str, int]
    field_spells: List[Dict[str, Any]]
    field_spell_count: int
    field_dependent_cards: List[Dict[str, Any]]
    field_dependent_count: int
    field_status: str
    field_opening_prob: float
    starter_opening_prob: float
    notes: List[str]


# -----------------------------------------------------------------------------
# Sub-Block 3.7: Master Rule Legality Report
# -----------------------------------------------------------------------------
class LegalityResult(TypedDict):
    """Validation report checking a deck against official Master Rule 5 construction constraints."""
    is_legal: bool
    main_count: int
    extra_count: int
    side_count: int
    errors: List[str]
    warnings: List[str]


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "CardDict",
    "DeckPartition",
    "ParsedYDK",
    "SavedDeckSlot",
    "StoryDeckRecord",
    "DeckAnalysisResult",
    "LegalityResult",
]

