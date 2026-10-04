#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.domain.progress
Description:
    Domain component managing duelist campaign progression, story stage unlocks,
    reward disbursements, unlocked title tracking, and admin progress recovery.

Architectural Classification:
    Layer 1 (L1) - Domain Component
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional
import aiosqlite

from production.main.logger import get_logger
from ..foundation.constants import DEFAULT_INITIAL_TITLE
from ..foundation.types import PlayerStoryProgressDict, StageCompletionResult
from .stages import fetch_stage, fetch_all_stages

logger = get_logger("discord_bot.services.story.progress")

# =============================================================================
# BLOCK 3: BODY BLOCK (Player Progress Lifecycle Operations)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Progress Retrieval & Account Initialization
# -----------------------------------------------------------------------------
async def fetch_or_create_player_progress(db_path: str, user_id: str) -> PlayerStoryProgressDict:
    """Fetches active story progress or starts new player at Chapter 1, Stage 1."""
    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM player_story_progress WHERE user_id = ?", (user_id_str,))
        row = await cur.fetchone()
        if row:
            data = dict(row)
            data["titles_list"] = [t.strip() for t in (data.get("unlocked_titles") or "").split(",") if t.strip()]
            return data

        # Initialize new campaign record
        await db.execute("""
            INSERT INTO player_story_progress (
                user_id, current_chapter_id, current_stage_number, highest_stage_completed, unlocked_titles, total_story_wins
            ) VALUES (?, 1, 1, 0, ?, 0)
        """, (user_id_str, DEFAULT_INITIAL_TITLE))
        await db.commit()

        return {
            "user_id": user_id_str,
            "current_chapter_id": 1,
            "current_stage_number": 1,
            "highest_stage_completed": 0,
            "unlocked_titles": DEFAULT_INITIAL_TITLE,
            "titles_list": [DEFAULT_INITIAL_TITLE],
            "total_story_wins": 0
        }


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Stage Completion & Narrative Rewards
# -----------------------------------------------------------------------------
async def record_stage_completion(
    db_path: str,
    user_id: str,
    stage_number: int
) -> StageCompletionResult:
    """
    Marks a story stage completed:
    - Advances player stage pointer
    - Awards stage title and adds reward card copy to player deck
    - Increments story win count
    """
    progress = await fetch_or_create_player_progress(db_path, user_id)
    current_stage = progress["current_stage_number"]
    chapter_id = progress["current_chapter_id"]

    stage = await fetch_stage(db_path, chapter_id, stage_number)
    if not stage:
        return {"success": False, "error": "Stage not found."}

    new_highest = max(progress.get("highest_stage_completed", 0), stage_number)
    
    # Check total stages in this chapter
    stages = await fetch_all_stages(db_path, chapter_id)
    max_stage = max(s["stage_number"] for s in stages) if stages else 3
    
    next_stage_number = min(stage_number + 1, max_stage) if stage_number < max_stage else stage_number
    is_chapter_cleared = (stage_number >= max_stage)

    # Update titles
    titles_set = set(progress.get("titles_list", []))
    reward_title = stage.get("reward_title")
    new_title_unlocked = False
    if reward_title and reward_title not in titles_set:
        titles_set.add(reward_title)
        new_title_unlocked = True

    updated_titles_str = ", ".join(titles_set)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            UPDATE player_story_progress SET
                current_stage_number = ?,
                highest_stage_completed = ?,
                unlocked_titles = ?,
                total_story_wins = total_story_wins + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (next_stage_number, new_highest, updated_titles_str, str(user_id)))

        # If there's a reward card, ensure it is added to the player's deck collection
        reward_card_id = stage.get("reward_card_id")
        if reward_card_id:
            await db.execute("""
                INSERT INTO player_decks (user_id, card_id, quantity)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = MIN(3, quantity + 1)
            """, (str(user_id), reward_card_id))

        await db.commit()

    logger.info(f"User {user_id} completed Story Stage {stage_number} ({stage.get('title')})")
    return {
        "success": True,
        "stage": stage,
        "next_stage_number": next_stage_number,
        "is_chapter_cleared": is_chapter_cleared,
        "reward_title": reward_title,
        "new_title_unlocked": new_title_unlocked,
        "reward_card_name": stage.get("reward_card_name"),
        "reward_card_set": stage.get("reward_card_set"),
        "outro_dialogue": stage.get("outro_dialogue")
    }


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Admin Progress Reset
# -----------------------------------------------------------------------------
async def reset_player_progress(db_path: str, user_id: str, stage_number: int = 1) -> bool:
    """Admin recovery function to reset or set player story stage."""
    user_id_str = str(user_id)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            UPDATE player_story_progress SET
                current_stage_number = ?,
                highest_stage_completed = MAX(0, ? - 1),
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (stage_number, stage_number, user_id_str))
        await db.commit()
    logger.info(f"Story progress reset for user {user_id} to stage {stage_number}")
    return True


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "fetch_or_create_player_progress",
    "record_stage_completion",
    "reset_player_progress",
]
