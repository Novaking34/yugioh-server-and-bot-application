#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.functional.test_story_campaign_scenario
Architecture: Hybrid Systems Engineering (Functional Testing Subsystem)
Domain: End-to-End Story Mode / Campaign Journey & Progression Scenario
Description:
    Functional test suite simulating a duelist embarking on the story campaign:
    1. Inspecting Chapter 1 and unlocking Stage 1.
    2. Simulating a scripted/AI duel against the stage boss.
    3. Completing the stage, claiming title and card rewards.
    4. Advancing to Stage 2 with updated campaign progress.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from unittest.mock import MagicMock
import pytest
import aiosqlite

from services.story import StoryService
from services.card import CardService
from cogs.story import StoryDuelSession
from config.paths import STORY_DB_PATH


# =============================================================================
# BLOCK 3: BODY BLOCK (Functional Scenarios)
# =============================================================================

@pytest.mark.anyio
async def test_complete_story_campaign_progression_scenario(test_db_path):
    """Simulates a player progressing through story stage 1 and unlocking stage 2."""
    story_svc = StoryService(test_db_path)
    card_svc = CardService(test_db_path)
    player_id = "story_hero_001"

    # Reset player
    async with aiosqlite.connect(test_db_path) as db:
        await db.execute("DELETE FROM player_story_progress WHERE user_id = ?", (player_id,))
        await db.commit()

    # 1. Player starts campaign
    progress = await story_svc.get_or_create_player_progress(player_id)
    assert progress["current_stage_number"] == 1

    # 2. Inspect Stage 1
    stage_1 = await story_svc.get_stage(1, 1)
    assert stage_1 is not None

    # 3. Simulate Encounter
    cards = await card_svc.get_all_cards()
    deck = [c["id"] for c in cards] * 2
    session = StoryDuelSession(MagicMock(id=player_id, display_name="Hero"), stage_1, deck, deck)
    assert len(session.player_hand) == 5

    # 4. Complete Stage 1
    completion = await story_svc.complete_stage(player_id, 1)
    assert completion["success"] is True
    assert completion["next_stage_number"] == 2
    assert "reward_title" in completion

    # 5. Check updated status
    updated_progress = await story_svc.get_or_create_player_progress(player_id)
    assert updated_progress["current_stage_number"] == 2
    assert updated_progress["highest_stage_completed"] == 1


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = ["test_complete_story_campaign_progression_scenario"]
