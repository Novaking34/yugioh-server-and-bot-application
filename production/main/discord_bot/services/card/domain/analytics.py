# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.domain.analytics
Description:
    Sub-Block 3.3: Telemetry & Meta Analytics Engine.
    Processes live duel activity, calculates statistical performance ratios,
    archetype evaluations, win-rate rankings, and macro cardpool health summaries.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import aiosqlite
from typing import Optional, List, Dict, Any

from ..foundation.constants import (
    DEFAULT_META_LIMIT,
    EXTRA_DECK_SQL_CONDITION,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Analytics Implementation)
# =============================================================================

async def get_card_usage_stats(db_path: str, card_id: int) -> Dict[str, Any]:
    """
    Fetches comprehensive telemetry stats for a card:
    - Times decked, drawn, played, won, lost.
    - Calculated metrics: total_matches, win_rate (%), play_to_draw_ratio (%).
    - Joined card metadata: name, set_number, card_type, card_subtype, attribute,
      monster_type, archetype, level_or_rank_or_link (as level), scale, rarity.
    If no stats row exists yet, returns initialized zero-counts with card identity.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT s.card_id, s.times_decked, s.times_drawn, s.times_played,
                   s.wins, s.losses, s.last_used_at,
                   c.name, c.set_number, c.card_type, c.card_subtype, c.rarity,
                   c.attribute, c.monster_type, c.archetype,
                   c.level_or_rank_or_link AS level, c.scale
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            WHERE s.card_id = ?
        """, (card_id,))
        row = await cur.fetchone()
        if row:
            data = dict(row)
            total_matches = data["wins"] + data["losses"]
            data["total_matches"] = total_matches
            data["win_rate"] = round((data["wins"] / total_matches * 100), 1) if total_matches > 0 else 0.0
            data["play_to_draw_ratio"] = round((data["times_played"] / data["times_drawn"] * 100), 1) if data["times_drawn"] > 0 else 0.0
            return data

        # If no stats record exists yet, fetch basic card info and return zeros
        cur = await db.execute("""
            SELECT id AS card_id, name, set_number, card_type, card_subtype, rarity,
                   attribute, monster_type, archetype,
                   level_or_rank_or_link AS level, scale
            FROM custom_cards WHERE id = ?
        """, (card_id,))
        card_row = await cur.fetchone()
        if card_row:
            d = dict(card_row)
            d.update({
                "times_decked": 0,
                "times_drawn": 0,
                "times_played": 0,
                "wins": 0,
                "losses": 0,
                "total_matches": 0,
                "last_used_at": None,
                "win_rate": 0.0,
                "play_to_draw_ratio": 0.0,
            })
            return d
        return {}


async def get_meta_overview(
    db_path: str,
    limit: int = DEFAULT_META_LIMIT,
    card_type: Optional[str] = None,
    is_extra_deck: Optional[bool] = None,
    archetype: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns competitive format meta leaderboards across multiple axes:
    1. most_popular: Highest deck inclusions (times_decked DESC, times_played DESC)
    2. most_played: Most frequently summoned/activated in live duels (times_played DESC)
    3. most_victorious: Raw win count leaders (wins DESC)
    4. highest_win_rate: Highest win percentage among cards with >= 3 matches (win_rate DESC)
    5. most_drawn: Most frequently drawn into player hands (times_drawn DESC)
    Supports scoping by card_type, is_extra_deck, and archetype.
    """
    conditions = []
    params: List[Any] = []

    if card_type:
        conditions.append("LOWER(c.card_type) = LOWER(?)")
        params.append(card_type)
    if is_extra_deck is not None:
        if is_extra_deck:
            conditions.append(EXTRA_DECK_SQL_CONDITION)
        else:
            conditions.append(f"NOT {EXTRA_DECK_SQL_CONDITION}")
    if archetype:
        conditions.append("LOWER(c.archetype) = LOWER(?)")
        params.append(archetype)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    def _decorate_rows(rows):
        result = []
        for r in rows:
            d = dict(r)
            total = d.get("wins", 0) + d.get("losses", 0)
            d["total_matches"] = total
            d["win_rate"] = round((d.get("wins", 0) / total * 100), 1) if total > 0 else 0.0
            d["play_to_draw_ratio"] = round((d.get("times_played", 0) / d.get("times_drawn", 1) * 100), 1) if d.get("times_drawn", 0) > 0 else 0.0
            result.append(d)
        return result

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        base_proj = """
            s.card_id, s.times_decked, s.times_drawn, s.times_played, s.wins, s.losses, s.last_used_at,
            c.name, c.set_number, c.card_type, c.card_subtype, c.rarity, c.attribute, c.monster_type, c.archetype
        """

        # 1. Most Popular (by deck inclusions)
        cur = await db.execute(f"""
            SELECT {base_proj}
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            {where_clause}
            ORDER BY s.times_decked DESC, s.times_played DESC, c.id ASC
            LIMIT ?
        """, (*params, limit))
        most_decked = _decorate_rows(await cur.fetchall())

        # 2. Most Played (by on-field summon/activation)
        cur = await db.execute(f"""
            SELECT {base_proj}
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            {where_clause}
            ORDER BY s.times_played DESC, s.times_decked DESC, c.id ASC
            LIMIT ?
        """, (*params, limit))
        most_played = _decorate_rows(await cur.fetchall())

        # 3. Most Victorious (raw win count)
        win_where = f"{where_clause} AND (s.wins + s.losses) > 0" if where_clause else "WHERE (s.wins + s.losses) > 0"
        cur = await db.execute(f"""
            SELECT {base_proj}
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            {win_where}
            ORDER BY s.wins DESC, s.times_played DESC, c.id ASC
            LIMIT ?
        """, (*params, limit))
        most_wins = _decorate_rows(await cur.fetchall())

        # 4. Highest Win Rate (minimum 3 matches to avoid 1-game noise)
        min_matches = 3
        wr_where = f"{where_clause} AND (s.wins + s.losses) >= {min_matches}" if where_clause else f"WHERE (s.wins + s.losses) >= {min_matches}"
        cur = await db.execute(f"""
            SELECT {base_proj}
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            {wr_where}
            ORDER BY (CAST(s.wins AS REAL) / (s.wins + s.losses)) DESC, s.wins DESC, c.id ASC
            LIMIT ?
        """, (*params, limit))
        top_wr = _decorate_rows(await cur.fetchall())

        # 5. Most Drawn
        cur = await db.execute(f"""
            SELECT {base_proj}
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            {where_clause}
            ORDER BY s.times_drawn DESC, s.times_played DESC, c.id ASC
            LIMIT ?
        """, (*params, limit))
        most_drawn = _decorate_rows(await cur.fetchall())

        return {
            "most_popular": most_decked,
            "most_victorious": most_wins,
            "most_played": most_played,
            "highest_win_rate": top_wr,
            "most_drawn": most_drawn,
        }


async def get_card_win_rates(
    db_path: str,
    limit: int = 10,
    min_matches: int = 1,
    card_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns cards ranked by duel win rate percentage with minimum match threshold.
    """
    conditions = ["(s.wins + s.losses) >= ?"]
    params: List[Any] = [min_matches]

    if card_type:
        conditions.append("LOWER(c.card_type) = LOWER(?)")
        params.append(card_type)

    where_clause = f"WHERE {' AND '.join(conditions)}"

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(f"""
            SELECT s.card_id, s.times_decked, s.times_drawn, s.times_played, s.wins, s.losses,
                   c.name, c.set_number, c.card_type, c.card_subtype, c.rarity, c.attribute
            FROM card_usage_stats s
            JOIN custom_cards c ON s.card_id = c.id
            {where_clause}
            ORDER BY (CAST(s.wins AS REAL) / (s.wins + s.losses)) DESC, s.wins DESC, c.id ASC
            LIMIT ?
        """, (*params, limit))
        rows = await cur.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            total = d["wins"] + d["losses"]
            d["total_matches"] = total
            d["win_rate"] = round((d["wins"] / total * 100), 1) if total > 0 else 0.0
            results.append(d)
        return results


async def get_archetype_meta_stats(db_path: str, archetype: str) -> Dict[str, Any]:
    """
    Aggregates meta telemetry across all registered cards in a specific archetype.
    """
    clean = archetype.strip()
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT COUNT(c.id) AS total_cards,
                   COALESCE(SUM(s.times_decked), 0) AS times_decked,
                   COALESCE(SUM(s.times_drawn), 0) AS times_drawn,
                   COALESCE(SUM(s.times_played), 0) AS times_played,
                   COALESCE(SUM(s.wins), 0) AS wins,
                   COALESCE(SUM(s.losses), 0) AS losses
            FROM custom_cards c
            LEFT JOIN card_usage_stats s ON c.id = s.card_id
            WHERE LOWER(c.archetype) = LOWER(?)
        """, (clean,))
        row = await cur.fetchone()
        if not row or row["total_cards"] == 0:
            return {
                "archetype": clean,
                "total_cards": 0,
                "times_decked": 0,
                "times_drawn": 0,
                "times_played": 0,
                "wins": 0,
                "losses": 0,
                "total_matches": 0,
                "win_rate": 0.0,
                "top_card_name": None,
                "top_card_id": None
            }

        data = dict(row)
        total_matches = data["wins"] + data["losses"]
        data["archetype"] = clean
        data["total_matches"] = total_matches
        data["win_rate"] = round((data["wins"] / total_matches * 100), 1) if total_matches > 0 else 0.0

        cur_top = await db.execute("""
            SELECT c.id, c.name, s.wins, s.times_decked
            FROM custom_cards c
            LEFT JOIN card_usage_stats s ON c.id = s.card_id
            WHERE LOWER(c.archetype) = LOWER(?)
            ORDER BY COALESCE(s.wins, 0) DESC, COALESCE(s.times_decked, 0) DESC, c.id ASC
            LIMIT 1
        """, (clean,))
        top_row = await cur_top.fetchone()
        data["top_card_name"] = top_row["name"] if top_row else None
        data["top_card_id"] = top_row["id"] if top_row else None
        return data


async def get_cardpool_telemetry_summary(db_path: str) -> Dict[str, Any]:
    """
    Returns macro server-wide health and activity metrics for the cardpool.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM custom_cards) AS total_registered_cards,
                (SELECT COUNT(*) FROM card_usage_stats WHERE times_decked > 0) AS distinct_cards_decked,
                (SELECT COUNT(*) FROM card_usage_stats WHERE times_drawn > 0) AS distinct_cards_drawn,
                (SELECT COUNT(*) FROM card_usage_stats WHERE times_played > 0) AS distinct_cards_played,
                COALESCE(SUM(times_decked), 0) AS total_deck_inclusions,
                COALESCE(SUM(times_drawn), 0) AS total_card_draws,
                COALESCE(SUM(times_played), 0) AS total_card_plays,
                COALESCE(SUM(wins), 0) AS total_card_wins,
                COALESCE(SUM(losses), 0) AS total_card_losses
            FROM card_usage_stats
        """)
        row = await cur.fetchone()
        return dict(row) if row else {}


async def get_underused_cards(db_path: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Identifies cards with lowest deck inclusion and play activity.
    Useful for community deck ideas and cardpool balance reviews.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT c.id, c.set_number, c.name, c.card_type, c.card_subtype, c.rarity,
                   COALESCE(s.times_decked, 0) AS times_decked,
                   COALESCE(s.times_played, 0) AS times_played
            FROM custom_cards c
            LEFT JOIN card_usage_stats s ON c.id = s.card_id
            ORDER BY COALESCE(s.times_decked, 0) ASC, COALESCE(s.times_played, 0) ASC, c.id ASC
            LIMIT ?
        """, (limit,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "get_card_usage_stats",
    "get_meta_overview",
    "get_card_win_rates",
    "get_archetype_meta_stats",
    "get_cardpool_telemetry_summary",
    "get_underused_cards",
]
