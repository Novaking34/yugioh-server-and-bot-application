#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.foundation.types
Description:
    Foundation TypedDict data contracts and type signatures for story chapters,
    stages, scripted dialogues, player progress, and completion results.

Architectural Classification:
    Layer 0 (L0) - Foundation Primitive
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional, TypedDict, Union

# =============================================================================
# BLOCK 3: BODY BLOCK (Type Definitions & Schemas)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Story Stage & Script Contracts
# -----------------------------------------------------------------------------
class StoryScriptTurnDict(TypedDict, total=False):
    play: str
    damage: int
    quote: Optional[str]


class StoryScriptDataDict(TypedDict, total=False):
    turns: Dict[str, StoryScriptTurnDict]
    repeat: Optional[StoryScriptTurnDict]
    threshold_4000: Optional[str]


class StoryStageDict(TypedDict, total=False):
    id: int
    chapter_id: int
    stage_number: int
    title: str
    intro_dialogue: str
    outro_dialogue: str
    opponent_name: str
    opponent_title: Optional[str]
    opponent_character_id: Optional[int]
    opponent_deck_id: Optional[int]
    encounter_type: str
    boss_hp: int
    script_data: Optional[str]
    script: Optional[StoryScriptDataDict]
    reward_title: Optional[str]
    reward_card_id: Optional[int]
    reward_card_name: Optional[str]
    reward_card_set: Optional[str]
    opponent_avatar: Optional[str]
    opponent_deck_name: Optional[str]
    opponent_deck_desc: Optional[str]


class StoryChapterDict(TypedDict, total=False):
    id: int
    chapter_number: int
    title: str
    arc_id: int
    synopsis: str
    arc_title: Optional[str]
    era_or_season: Optional[str]
    stages: Optional[List[StoryStageDict]]


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Player Progress & Campaign Results
# -----------------------------------------------------------------------------
class PlayerStoryProgressDict(TypedDict, total=False):
    user_id: str
    current_chapter_id: int
    current_stage_number: int
    highest_stage_completed: int
    unlocked_titles: str
    titles_list: List[str]
    total_story_wins: int
    updated_at: Optional[str]


class StageCompletionResult(TypedDict, total=False):
    success: bool
    error: Optional[str]
    stage: Optional[StoryStageDict]
    next_stage_number: int
    is_chapter_cleared: bool
    reward_title: Optional[str]
    new_title_unlocked: bool
    reward_card_name: Optional[str]
    reward_card_set: Optional[str]
    outro_dialogue: Optional[str]


class ScenarioImportResult(TypedDict, total=False):
    chapter_id: int
    chapter_number: int
    title: str
    stages_imported: int


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "StoryScriptTurnDict",
    "StoryScriptDataDict",
    "StoryStageDict",
    "StoryChapterDict",
    "PlayerStoryProgressDict",
    "StageCompletionResult",
    "ScenarioImportResult",
]
