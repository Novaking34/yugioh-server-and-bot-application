#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.foundation
Description:
    Foundation Package Translation Unit for the Story Campaign Subsystem.
    Re-exports core constants, default settings, and TypedDict schemas.

Architectural Classification:
    Layer 0 (L0) - Foundation Package
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .constants import (
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
)

from .types import (
    StoryScriptTurnDict,
    StoryScriptDataDict,
    StoryStageDict,
    StoryChapterDict,
    PlayerStoryProgressDict,
    StageCompletionResult,
    ScenarioImportResult,
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
]
