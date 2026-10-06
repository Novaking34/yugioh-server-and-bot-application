#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.bot.services.test_story_service
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Discord Bot Services / Story Campaign Progression & Encounters
Description:
    Unit test suite for StoryService and the story duel engine:
    1. Player story progress tracking, stage completion, and reward distribution.
    2. Modular C-style architecture contracts for services.story.
    3. Scripted encounters and dynamic AI encounters in StoryDuelSession.
    4. Story chapter and stage synchronization from external JSON manifests.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from unittest.mock import MagicMock
import pytest
import aiosqlite

from config.paths import STORY_DB_PATH
from services.story import StoryService
import services.story as story_mod
from services.story.foundation import (
    DEFAULT_STARTING_PLAYER_HP,
    DEFAULT_STARTING_BOSS_HP,
    ENCOUNTER_TYPE_AI,
    ENCOUNTER_TYPE_SCRIPTED,
    CHAPTER_1_ID,
    CHAPTER_2_ID,
)
from services.story.domain import (
    fetch_current_chapter,
    fetch_stage,
    fetch_all_stages,
    fetch_or_create_player_progress,
    record_stage_completion,
    reset_player_progress,
)
from services.story.core import StoryService as CoreStoryService
from services.card import CardService
from services.deck import DeckService
from cogs.story import StoryDuelSession


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Story Progression and Rewards
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_story_service_progression_and_rewards(test_db_path):
    service = StoryService(test_db_path)
    test_uid = "777000001"

    # Reset test user to ensure clean state
    async with aiosqlite.connect(test_db_path) as db:
        await db.execute("DELETE FROM player_story_progress WHERE user_id = ?", (test_uid,))
        await db.commit()

    # 1. Initial Progress
    progress = await service.get_or_create_player_progress(test_uid)
    assert progress["current_chapter_id"] == 1
    assert progress["current_stage_number"] == 1

    # 2. Stage Inspection
    stage1 = await service.get_stage(1, 1)
    assert stage1 is not None
    assert stage1["title"] == "The Quiet Void"
    assert stage1["reward_title"] == "Void Wanderer"
    assert stage1["reward_card_id"] == 50000102

    # 3. Complete Stage 1
    result = await service.complete_stage(test_uid, 1)
    assert result["success"] is True
    assert result["next_stage_number"] == 2
    assert result["reward_title"] == "Void Wanderer"

    # Verify updated player record
    progress_after = await service.get_or_create_player_progress(test_uid)
    assert progress_after["current_stage_number"] == 2


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Modular Architecture Verification
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_story_service_modular_architecture(test_db_path):
    assert DEFAULT_STARTING_PLAYER_HP == 8000
    assert DEFAULT_STARTING_BOSS_HP == 8000
    assert ENCOUNTER_TYPE_AI == "AI"
    assert ENCOUNTER_TYPE_SCRIPTED == "SCRIPTED"

    # Verify domain functions directly
    ch1 = await fetch_current_chapter(test_db_path, CHAPTER_1_ID)
    assert ch1 is not None

    stages = await fetch_all_stages(test_db_path, CHAPTER_1_ID)
    assert len(stages) >= 2

    st1 = await fetch_stage(test_db_path, CHAPTER_1_ID, 1)
    assert st1 is not None
    assert st1["stage_number"] == 1

    # Verify Core Service Facade
    srv = StoryService(test_db_path)
    srv_stages = await srv.get_all_stages(1)
    assert len(srv_stages) == len(stages)

    # Verify root bridge re-exports
    assert hasattr(story_mod, "StoryService")
    assert hasattr(story_mod, "story_service")
    assert hasattr(story_mod, "StoryDuelSession")


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Scripted and Dynamic AI Story Duel Encounters
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_story_duel_session_scripted_and_ai_encounters(test_db_path):
    story_service = StoryService(test_db_path)
    card_service = CardService(test_db_path)
    deck_service = DeckService(test_db_path)

    mock_user = MagicMock()
    mock_user.id = 5550001
    mock_user.display_name = "DuelistPlayer"

    cards = await card_service.get_all_cards()
    player_deck = [c["id"] for c in cards] * 2
    npc_deck = [c["id"] for c in cards] * 2

    # Test Chapter 1 Stage 1: DYNAMIC AI Encounter
    stage1 = await story_service.get_stage(1, 1)
    assert stage1 is not None

    session1 = StoryDuelSession(mock_user, stage1, player_deck, npc_deck)
    assert session1.encounter_type == "AI"

    action_text_ai, dmg_ai = await session1.execute_npc_turn(card_service)
    assert dmg_ai > 0
    assert session1.npc_name in action_text_ai
    assert len(session1.npc_hand) >= 1


# -----------------------------------------------------------------------------
# Sub-Block 3.4: JSON Scenario Synchronization
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_story_json_sync_and_data_loading(test_db_path):
    story_service = StoryService(test_db_path)
    res = await story_service.sync_all_story_files()
    assert res["chapters_synced"] >= 1
    assert res["stages_synced"] >= 2


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_story_service_progression_and_rewards",
    "test_story_service_modular_architecture",
    "test_story_duel_session_scripted_and_ai_encounters",
    "test_story_json_sync_and_data_loading",
]
