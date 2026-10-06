#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.functional.test_deck_builder_scenario
Architecture: Hybrid Systems Engineering (Functional Testing Subsystem)
Domain: End-to-End Deck Management / Player Deckbuilding Lifecycle
Description:
    Functional test suite simulating a complete deckbuilding session:
    1. Clearing player deck and assembling custom cards.
    2. Analyzing tribute curves, field awareness, and extra deck partitions.
    3. Saving the custom deck into a named profile slot.
    4. Exporting to a standard .ydk simulator file.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import pytest
from services.deck import DeckService
from config.paths import STORY_DB_PATH


# =============================================================================
# BLOCK 3: BODY BLOCK (Functional Scenarios)
# =============================================================================

@pytest.mark.anyio
async def test_complete_deck_builder_workflow_scenario(test_db_path):
    """Simulates a complete player deckbuilding journey."""
    service = DeckService(test_db_path)
    user_id = "builder_player_404"

    # 1. Clean state
    await service.clear_deck(user_id)

    # 2. Add cards
    await service.add_card_to_deck(user_id, 50000101, quantity=3)
    await service.add_card_to_deck(user_id, 50000102, quantity=3)
    await service.add_card_to_deck(user_id, 50000103, quantity=3)

    deck_cards = await service.get_player_deck(user_id)
    assert len(deck_cards) == 3

    # 3. Analyze deck structure
    analysis = service.analyze_deck_structure(deck_cards)
    assert analysis["total_count"] == 9

    # 4. Save to named slot
    slot_name = "Tournament Build"
    ok, saved_name = await service.save_named_deck(user_id, slot_name)
    assert ok is True
    assert saved_name == slot_name

    saved_deck = await service.get_saved_deck(user_id, slot_name)
    assert saved_deck is not None
    assert saved_deck["total_count"] == 9

    # 5. Export to YDK format
    ydk_str = await service.export_player_deck_to_ydk(user_id, deck_title=slot_name)
    assert "#main" in ydk_str
    assert "50000101" in ydk_str

    # 6. Cleanup
    await service.clear_deck(user_id)
    await service.delete_named_deck(user_id, slot_name)


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = ["test_complete_deck_builder_workflow_scenario"]
