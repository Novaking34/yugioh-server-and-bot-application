#!/usr/bin/env python3
"""
=============================================================================
Rating Service: ELO Engine, Competitive Tiers & Leaderboards
=============================================================================
Provides FIDE-standard Elo rating calculations, tier progression, win-streak
telemetry, competitive match recording, and leaderboards.
=============================================================================
"""

import math
import aiosqlite
from typing import Optional, List, Dict, Any, Tuple
from bot_config import BOT_CONFIG
from production.main.logger import get_logger

logger = get_logger("discord_bot.services.rating")

TIER_BRACKETS = [
    (2100, "King of Games", "👑", 0xFFD700),
    (1900, "Diamond Duelist", "💠", 0x00E5FF),
    (1700, "Platinum Duelist", "💎", 0x00E676),
    (1500, "Gold Duelist", "🥇", 0xF59E0B),
    (1300, "Silver Duelist", "🥈", 0x94A3B8),
    (1100, "Bronze Duelist", "🥉", 0xCD7F32),
    (0,    "Novice Duelist", "🔰", 0x6B7280),
]


class RatingService:
    """Service handling competitive Elo ratings, tier classification, and match history."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or BOT_CONFIG["db_path"]

    @staticmethod
    def get_tier_info(elo: int) -> Tuple[str, str, int]:
        """Returns (tier_name, badge_icon, embed_color) for a given Elo rating."""
        for min_elo, name, badge, color in TIER_BRACKETS:
            if elo >= min_elo:
                return name, badge, color
        return "Novice Duelist", "🔰", 0x6B7280

    async def get_or_create_player(self, user_id: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves player rating profile or initializes new entry with baseline 1200 Elo."""
        user_id_str = str(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM player_ratings WHERE user_id = ?", (user_id_str,))
            row = await cur.fetchone()
            if row:
                data = dict(row)
                if username and data.get("username") != username:
                    await db.execute("UPDATE player_ratings SET username = ? WHERE user_id = ?", (username, user_id_str))
                    await db.commit()
                    data["username"] = username
                return data

            # Initialize new duelist profile
            default_elo = 1200
            tier_name, _, _ = self.get_tier_info(default_elo)
            display_name = username or f"Duelist_{user_id_str[:6]}"

            await db.execute("""
                INSERT INTO player_ratings (
                    user_id, username, elo, wins, losses, draws, win_streak, highest_streak, highest_elo, tier, season_id
                ) VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?, ?, 'Season 1')
            """, (user_id_str, display_name, default_elo, default_elo, tier_name))
            await db.commit()

            return {
                "user_id": user_id_str,
                "username": display_name,
                "elo": default_elo,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "win_streak": 0,
                "highest_streak": 0,
                "highest_elo": default_elo,
                "tier": tier_name,
                "season_id": "Season 1"
            }

    @staticmethod
    def compute_elo_change(p1_elo: int, p2_elo: int, p1_score: float, p1_matches: int = 15, p2_matches: int = 15) -> Tuple[int, int]:
        """
        Calculates new Elo ratings using standard logistic Elo formula.
        p1_score: 1.0 (P1 win), 0.5 (Draw), 0.0 (P1 loss).
        """
        k1 = 40 if p1_matches < 10 else 32
        k2 = 40 if p2_matches < 10 else 32

        expected_p1 = 1.0 / (1.0 + 10.0 ** ((p2_elo - p1_elo) / 400.0))
        expected_p2 = 1.0 - expected_p1
        p2_score = 1.0 - p1_score

        new_p1 = max(100, round(p1_elo + k1 * (p1_score - expected_p1)))
        new_p2 = max(100, round(p2_elo + k2 * (p2_score - expected_p2)))

        return new_p1, new_p2

    async def record_duel_match(
        self,
        p1_id: str,
        p2_id: str,
        winner_id: Optional[str],
        match_type: str = "RANKED",
        turns: int = 1,
        summary: str = "",
        p1_deck: Optional[List[int]] = None,
        p2_deck: Optional[List[int]] = None,
        p1_name: Optional[str] = None,
        p2_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes a concluded match:
        - Updates Elo and stats for both players if RANKED.
        - Updates win/loss telemetry in card_usage_stats.
        - Records match in duel_matches.
        """
        p1 = await self.get_or_create_player(p1_id, p1_name)
        p2 = await self.get_or_create_player(p2_id, p2_name)

        p1_elo_before = p1["elo"]
        p2_elo_before = p2["elo"]
        p1_elo_after = p1_elo_before
        p2_elo_after = p2_elo_before

        is_draw = (winner_id is None or winner_id == "DRAW")
        is_p1_win = (winner_id == str(p1_id))
        is_p2_win = (winner_id == str(p2_id))

        if match_type.upper() == "RANKED":
            p1_total = p1["wins"] + p1["losses"] + p1["draws"]
            p2_total = p2["wins"] + p2["losses"] + p2["draws"]

            if is_draw:
                score = 0.5
            elif is_p1_win:
                score = 1.0
            else:
                score = 0.0

            p1_elo_after, p2_elo_after = self.compute_elo_change(
                p1_elo_before, p2_elo_before, score, p1_total, p2_total
            )

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Update Player 1
            p1_tier, _, _ = self.get_tier_info(p1_elo_after)
            p1_streak = (p1["win_streak"] + 1) if is_p1_win else 0
            p1_highest_streak = max(p1["highest_streak"], p1_streak)
            p1_highest_elo = max(p1["highest_elo"], p1_elo_after)

            await db.execute("""
                UPDATE player_ratings SET
                    elo = ?,
                    wins = wins + ?,
                    losses = losses + ?,
                    draws = draws + ?,
                    win_streak = ?,
                    highest_streak = ?,
                    highest_elo = ?,
                    tier = ?,
                    last_match_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                p1_elo_after,
                1 if is_p1_win else 0,
                1 if is_p2_win else 0,
                1 if is_draw else 0,
                p1_streak,
                p1_highest_streak,
                p1_highest_elo,
                p1_tier,
                str(p1_id)
            ))

            # 2. Update Player 2
            p2_tier, _, _ = self.get_tier_info(p2_elo_after)
            p2_streak = (p2["win_streak"] + 1) if is_p2_win else 0
            p2_highest_streak = max(p2["highest_streak"], p2_streak)
            p2_highest_elo = max(p2["highest_elo"], p2_elo_after)

            await db.execute("""
                UPDATE player_ratings SET
                    elo = ?,
                    wins = wins + ?,
                    losses = losses + ?,
                    draws = draws + ?,
                    win_streak = ?,
                    highest_streak = ?,
                    highest_elo = ?,
                    tier = ?,
                    last_match_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                p2_elo_after,
                1 if is_p2_win else 0,
                1 if is_p1_win else 0,
                1 if is_draw else 0,
                p2_streak,
                p2_highest_streak,
                p2_highest_elo,
                p2_tier,
                str(p2_id)
            ))

            # 3. Record Match History
            cur = await db.execute("""
                INSERT INTO duel_matches (
                    match_type, p1_user_id, p2_user_id, winner_user_id,
                    p1_elo_before, p1_elo_after, p2_elo_before, p2_elo_after,
                    turns, summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_type.upper(), str(p1_id), str(p2_id),
                winner_id or "DRAW",
                p1_elo_before, p1_elo_after, p2_elo_before, p2_elo_after,
                turns, summary
            ))
            match_id = cur.lastrowid

            # 4. Telemetry: Update card wins/losses
            if p1_deck:
                unique_p1 = set(p1_deck)
                for cid in unique_p1:
                    await db.execute("""
                        INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(card_id) DO UPDATE SET
                            wins = wins + ?,
                            losses = losses + ?,
                            last_used_at = CURRENT_TIMESTAMP
                    """, (cid, 1 if is_p1_win else 0, 1 if is_p2_win else 0,
                          1 if is_p1_win else 0, 1 if is_p2_win else 0))

            if p2_deck:
                unique_p2 = set(p2_deck)
                for cid in unique_p2:
                    await db.execute("""
                        INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(card_id) DO UPDATE SET
                            wins = wins + ?,
                            losses = losses + ?,
                            last_used_at = CURRENT_TIMESTAMP
                    """, (cid, 1 if is_p2_win else 0, 1 if is_p1_win else 0,
                          1 if is_p2_win else 0, 1 if is_p1_win else 0))

            await db.commit()

        logger.info(f"Recorded {match_type} duel #{match_id}: P1 {p1_elo_before}->{p1_elo_after}, P2 {p2_elo_before}->{p2_elo_after}")
        return {
            "match_id": match_id,
            "match_type": match_type.upper(),
            "p1_id": p1_id,
            "p2_id": p2_id,
            "p1_elo_before": p1_elo_before,
            "p1_elo_after": p1_elo_after,
            "p1_elo_delta": p1_elo_after - p1_elo_before,
            "p2_elo_before": p2_elo_before,
            "p2_elo_after": p2_elo_after,
            "p2_elo_delta": p2_elo_after - p2_elo_before,
            "winner_id": winner_id or "DRAW",
        }

    async def get_leaderboard(self, limit: int = 10, season_id: str = "Season 1") -> List[Dict[str, Any]]:
        """Returns the top duelists ordered by ELO."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT user_id, username, elo, wins, losses, draws, win_streak, highest_elo, tier
                FROM player_ratings
                WHERE season_id = ?
                ORDER BY elo DESC, wins DESC
                LIMIT ?
            """, (season_id, limit))
            rows = await cur.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                total = d["wins"] + d["losses"] + d["draws"]
                d["win_rate"] = round((d["wins"] / total * 100), 1) if total > 0 else 0.0
                results.append(d)
            return results
