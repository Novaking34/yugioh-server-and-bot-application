# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card_service
Description:
    Core Custom Card Discovery, Autocomplete & Live Duel Telemetry Engine.
    Encapsulates all database operations for Set 1: The Land of Kustomazi cards,
    fuzzy search queries, Duelingbook metadata lookups, faction/character lore
    relations, and card usage telemetry.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Imports, Type Contracts & Logger)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Inclusions & Imports
# -----------------------------------------------------------------------------
import aiosqlite
from typing import Optional, List, Dict, Any, Tuple, TypedDict, Final, Union
from bot_config import BOT_CONFIG
from production.main.logger import get_logger

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Subsystem Logger
# -----------------------------------------------------------------------------
logger = get_logger("discord_bot.services.card")

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Query Limits (Discord autocomplete / select menus cap at 25)
# -----------------------------------------------------------------------------
DEFAULT_AUTOCOMPLETE_LIMIT: Final[int] = 20   # /card autocomplete suggestions
DEFAULT_RECENT_LIMIT: Final[int] = 10         # /recent newest additions
DEFAULT_META_LIMIT: Final[int] = 5            # /meta top-N leaderboards

# -----------------------------------------------------------------------------
# Sub-Block 2.4: Card Identity Vocabulary (mirrors schema.sql custom_cards)
# -----------------------------------------------------------------------------
# Primary card frames (custom_cards.card_type)
CARD_TYPE_MONSTER: Final[str] = "Monster"
CARD_TYPE_SPELL: Final[str] = "Spell"
CARD_TYPE_TRAP: Final[str] = "Trap"
CARD_TYPES: Final[Tuple[str, ...]] = (CARD_TYPE_MONSTER, CARD_TYPE_SPELL, CARD_TYPE_TRAP)

# Monster attributes (custom_cards.attribute)
CARD_ATTRIBUTES: Final[Tuple[str, ...]] = ("DARK", "LIGHT", "EARTH", "WATER", "FIRE", "WIND", "DIVINE")

# Stat sentinel: schema stores "?" ATK/DEF as -2. The duel engine must treat
# this as unknown/variable rather than as a negative battle value.
STAT_UNKNOWN: Final[int] = -2

# -----------------------------------------------------------------------------
# Sub-Block 2.5: Canonical Card Projection (single SELECT shape for one card)
# -----------------------------------------------------------------------------
# Every full-card read should return this shape so all consumers (duel engine,
# deck engine, embeds, story NPCs) see identical keys. `level` is an alias of
# level_or_rank_or_link because the duel engine's tribute logic reads "level".
CARD_RECORD_PROJECTION: Final[str] = """
    c.*,
    c.level_or_rank_or_link AS level,
    f.name  AS faction_name,
    ch.name AS character_name
"""
CARD_RECORD_JOINS: Final[str] = """
    FROM custom_cards c
    LEFT JOIN factions   f  ON c.faction_id = f.id
    LEFT JOIN characters ch ON c.signature_character_id = ch.id
"""

# -----------------------------------------------------------------------------
# Sub-Block 2.6: Telemetry Counter Manifest (card_usage_stats columns owned here)
# -----------------------------------------------------------------------------
TELEMETRY_COUNTERS: Final[Tuple[str, ...]] = (
    "times_decked",   # Included in player decks (deck engine lifecycle)
    "times_drawn",    # Drawn during live duels
    "times_played",   # Summoned / activated during live duels
    "wins",           # Matches won while in the active deck
    "losses",         # Matches lost while in the active deck
)

# -----------------------------------------------------------------------------
# Sub-Block 2.7: Type Contracts
# -----------------------------------------------------------------------------
# Functional TypedDict syntax is required because the real column is named
# `def` (a Python keyword) — the contract must match the row keys exactly.
CardRecordDict = TypedDict("CardRecordDict", {
    # Identity
    "id": int,                              # 8-digit passcode (e.g. 50000101)
    "name": str,
    "set_number": Optional[str],            # e.g. TLOK-001
    "set_code": Optional[str],              # e.g. TLOK
    # Frame & Classification
    "card_type": str,                       # Monster | Spell | Trap
    "card_subtype": Optional[str],          # Normal, Effect, Ritual, Fusion, Synchro, Xyz, Link, Pendulum, Field...
    "attribute": Optional[str],
    "monster_type": Optional[str],          # Species / race (Warrior, Dragon, ...)
    "archetype": Optional[str],
    # Battle Stats
    "level_or_rank_or_link": Optional[int],
    "level": Optional[int],                 # Alias of level_or_rank_or_link (duel engine tributes)
    "scale": Optional[int],                 # Pendulum scale 0-13
    "atk": Optional[int],                   # STAT_UNKNOWN (-2) == "?"
    "def": Optional[int],                   # STAT_UNKNOWN (-2) == "?"; NULL for Link monsters
    "link_arrows": Optional[str],           # Comma-separated, e.g. "BL,BR,T"
    # Rules Text
    "effect_text": str,
    "pendulum_effect": Optional[str],
    # Legality & Release
    "rarity": Optional[str],
    "banlist_status": Optional[str],        # Unlimited | Semi-Limited | Limited | Forbidden
    "playtesting_status": Optional[str],
    # Scripting (EDOPro / Project Ignis)
    "script_file": Optional[str],
    "script_status": Optional[str],         # Implemented | Draft | Stub | Vanilla
    # Assets & External Integration
    "image_url": Optional[str],
    "local_image_path": Optional[str],
    "duelingbook_id": Optional[str],
    "duelingbook_url": Optional[str],
    "creator_name": Optional[str],
    # Story & Lore Relations
    "lore_text": Optional[str],
    "story_significance": Optional[str],
    "faction_id": Optional[int],
    "faction_name": Optional[str],          # Joined from factions
    "signature_character_id": Optional[int],
    "character_name": Optional[str],        # Joined from characters
    # Audit
    "created_at": Optional[str],
}, total=False)


class CardSummaryDict(TypedDict, total=False):
    """Lightweight card shape for autocomplete and recent-additions lists."""
    id: int
    set_number: Optional[str]
    name: str
    card_type: str
    card_subtype: Optional[str]
    rarity: Optional[str]
    created_at: Optional[str]


class CardUsageStatsDict(TypedDict, total=False):
    """card_usage_stats row joined with card identity, plus derived win_rate."""
    card_id: int
    name: str
    set_number: Optional[str]
    card_type: str
    card_subtype: Optional[str]
    rarity: Optional[str]
    times_decked: int
    times_drawn: int
    times_played: int
    wins: int
    losses: int
    last_used_at: Optional[str]
    win_rate: float                          # Derived: wins / (wins + losses) * 100


class MetaOverviewDict(TypedDict):
    """Format meta snapshot. NOTE: most_victorious currently ranks by raw wins."""
    most_popular: List[CardUsageStatsDict]
    most_victorious: List[CardUsageStatsDict]


# =============================================================================
# BLOCK 3: BODY BLOCK (Core CardService Engine Translation Unit)
# =============================================================================

class CardService:
    """Service handling card retrieval, search, and usage telemetry."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or BOT_CONFIG["db_path"]

    # -------------------------------------------------------------------------
    # 3.1 Card Discovery & Direct Lookups
    # -------------------------------------------------------------------------

    async def get_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """
        Direct O(1) indexed lookup for a single card by its 8-digit passcode ID.
        Returns the canonical CARD_RECORD_PROJECTION or None if not found.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(f"""
                SELECT {CARD_RECORD_PROJECTION}
                {CARD_RECORD_JOINS}
                WHERE c.id = ?
                LIMIT 1
            """, (card_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_card_by_query(self, query: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Retrieves a custom card by exact or prioritized fuzzy match across:
        1. Passcode ID (e.g. 50000101)
        2. Set Number (e.g. TLOK-001)
        3. Exact Name (case-insensitive)
        4. Name Prefix or Substring
        Gracefully handles composite autocomplete labels (e.g. "TLOK-001 | The Great Kasutamaiza").
        """
        raw_str = str(query).strip()
        if not raw_str:
            return None

        # Sanitize composite labels e.g. "TLOK-001 | Card Name"
        if " | " in raw_str:
            parts = [p.strip() for p in raw_str.split(" | ") if p.strip()]
            for part in parts:
                found = await self.get_card_by_query(part)
                if found:
                    return found

        # Sanitize bracketed labels e.g. "[50000101] Card Name"
        if raw_str.startswith("[") and "]" in raw_str:
            bracket_val = raw_str[1:raw_str.index("]")].strip()
            if bracket_val.isdigit():
                found = await self.get_card_by_id(int(bracket_val))
                if found:
                    return found
            rest = raw_str[raw_str.index("]") + 1:].strip()
            if rest:
                found = await self.get_card_by_query(rest)
                if found:
                    return found

        # Fast path: numeric string lookup directly by passcode
        if raw_str.isdigit():
            found = await self.get_card_by_id(int(raw_str))
            if found:
                return found

        query_clean = raw_str
        like_pattern = f"%{query_clean}%"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(f"""
                SELECT {CARD_RECORD_PROJECTION}
                {CARD_RECORD_JOINS}
                WHERE LOWER(c.name) = LOWER(?)
                   OR LOWER(c.set_number) = LOWER(?)
                   OR CAST(c.id AS TEXT) = ?
                   OR LOWER(c.name) LIKE LOWER(?)
                   OR LOWER(c.set_number) LIKE LOWER(?)
                ORDER BY
                    CASE
                        WHEN LOWER(c.name) = LOWER(?) THEN 1
                        WHEN LOWER(c.set_number) = LOWER(?) THEN 2
                        WHEN CAST(c.id AS TEXT) = ? THEN 3
                        WHEN LOWER(c.name) LIKE LOWER(?) || '%' THEN 4
                        WHEN LOWER(c.set_number) LIKE LOWER(?) || '%' THEN 5
                        WHEN LOWER(c.name) LIKE '% ' || LOWER(?) || '%' THEN 6
                        ELSE 7
                    END,
                    c.id ASC
                LIMIT 1
            """, (
                query_clean, query_clean, query_clean, like_pattern, like_pattern,
                query_clean, query_clean, query_clean, query_clean, query_clean, query_clean
            ))
            row = await cur.fetchone()
            if row:
                return dict(row)
        return None

    async def get_cards_by_filter(
        self,
        card_type: Optional[str] = None,
        card_subtype: Optional[str] = None,
        attribute: Optional[str] = None,
        archetype: Optional[str] = None,
        monster_type: Optional[str] = None,
        rarity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Discovers cards matching multiple optional filter criteria
        (card_type, subtype, attribute, archetype, monster_type/race, rarity).
        """
        conditions = []
        params: List[Any] = []

        if card_type:
            conditions.append("LOWER(c.card_type) = LOWER(?)")
            params.append(card_type)
        if card_subtype:
            conditions.append("LOWER(c.card_subtype) LIKE LOWER(?)")
            params.append(f"%{card_subtype}%")
        if attribute:
            conditions.append("UPPER(c.attribute) = UPPER(?)")
            params.append(attribute)
        if archetype:
            conditions.append("LOWER(c.archetype) = LOWER(?)")
            params.append(archetype)
        if monster_type:
            conditions.append("LOWER(c.monster_type) = LOWER(?)")
            params.append(monster_type)
        if rarity:
            conditions.append("LOWER(c.rarity) = LOWER(?)")
            params.append(rarity)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        limit_clause = f"LIMIT {int(limit)}" if limit and limit > 0 else ""

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(f"""
                SELECT {CARD_RECORD_PROJECTION}
                {CARD_RECORD_JOINS}
                {where_clause}
                ORDER BY c.id ASC
                {limit_clause}
            """, params)
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # 3.2 Real-time Autocomplete Engine
    # -------------------------------------------------------------------------

    async def search_cards(
        self,
        current: str,
        limit: int = DEFAULT_AUTOCOMPLETE_LIMIT
    ) -> List[Dict[str, Any]]:
        """
        Returns ranked matching card suggestions for real-time Discord autocomplete.
        Prioritizes:
        1. Exact Match (Name, Set Number, Passcode)
        2. Prefix Name Match (e.g. "Kas..." -> "Kasutamaiza...")
        3. Prefix Set Number Match (e.g. "TLOK..." -> "TLOK-001...")
        4. Word-Boundary Match (e.g. "Creator" -> "Kasutamaiza, the Creator of Kustomazi")
        5. General Substring Match
        When query is empty, yields cards in canonical Set order (TLOK-001, TLOK-002...).
        """
        clean = current.strip()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if clean:
                like_pattern = f"%{clean}%"
                cur = await db.execute("""
                    SELECT id, set_number, name, card_type, card_subtype, rarity, attribute
                    FROM custom_cards
                    WHERE LOWER(name) LIKE LOWER(?) 
                       OR LOWER(set_number) LIKE LOWER(?) 
                       OR CAST(id AS TEXT) LIKE ?
                    ORDER BY
                        CASE
                            WHEN LOWER(name) = LOWER(?) THEN 1
                            WHEN LOWER(set_number) = LOWER(?) THEN 2
                            WHEN CAST(id AS TEXT) = ? THEN 3
                            WHEN LOWER(name) LIKE LOWER(?) || '%' THEN 4
                            WHEN LOWER(set_number) LIKE LOWER(?) || '%' THEN 5
                            WHEN LOWER(name) LIKE '% ' || LOWER(?) || '%' THEN 6
                            ELSE 7
                        END,
                        id ASC
                    LIMIT ?
                """, (
                    like_pattern, like_pattern, like_pattern,
                    clean, clean, clean, clean, clean, clean,
                    limit
                ))
            else:
                cur = await db.execute("""
                    SELECT id, set_number, name, card_type, card_subtype, rarity, attribute
                    FROM custom_cards
                    ORDER BY 
                        CASE WHEN set_number IS NOT NULL THEN 0 ELSE 1 END,
                        set_number ASC,
                        id ASC
                    LIMIT ?
                """, (limit,))

            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_all_cards(self) -> List[Dict[str, Any]]:
        """Returns all registered custom cards in Set 1."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(f"""
                SELECT {CARD_RECORD_PROJECTION}
                {CARD_RECORD_JOINS}
                ORDER BY c.id ASC
            """)
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_random_card(self, card_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Selects a random card from the active pool, optionally filtered by card_type."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if card_type:
                cur = await db.execute(f"""
                    SELECT {CARD_RECORD_PROJECTION}
                    {CARD_RECORD_JOINS}
                    WHERE LOWER(c.card_type) = LOWER(?)
                    ORDER BY RANDOM() LIMIT 1
                """, (card_type,))
            else:
                cur = await db.execute(f"""
                    SELECT {CARD_RECORD_PROJECTION}
                    {CARD_RECORD_JOINS}
                    ORDER BY RANDOM() LIMIT 1
                """)
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_recent_cards(self, limit: int = DEFAULT_RECENT_LIMIT) -> List[Dict[str, Any]]:
        """Returns recently added custom cards with summary identity."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT id, set_number, name, card_type, card_subtype, rarity, created_at
                FROM custom_cards
                ORDER BY created_at DESC, id DESC LIMIT ?
            """, (limit,))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # 3.3 Telemetry & Meta Analytics Engine
    # -------------------------------------------------------------------------

    async def get_card_usage_stats(self, card_id: int) -> Dict[str, Any]:
        """Fetches telemetry stats (times decked, drawn, played, win rate) for a card."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT s.*, c.name, c.set_number, c.card_type, c.card_subtype, c.rarity
                FROM card_usage_stats s
                JOIN custom_cards c ON s.card_id = c.id
                WHERE s.card_id = ?
            """, (card_id,))
            row = await cur.fetchone()
            if row:
                data = dict(row)
                total_games = data["wins"] + data["losses"]
                data["win_rate"] = round((data["wins"] / total_games * 100), 1) if total_games > 0 else 0.0
                return data

            # If no stats record exists yet, fetch basic card info and return zeros
            cur = await db.execute("SELECT id, name, set_number, card_type, card_subtype, rarity FROM custom_cards WHERE id = ?", (card_id,))
            card_row = await cur.fetchone()
            if card_row:
                return {
                    "card_id": card_row["id"],
                    "name": card_row["name"],
                    "set_number": card_row["set_number"],
                    "card_type": card_row["card_type"],
                    "card_subtype": card_row["card_subtype"],
                    "rarity": card_row["rarity"],
                    "times_decked": 0,
                    "times_drawn": 0,
                    "times_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0.0
                }
            return {}

    async def get_meta_overview(self, limit: int = DEFAULT_META_LIMIT) -> Dict[str, List[Dict[str, Any]]]:
        """Returns top cards by deck popularity and most played cards."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT s.*, c.name, c.set_number
                FROM card_usage_stats s
                JOIN custom_cards c ON s.card_id = c.id
                ORDER BY s.times_decked DESC, s.times_played DESC LIMIT ?
            """, (limit,))
            most_decked = [dict(r) for r in await cur.fetchall()]

            cur = await db.execute("""
                SELECT s.*, c.name, c.set_number
                FROM card_usage_stats s
                JOIN custom_cards c ON s.card_id = c.id
                WHERE (s.wins + s.losses) > 0
                ORDER BY s.wins DESC LIMIT ?
            """, (limit,))
            most_wins = [dict(r) for r in await cur.fetchall()]

            return {"most_popular": most_decked, "most_victorious": most_wins}

    # -------------------------------------------------------------------------
    # 3.4 Live Duel Event Tracking Mutators
    # -------------------------------------------------------------------------

    async def track_card_draw(self, card_id: int):
        """Increments draw count for a card during live duels."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_drawn, last_used_at)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_drawn = times_drawn + 1,
                        last_used_at = CURRENT_TIMESTAMP
                """, (card_id,))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record card draw for ID {card_id}: {e}")

    async def track_card_play(self, card_id: int):
        """Increments play count for a card when summoned or activated."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_played, last_used_at)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_played = times_played + 1,
                        last_used_at = CURRENT_TIMESTAMP
                """, (card_id,))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record card play for ID {card_id}: {e}")

    async def track_deck_inclusion(self, card_id: int, delta: int):
        """Updates the count of player decks including this card."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                    VALUES (?, MAX(0, ?), CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_decked = MAX(0, times_decked + ?),
                        last_used_at = CURRENT_TIMESTAMP
                """, (card_id, delta, delta))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to track deck inclusion for ID {card_id}: {e}")


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "CardService",
    "CardRecordDict",
    "CardSummaryDict",
    "CardUsageStatsDict",
    "MetaOverviewDict",
    "DEFAULT_AUTOCOMPLETE_LIMIT",
    "DEFAULT_RECENT_LIMIT",
    "DEFAULT_META_LIMIT",
    "CARD_RECORD_PROJECTION",
    "CARD_RECORD_JOINS",
]

