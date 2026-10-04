#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.domain.scenarios
Description:
    Domain component managing scenario JSON serialization, validation,
    and automatic synchronization from data/story/*.json files into the SQLite
    story database.

Architectural Classification:
    Layer 1 (L1) - Domain Component
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import glob
import json
import os
from typing import Any, Dict, List, Optional, Union
import aiosqlite

from production.main.logger import get_logger
from ..foundation.types import ScenarioImportResult

logger = get_logger("discord_bot.services.story.scenarios")

# =============================================================================
# BLOCK 3: BODY BLOCK (Scenario Import & Sync Engine)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: JSON Chapter & Stage Ingestion
# -----------------------------------------------------------------------------
async def import_chapter_scenario(
    db_path: str,
    data_or_path: Union[str, Dict[str, Any]]
) -> ScenarioImportResult:
    """
    Parses and imports a story chapter scenario JSON into the database.
    Allows authors and game designers to create story chapters without hardcoding Python.
    """
    if isinstance(data_or_path, str):
        if not os.path.exists(data_or_path):
            raise FileNotFoundError(f"Story scenario file not found: {data_or_path}")
        with open(data_or_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = data_or_path

    chapter_num = data.get("chapter_number", 1)
    chapter_id = data.get("chapter_id", chapter_num)
    title = data.get("title", f"Chapter {chapter_num}")
    arc_id = data.get("arc_id", 1)
    synopsis = data.get("synopsis", "")

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO story_chapters (id, chapter_number, title, arc_id, synopsis)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                chapter_number = excluded.chapter_number,
                title = excluded.title,
                arc_id = excluded.arc_id,
                synopsis = excluded.synopsis
        """, (chapter_id, chapter_num, title, arc_id, synopsis))

        stages_imported = 0
        for stage in data.get("stages", []):
            stage_num = stage.get("stage_number", 1)
            stage_id = stage.get("stage_id") or (chapter_id * 100 + stage_num)
            script_raw = stage.get("script_data")
            script_json_str = json.dumps(script_raw) if (script_raw and not isinstance(script_raw, str)) else script_raw

            await db.execute("""
                INSERT INTO story_stages (
                    id, chapter_id, stage_number, title, intro_dialogue, outro_dialogue,
                    opponent_name, opponent_title, opponent_character_id, opponent_deck_id,
                    encounter_type, boss_hp, script_data, reward_title, reward_card_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    chapter_id = excluded.chapter_id,
                    stage_number = excluded.stage_number,
                    title = excluded.title,
                    intro_dialogue = excluded.intro_dialogue,
                    outro_dialogue = excluded.outro_dialogue,
                    opponent_name = excluded.opponent_name,
                    opponent_title = excluded.opponent_title,
                    opponent_character_id = excluded.opponent_character_id,
                    opponent_deck_id = excluded.opponent_deck_id,
                    encounter_type = excluded.encounter_type,
                    boss_hp = excluded.boss_hp,
                    script_data = excluded.script_data,
                    reward_title = excluded.reward_title,
                    reward_card_id = excluded.reward_card_id
            """, (
                stage_id, chapter_id, stage_num, stage.get("title", ""),
                stage.get("intro_dialogue", ""), stage.get("outro_dialogue", ""),
                stage.get("opponent_name", "Story Opponent"),
                stage.get("opponent_title", "Challenger"),
                stage.get("opponent_character_id", 1),
                stage.get("opponent_deck_id", 1),
                stage.get("encounter_type", "AI"),
                stage.get("boss_hp", 8000),
                script_json_str,
                stage.get("reward_title"),
                stage.get("reward_card_id")
            ))
            stages_imported += 1

        await db.commit()

    logger.info(f"Imported Chapter {chapter_num} ('{title}') with {stages_imported} stages from JSON.")
    return {
        "chapter_id": chapter_id,
        "chapter_number": chapter_num,
        "title": title,
        "stages_imported": stages_imported
    }


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Automated Batch Directory Sync
# -----------------------------------------------------------------------------
async def sync_all_scenario_files(db_path: str, story_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Scans story directory for scenario JSON files and synchronizes all chapters/stages into the database.
    """
    if not story_dir:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        story_dir = os.path.join(base, "data", "story")

    if not os.path.isdir(story_dir):
        return {"chapters_synced": 0, "stages_synced": 0, "files": []}

    json_files = sorted(glob.glob(os.path.join(story_dir, "*.json")))
    total_stages = 0
    synced_files = []

    for fpath in json_files:
        try:
            res = await import_chapter_scenario(db_path, fpath)
            total_stages += res["stages_imported"]
            synced_files.append(os.path.basename(fpath))
        except Exception as e:
            logger.error(f"Error syncing story scenario file {fpath}: {e}")

    logger.info(f"Story synchronization complete: {len(synced_files)} files, {total_stages} stages.")
    return {
        "chapters_synced": len(synced_files),
        "stages_synced": total_stages,
        "files": synced_files
    }


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "import_chapter_scenario",
    "sync_all_scenario_files",
]
