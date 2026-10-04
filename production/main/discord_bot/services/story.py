#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story
Description:
    Top-Level Service Translation Unit & Backward Compatibility Bridge.
    Re-exports the modular 4-block Story Campaign architecture from
    services/story/ into the root services namespace.

Architectural Classification:
    Layer 2 (L2) - Service Translation Unit Bridge
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .story import (
    # Constants
    ENCOUNTER_TYPE_AI,
    ENCOUNTER_TYPE_SCRIPTED,
    DEFAULT_STARTING_PLAYER_HP,
    DEFAULT_STARTING_BOSS_HP,
    DEFAULT_STARTING_HAND_SIZE,
    MIN_LEGAL_STORY_MAIN_DECK,
    MAX_LEGAL_STORY_MAIN_DECK,
    MAX_LEGAL_STORY_EXTRA_DECK,
    CHAPTER_1_ID,
    CHAPTER_1_TITLE,
    CHAPTER_2_ID,
    CHAPTER_2_TITLE,
    DEFAULT_STARTING_STAGE,
    DEFAULT_INITIAL_TITLE,
    MIN_COMBAT_DAMAGE,
    MAX_COMBAT_DAMAGE,
    DEFAULT_AI_STRIKE_DAMAGE,
    # Types
    StoryScriptTurnDict,
    StoryScriptDataDict,
    StoryStageDict,
    StoryChapterDict,
    PlayerStoryProgressDict,
    StageCompletionResult,
    ScenarioImportResult,
    # Domain Engines
    fetch_current_chapter,
    fetch_stage,
    fetch_all_stages,
    fetch_or_create_player_progress,
    record_stage_completion,
    reset_player_progress,
    import_chapter_scenario,
    sync_all_scenario_files,
    # Session
    StoryDuelSession,
    # Core Service
    StoryService,
    story_service,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    # Constants
    "ENCOUNTER_TYPE_AI",
    "ENCOUNTER_TYPE_SCRIPTED",
    "DEFAULT_STARTING_PLAYER_HP",
    "DEFAULT_STARTING_BOSS_HP",
    "DEFAULT_STARTING_HAND_SIZE",
    "MIN_LEGAL_STORY_MAIN_DECK",
    "MAX_LEGAL_STORY_MAIN_DECK",
    "MAX_LEGAL_STORY_EXTRA_DECK",
    "CHAPTER_1_ID",
    "CHAPTER_1_TITLE",
    "CHAPTER_2_ID",
    "CHAPTER_2_TITLE",
    "DEFAULT_STARTING_STAGE",
    "DEFAULT_INITIAL_TITLE",
    "MIN_COMBAT_DAMAGE",
    "MAX_COMBAT_DAMAGE",
    "DEFAULT_AI_STRIKE_DAMAGE",
    # Types
    "StoryScriptTurnDict",
    "StoryScriptDataDict",
    "StoryStageDict",
    "StoryChapterDict",
    "PlayerStoryProgressDict",
    "StageCompletionResult",
    "ScenarioImportResult",
    # Domain Engines
    "fetch_current_chapter",
    "fetch_stage",
    "fetch_all_stages",
    "fetch_or_create_player_progress",
    "record_stage_completion",
    "reset_player_progress",
    "import_chapter_scenario",
    "sync_all_scenario_files",
    # Session
    "StoryDuelSession",
    # Core Service
    "StoryService",
    "story_service",
]
