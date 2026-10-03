# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.deck.domain
Description:
    Domain Logic & Subsystem Engines:
    - cardpool: 3.1 Live cardpool queries & telemetry
    - storage: 3.2 Player active deck CRUD & capacity enforcement
    - slots: 3.3 Multi-deck named slot profiles (20-slot ceiling)
    - story: 3.4 Pre-constructed story decks & AI ELO matchmaking
    - ydk: 3.5 EDOPro / Project Ignis .YDK serialization & ingestion
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# =============================================================================
# BLOCK 3: BODY BLOCK (Domain Engine Re-Exports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Cardpool Telemetry Engine
# -----------------------------------------------------------------------------
from .cardpool import (
    query_cardpool_cards,
    calculate_cardpool_stats,
    format_cardpool_summary,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Active Deck Storage Engine
# -----------------------------------------------------------------------------
from .storage import (
    fetch_player_deck,
    fetch_player_card_ids,
    partition_player_deck,
    add_card_to_player_deck,
    remove_card_from_player_deck,
    clear_player_deck,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Named Deck Slot Engine
# -----------------------------------------------------------------------------
from .slots import (
    ensure_saved_deck_tables,
    save_named_deck_slot,
    load_named_deck_slot,
    list_user_deck_slots,
    get_saved_deck_slot,
    rename_saved_deck_slot,
    delete_saved_deck_slot,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.4: Story Decks & AI Matchmaking Engine
# -----------------------------------------------------------------------------
from .story import (
    fetch_character_decks,
    fetch_character_deck_by_id,
    copy_character_deck_to_player_deck,
    match_ai_deck_for_elo,
    format_character_deck_summary,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.5: .YDK Serialization & Ingestion Engine
# -----------------------------------------------------------------------------
from .ydk import (
    parse_ydk,
    export_to_ydk,
    validate_ydk_passcodes,
    save_ydk_file,
    load_ydk_file,
    import_ydk_to_player_deck,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================
__all__ = [
    # Cardpool
    "query_cardpool_cards",
    "calculate_cardpool_stats",
    "format_cardpool_summary",
    # Storage
    "fetch_player_deck",
    "fetch_player_card_ids",
    "partition_player_deck",
    "add_card_to_player_deck",
    "remove_card_from_player_deck",
    "clear_player_deck",
    # Slots
    "ensure_saved_deck_tables",
    "save_named_deck_slot",
    "load_named_deck_slot",
    "list_user_deck_slots",
    "get_saved_deck_slot",
    "rename_saved_deck_slot",
    "delete_saved_deck_slot",
    # Story
    "fetch_character_decks",
    "fetch_character_deck_by_id",
    "copy_character_deck_to_player_deck",
    "match_ai_deck_for_elo",
    "format_character_deck_summary",
    # YDK
    "parse_ydk",
    "export_to_ydk",
    "validate_ydk_passcodes",
    "save_ydk_file",
    "load_ydk_file",
    "import_ydk_to_player_deck",
]
