#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.core
Description:
    Core Service Orchestrator for The Land of Kustomazi Story RPG Campaign.
    Provides unified facade encapsulating chapter/stage retrieval, player
    campaign progress, reward grants, scenario JSON imports, and story duel sessions.

Architectural Classification:
    Layer 2 (L2) - Core Service Facade
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional, Union

from bot_config import BOT_CONFIG
from production.main.logger import get_logger
from .domain.progress import (
    fetch_or_create_player_progress,
    record_stage_completion,
    reset_player_progress,
)
from .domain.scenarios import (
    import_chapter_scenario,
    sync_all_scenario_files,
)
from .domain.stages import (
    fetch_all_stages,
    fetch_current_chapter,
    fetch_stage,
)
from .foundation.types import (
    PlayerStoryProgressDict,
    ScenarioImportResult,
    StageCompletionResult,
    StoryChapterDict,
    StoryStageDict,
)

logger = get_logger("discord_bot.services.story.core")

# =============================================================================
# BLOCK 3: BODY BLOCK (Core Story Service Facade)
# =============================================================================

class StoryService:
    """Service handling story campaign chapters, stages, NPC profiles, and player progress."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path: str = db_path or BOT_CONFIG["db_path"]

    async def get_or_create_player_progress(self, user_id: str) -> PlayerStoryProgressDict:
        """Fetches active story progress or starts new player at Chapter 1, Stage 1."""
        return await fetch_or_create_player_progress(self.db_path, user_id)

    async def get_current_chapter(self, chapter_id: int = 1) -> Optional[StoryChapterDict]:
        """Retrieves story chapter metadata and associated lore arc."""
        return await fetch_current_chapter(self.db_path, chapter_id)

    async def get_stage(self, chapter_id: int, stage_number: int) -> Optional[StoryStageDict]:
        """Retrieves a specific story stage encounter with NPC dialogue and rewards."""
        return await fetch_stage(self.db_path, chapter_id, stage_number)

    async def get_all_stages(self, chapter_id: int = 1) -> List[StoryStageDict]:
        """Returns all stages belonging to a story chapter."""
        return await fetch_all_stages(self.db_path, chapter_id)

    async def complete_stage(self, user_id: str, stage_number: int) -> StageCompletionResult:
        """
        Marks a story stage completed:
        - Advances player stage pointer
        - Awards stage title and adds reward card copy to player deck
        - Increments story win count
        """
        return await record_stage_completion(self.db_path, user_id, stage_number)

    async def reset_progress(self, user_id: str, stage_number: int = 1) -> bool:
        """Admin recovery function to reset or set player story stage."""
        return await reset_player_progress(self.db_path, user_id, stage_number)

    async def import_chapter_from_json(
        self,
        data_or_path: Union[str, Dict[str, Any]]
    ) -> ScenarioImportResult:
        """
        Parses and imports a story chapter scenario JSON into the database.
        Allows authors and game designers to create story chapters without hardcoding Python.
        """
        return await import_chapter_scenario(self.db_path, data_or_path)

    async def sync_all_story_files(self, story_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans story directory for scenario JSON files and synchronizes all chapters/stages into the database.
        """
        return await sync_all_scenario_files(self.db_path, story_dir)

    # Alias for legacy and convenience
    sync_scenarios_from_json = sync_all_story_files


# Default Singleton Instance
story_service = StoryService()

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "StoryService",
    "story_service",
]
