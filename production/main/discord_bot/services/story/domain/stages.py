#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.domain.stages
Description:
    Domain component managing story chapters and stages. Provides database
    queries for active lore arcs, NPC opponent profiles, reward details,
    and JSON scripted encounter events.

Architectural Classification:
    Layer 1 (L1) - Domain Component
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import json
from typing import Any, Dict, List, Optional
import aiosqlite

from production.main.logger import get_logger
from ..foundation.constants import DEFAULT_STARTING_BOSS_HP, ENCOUNTER_TYPE_AI
from ..foundation.types import StoryChapterDict, StoryStageDict

logger = get_logger("discord_bot.services.story.stages")

# =============================================================================
# BLOCK 3: BODY BLOCK (Chapter & Stage Query Engine)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Chapter Retrieval
# -----------------------------------------------------------------------------
async def fetch_current_chapter(db_path: str, chapter_id: int = 1) -> Optional[StoryChapterDict]:
    """Retrieves story chapter metadata and associated lore arc."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT c.*, a.title AS arc_title, a.era_or_season
            FROM story_chapters c
            LEFT JOIN lore_arcs a ON c.arc_id = a.id
            WHERE c.id = ? OR c.chapter_number = ?
            LIMIT 1
        """, (chapter_id, chapter_id))
        row = await cur.fetchone()
        return dict(row) if row else None


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Single Stage Query with NPC & Script Parsing
# -----------------------------------------------------------------------------
async def fetch_stage(db_path: str, chapter_id: int, stage_number: int) -> Optional[StoryStageDict]:
    """Retrieves a specific story stage encounter with NPC dialogue, deck, and rewards."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT s.*, 
                   c.name AS reward_card_name, c.set_number AS reward_card_set,
                   ch.avatar_url AS opponent_avatar,
                   d.name AS opponent_deck_name, d.description AS opponent_deck_desc
            FROM story_stages s
            LEFT JOIN custom_cards c ON s.reward_card_id = c.id
            LEFT JOIN characters ch ON s.opponent_character_id = ch.id
            LEFT JOIN decks d ON s.opponent_deck_id = d.id
            WHERE s.chapter_id = ? AND s.stage_number = ?
            LIMIT 1
        """, (chapter_id, stage_number))
        row = await cur.fetchone()
        if not row:
            return None
        data = dict(row)
        data["boss_hp"] = data.get("boss_hp") or DEFAULT_STARTING_BOSS_HP
        data["encounter_type"] = (data.get("encounter_type") or ENCOUNTER_TYPE_AI).upper()
        if data.get("script_data"):
            try:
                data["script"] = json.loads(data["script_data"])
            except Exception as e:
                logger.warning(f"Failed to parse script_data for stage {stage_number}: {e}")
                data["script"] = None
        else:
            data["script"] = None
        return data


# -----------------------------------------------------------------------------
# Sub-Block 3.3: All Stages Query for Chapter
# -----------------------------------------------------------------------------
async def fetch_all_stages(db_path: str, chapter_id: int = 1) -> List[StoryStageDict]:
    """Returns all stages belonging to a story chapter in chronological order."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT s.*, c.name AS reward_card_name, c.set_number AS reward_card_set
            FROM story_stages s
            LEFT JOIN custom_cards c ON s.reward_card_id = c.id
            WHERE s.chapter_id = ?
            ORDER BY s.stage_number ASC
        """, (chapter_id,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "fetch_current_chapter",
    "fetch_stage",
    "fetch_all_stages",
]
