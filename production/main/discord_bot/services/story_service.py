#!/usr/bin/env python3
"""
=============================================================================
Story Service: Lore Campaign Progression & Narrative Encounters
=============================================================================
Powers the non-competitive story mode RPG where players progress through
The Land of Kustomazi lore sagas, duel themed NPC bosses, and unlock cards
and narrative duelist titles.
=============================================================================
"""

import aiosqlite
import json
import os
import glob
from typing import Optional, List, Dict, Any, Tuple, Union
from bot_config import BOT_CONFIG
from production.main.logger import get_logger

logger = get_logger("discord_bot.services.story")


class StoryService:
    """Service handling story campaign chapters, stages, NPC profiles, and player progress."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or BOT_CONFIG["db_path"]

    async def get_or_create_player_progress(self, user_id: str) -> Dict[str, Any]:
        """Fetches active story progress or starts new player at Chapter 1, Stage 1."""
        user_id_str = str(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM player_story_progress WHERE user_id = ?", (user_id_str,))
            row = await cur.fetchone()
            if row:
                data = dict(row)
                data["titles_list"] = [t.strip() for t in data["unlocked_titles"].split(",") if t.strip()]
                return data

            # Initialize new campaign record
            await db.execute("""
                INSERT INTO player_story_progress (
                    user_id, current_chapter_id, current_stage_number, highest_stage_completed, unlocked_titles, total_story_wins
                ) VALUES (?, 1, 1, 0, 'Initiate of Kustomazi', 0)
            """, (user_id_str,))
            await db.commit()

            return {
                "user_id": user_id_str,
                "current_chapter_id": 1,
                "current_stage_number": 1,
                "highest_stage_completed": 0,
                "unlocked_titles": "Initiate of Kustomazi",
                "titles_list": ["Initiate of Kustomazi"],
                "total_story_wins": 0
            }

    async def get_current_chapter(self, chapter_id: int = 1) -> Optional[Dict[str, Any]]:
        """Retrieves story chapter metadata and associated lore arc."""
        async with aiosqlite.connect(self.db_path) as db:
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

    async def get_stage(self, chapter_id: int, stage_number: int) -> Optional[Dict[str, Any]]:
        """Retrieves a specific story stage encounter with NPC dialogue and rewards."""
        async with aiosqlite.connect(self.db_path) as db:
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
            data["boss_hp"] = data.get("boss_hp") or 8000
            data["encounter_type"] = data.get("encounter_type") or "AI"
            if data.get("script_data"):
                try:
                    import json
                    data["script"] = json.loads(data["script_data"])
                except Exception as e:
                    logger.warning(f"Failed to parse script_data for stage {stage_number}: {e}")
                    data["script"] = None
            else:
                data["script"] = None
            return data


    async def get_all_stages(self, chapter_id: int = 1) -> List[Dict[str, Any]]:
        """Returns all stages belonging to a story chapter."""
        async with aiosqlite.connect(self.db_path) as db:
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

    async def complete_stage(self, user_id: str, stage_number: int) -> Dict[str, Any]:
        """
        Marks a story stage completed:
        - Advances player stage pointer
        - Awards stage title and adds reward card copy to player deck
        - Increments story win count
        """
        progress = await self.get_or_create_player_progress(user_id)
        current_stage = progress["current_stage_number"]
        chapter_id = progress["current_chapter_id"]

        stage = await self.get_stage(chapter_id, stage_number)
        if not stage:
            return {"success": False, "error": "Stage not found."}

        new_highest = max(progress["highest_stage_completed"], stage_number)
        
        # Check total stages in this chapter
        stages = await self.get_all_stages(chapter_id)
        max_stage = max(s["stage_number"] for s in stages) if stages else 3
        
        next_stage_number = min(stage_number + 1, max_stage) if stage_number < max_stage else stage_number
        is_chapter_cleared = (stage_number >= max_stage)

        # Update titles
        titles_set = set(progress["titles_list"])
        reward_title = stage.get("reward_title")
        new_title_unlocked = False
        if reward_title and reward_title not in titles_set:
            titles_set.add(reward_title)
            new_title_unlocked = True

        updated_titles_str = ", ".join(titles_set)

        async with aiosqlite.connect(self.db_path) as db:
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

        logger.info(f"User {user_id} completed Story Stage {stage_number} ({stage['title']})")
        return {
            "success": True,
            "stage": stage,
            "next_stage_number": next_stage_number,
            "is_chapter_cleared": is_chapter_cleared,
            "reward_title": reward_title,
            "new_title_unlocked": new_title_unlocked,
            "reward_card_name": stage.get("reward_card_name"),
            "reward_card_set": stage.get("reward_card_set"),
            "outro_dialogue": stage["outro_dialogue"]
        }


    async def reset_progress(self, user_id: str, stage_number: int = 1) -> bool:
        """Admin recovery function to reset or set player story stage."""
        user_id_str = str(user_id)
        async with aiosqlite.connect(self.db_path) as db:
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

    async def import_chapter_from_json(self, data_or_path: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
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

        async with aiosqlite.connect(self.db_path) as db:
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

    async def sync_all_story_files(self, story_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans story directory for scenario JSON files and synchronizes all chapters/stages into the database.
        """
        if not story_dir:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            story_dir = os.path.join(base, "data", "story")

        if not os.path.isdir(story_dir):
            return {"chapters_synced": 0, "stages_synced": 0, "files": []}

        json_files = sorted(glob.glob(os.path.join(story_dir, "*.json")))
        total_stages = 0
        synced_files = []

        for fpath in json_files:
            try:
                res = await self.import_chapter_from_json(fpath)
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
