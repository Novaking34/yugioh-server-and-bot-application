#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.foundation.constants
Description:
    Foundation configuration constants, default starting parameters,
    encounter types, and narrative title definitions for The Land of Kustomazi
    Story Campaign RPG.

Architectural Classification:
    Layer 0 (L0) - Foundation Primitive
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Final, List, Set

# =============================================================================
# BLOCK 3: BODY BLOCK (Constants & Operational Settings)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Story Encounter Types & State Constants
# -----------------------------------------------------------------------------
ENCOUNTER_TYPE_AI: Final[str] = "AI"
ENCOUNTER_TYPE_SCRIPTED: Final[str] = "SCRIPTED"

DEFAULT_STARTING_PLAYER_HP: Final[int] = 8000
DEFAULT_STARTING_BOSS_HP: Final[int] = 8000
SKIRMISH_STARTING_HP: Final[int] = 4000
MIDBOSS_STARTING_HP: Final[int] = 6000
APEX_STARTING_HP: Final[int] = 8000
DEFAULT_STARTING_HAND_SIZE: Final[int] = 5

MIN_LEGAL_STORY_MAIN_DECK: Final[int] = 40
MAX_LEGAL_STORY_MAIN_DECK: Final[int] = 60
MAX_LEGAL_STORY_EXTRA_DECK: Final[int] = 15

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Campaign Chapters & Milestone Constants
# -----------------------------------------------------------------------------
CHAPTER_1_ID: Final[int] = 1
CHAPTER_1_TITLE: Final[str] = "The Genesis of Kustomazi"

CHAPTER_2_ID: Final[int] = 2
CHAPTER_2_TITLE: Final[str] = "The LeSpookiest Night"

DEFAULT_STARTING_STAGE: Final[int] = 1
DEFAULT_INITIAL_TITLE: Final[str] = "Initiate of Kustomazi"

# -----------------------------------------------------------------------------
# Sub-Block 3.3: Combat & AI Simulation Multipliers
# -----------------------------------------------------------------------------
MIN_COMBAT_DAMAGE: Final[int] = 600
MAX_COMBAT_DAMAGE: Final[int] = 2000
DEFAULT_AI_STRIKE_DAMAGE: Final[int] = 800

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
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
]
