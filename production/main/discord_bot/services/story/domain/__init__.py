#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.domain
Description:
    Domain Package Translation Unit for the Story Campaign Subsystem.
    Re-exports stages, progress, scenarios, and StoryDuelSession engine.

Architectural Classification:
    Layer 1 (L1) - Domain Package
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .stages import (
    fetch_current_chapter,
    fetch_stage,
    fetch_all_stages,
)

from .progress import (
    fetch_or_create_player_progress,
    record_stage_completion,
    reset_player_progress,
)

from .scenarios import (
    import_chapter_scenario,
    sync_all_scenario_files,
)

from .session import (
    StoryDuelSession,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    # Stages
    "fetch_current_chapter",
    "fetch_stage",
    "fetch_all_stages",
    # Progress
    "fetch_or_create_player_progress",
    "record_stage_completion",
    "reset_player_progress",
    # Scenarios
    "import_chapter_scenario",
    "sync_all_scenario_files",
    # Session
    "StoryDuelSession",
]
