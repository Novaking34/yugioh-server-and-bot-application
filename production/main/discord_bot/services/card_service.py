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
from typing import Optional, List, Dict, Any, Tuple, TypedDict, Final, Union, Sequence
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
    attribute: Optional[str]
    monster_type: Optional[str]
    archetype: Optional[str]
    level: Optional[int]
    scale: Optional[int]
    times_decked: int
    times_drawn: int
    times_played: int
    wins: int
    losses: int
    total_matches: int
    last_used_at: Optional[str]
    win_rate: float                          # Derived: wins / (wins + losses) * 100
    play_to_draw_ratio: float                # Derived: times_played / times_drawn * 100


class MetaOverviewDict(TypedDict, total=False):
    """Format meta snapshot covering popularity, playrate, and victory metrics."""
    most_popular: List[CardUsageStatsDict]
    most_victorious: List[CardUsageStatsDict]
    most_played: List[CardUsageStatsDict]
    highest_win_rate: List[CardUsageStatsDict]
    most_drawn: List[CardUsageStatsDict]


class ArchetypeMetaDict(TypedDict, total=False):
    """Aggregated meta performance metrics for a specific archetype."""
    archetype: str
    total_cards: int
    times_decked: int
    times_drawn: int
    times_played: int
    wins: int
    losses: int
    total_matches: int
    win_rate: float
    top_card_name: Optional[str]
    top_card_id: Optional[int]


class CardpoolTelemetrySummaryDict(TypedDict, total=False):
    """High-level cardpool health and participation statistics."""
    total_registered_cards: int
    distinct_cards_decked: int
    distinct_cards_drawn: int
    distinct_cards_played: int
    total_deck_inclusions: int
    total_card_draws: int
    total_card_plays: int
    total_card_wins: int
    total_card_losses: int


# -----------------------------------------------------------------------------
# Sub-Block 2.8: Real-time Autocomplete Formatter
# -----------------------------------------------------------------------------
def format_card_autocomplete_choice(card: Dict[str, Any]) -> str:
    """
    Builds a rich, compact single-line label for Discord autocomplete choice menus.
    Enforces Discord's strict 100-character ceiling while displaying frame mechanics:
    - Monsters: [ATTR Lv/Rk/Link Type] (e.g. [DIVINE ★12 Creator], [DARK Rank 4 Dragon], [LIGHT Link-3 Cyberse])
    - Pendulum: includes scale e.g. [DARK ★4 S:8 Spellcaster]
    - Spells: [Spell/Field], [Spell/Quick-Play], [Spell/Continuous], etc.
    - Traps: [Trap/Counter], [Trap/Continuous], etc.
    """
    card_type = (card.get("card_type") or "").strip()
    subtype = (card.get("card_subtype") or "").strip()
    set_num = (card.get("set_number") or "").strip()
    cid = card.get("id")
    prefix = set_num if set_num else (f"[{cid}]" if cid else "")
    name = (card.get("name") or "").strip()

    descriptor_parts: List[str] = []

    if card_type.lower() == "monster":
        attr = card.get("attribute")
        if attr:
            descriptor_parts.append(str(attr).upper())

        lvl = card.get("level_or_rank_or_link") if card.get("level_or_rank_or_link") is not None else card.get("level")
        subtype_lower = subtype.lower()
        if "link" in subtype_lower:
            descriptor_parts.append(f"Link-{lvl}" if lvl is not None else "Link")
        elif "xyz" in subtype_lower:
            descriptor_parts.append(f"Rank {lvl}" if lvl is not None else "Xyz")
        else:
            if lvl is not None:
                descriptor_parts.append(f"★{lvl}")

        scale = card.get("scale")
        if scale is not None and ("pendulum" in subtype_lower or scale > 0):
            descriptor_parts.append(f"S:{scale}")

        mtype = card.get("monster_type")
        if mtype:
            descriptor_parts.append(str(mtype))
        elif subtype and subtype_lower not in ("normal", "effect"):
            clean_sub = subtype.split("/")[0].strip()
            if clean_sub.lower() not in ("normal", "effect"):
                descriptor_parts.append(clean_sub)

    elif card_type.lower() == "spell":
        if subtype and subtype.lower() != "normal":
            clean_sub = subtype.replace(" / ", "/").strip()
            descriptor_parts.append(f"Spell/{clean_sub}")
        else:
            descriptor_parts.append("Spell")

    elif card_type.lower() == "trap":
        if subtype and subtype.lower() != "normal":
            clean_sub = subtype.replace(" / ", "/").strip()
            descriptor_parts.append(f"Trap/{clean_sub}")
        else:
            descriptor_parts.append("Trap")
    else:
        if card_type:
            descriptor_parts.append(card_type)
        if subtype:
            descriptor_parts.append(subtype)

    tag = f" [{' '.join(descriptor_parts)}]" if descriptor_parts else ""
    full_label = f"{prefix} | {name}{tag}" if prefix else f"{name}{tag}"

    if len(full_label) > 100:
        overhead = len(f"{prefix} | ") if prefix else 0
        tag_len = len(tag)
        available_name = 100 - overhead - tag_len - 3
        if available_name >= 8:
            full_label = f"{prefix} | {name[:available_name]}...{tag}" if prefix else f"{name[:available_name]}...{tag}"
        else:
            full_label = full_label[:97] + "..."

    return full_label


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

    async def get_card_by_set_number(self, set_number: str) -> Optional[Dict[str, Any]]:
        """
        Direct lookup for a single card by its official set number (e.g. TLOK-001).
        Case-insensitive and whitespace-tolerant.
        """
        clean = set_number.strip()
        if not clean:
            return None
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(f"""
                SELECT {CARD_RECORD_PROJECTION}
                {CARD_RECORD_JOINS}
                WHERE LOWER(c.set_number) = LOWER(?)
                LIMIT 1
            """, (clean,))
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

        # Strip trailing autocomplete metadata tags e.g. "Card Name [Spell/Field]" or "Card Name [DIVINE ★12 Creator]"
        if raw_str.endswith("]") and " [" in raw_str:
            without_tag = raw_str[:raw_str.rindex(" [")].strip()
            if without_tag:
                found = await self.get_card_by_query(without_tag)
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
        level: Optional[int] = None,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        scale: Optional[int] = None,
        min_atk: Optional[int] = None,
        max_atk: Optional[int] = None,
        min_def: Optional[int] = None,
        max_def: Optional[int] = None,
        rarity: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Discovers cards matching comprehensive game mechanics and criteria:
        - Primary frame: card_type ("Monster", "Spell", "Trap")
        - Mechanics/subtypes: card_subtype ("Ritual", "Fusion", "Synchro", "Xyz", "Link", "Pendulum", "Field", "Quick-Play", "Counter"...)
        - Battle stats: level/rank/link, min/max level, scale, min/max ATK, min/max DEF
        - Universe: attribute, archetype, monster_type (race), rarity
        - Zone: is_extra_deck (True = Fusion/Synchro/Xyz/Link; False = Main Deck)
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
        if level is not None:
            conditions.append("c.level_or_rank_or_link = ?")
            params.append(level)
        if min_level is not None:
            conditions.append("c.level_or_rank_or_link >= ?")
            params.append(min_level)
        if max_level is not None:
            conditions.append("c.level_or_rank_or_link <= ?")
            params.append(max_level)
        if scale is not None:
            conditions.append("c.scale = ?")
            params.append(scale)
        if min_atk is not None:
            conditions.append("c.atk >= ?")
            params.append(min_atk)
        if max_atk is not None:
            conditions.append("c.atk <= ?")
            params.append(max_atk)
        if min_def is not None:
            conditions.append("c.def >= ?")
            params.append(min_def)
        if max_def is not None:
            conditions.append("c.def <= ?")
            params.append(max_def)
        if rarity:
            conditions.append("LOWER(c.rarity) = LOWER(?)")
            params.append(rarity)
        if is_extra_deck is not None:
            extra_cond = """(
                LOWER(c.card_type) IN ('fusion', 'synchro', 'xyz', 'link') OR
                LOWER(c.card_subtype) LIKE '%fusion%' OR
                LOWER(c.card_subtype) LIKE '%synchro%' OR
                LOWER(c.card_subtype) LIKE '%xyz%' OR
                LOWER(c.card_subtype) LIKE '%link%'
            )"""
            if is_extra_deck:
                conditions.append(extra_cond)
            else:
                conditions.append(f"NOT {extra_cond}")

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

    async def get_extra_deck_cards(self) -> List[Dict[str, Any]]:
        """Retrieves all registered Extra Deck cards (Fusion, Synchro, Xyz, Link)."""
        return await self.get_cards_by_filter(is_extra_deck=True)

    async def get_main_deck_cards(self) -> List[Dict[str, Any]]:
        """Retrieves all registered Main Deck cards (Monsters, Spells, Traps)."""
        return await self.get_cards_by_filter(is_extra_deck=False)

    async def get_field_spells(self) -> List[Dict[str, Any]]:
        """Retrieves all Field Spell cards in the cardpool."""
        return await self.get_cards_by_filter(card_type="Spell", card_subtype="Field")

    async def get_ritual_monsters(self) -> List[Dict[str, Any]]:
        """Retrieves all Ritual Monster cards in the cardpool."""
        return await self.get_cards_by_filter(card_type="Monster", card_subtype="Ritual")

    async def get_cards_by_archetype(self, archetype: str) -> List[Dict[str, Any]]:
        """Retrieves all cards belonging to a specific archetype (e.g. Kasutamaiza)."""
        return await self.get_cards_by_filter(archetype=archetype)

    # -------------------------------------------------------------------------
    # 3.2 Real-time Autocomplete Engine
    # -------------------------------------------------------------------------

    @staticmethod
    def format_autocomplete_label(card: Dict[str, Any]) -> str:
        """
        Builds a rich, compact single-line label for Discord autocomplete choice menus.
        Enforces Discord's strict 100-character ceiling while displaying frame mechanics.
        """
        return format_card_autocomplete_choice(card)

    async def search_cards(
        self,
        current: str,
        limit: int = DEFAULT_AUTOCOMPLETE_LIMIT,
        card_type: Optional[str] = None,
        card_subtype: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        archetype: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns ranked matching card suggestions for real-time Discord autocomplete.
        Prioritizes:
        1. Exact Match (Name, Set Number, Passcode)
        2. Prefix Name Match (e.g. "Kas..." -> "Kasutamaiza...")
        3. Prefix Set Number Match (e.g. "TLOK..." -> "TLOK-001...")
        4. Word-Boundary Match (e.g. "Creator" -> "Kasutamaiza, the Creator of Kustomazi")
        5. General Substring Match
        Supports contextual scoping (card_type, card_subtype, is_extra_deck, archetype).
        When query is empty, yields cards in canonical Set order (TLOK-001, TLOK-002...).
        """
        clean = current.strip()
        conditions = []
        params: List[Any] = []

        if clean:
            conditions.append("(LOWER(name) LIKE LOWER(?) OR LOWER(set_number) LIKE LOWER(?) OR CAST(id AS TEXT) LIKE ?)")
            params.extend([f"%{clean}%", f"%{clean}%", f"%{clean}%"])

        if card_type:
            conditions.append("LOWER(card_type) = LOWER(?)")
            params.append(card_type)

        if card_subtype:
            conditions.append("LOWER(card_subtype) LIKE LOWER(?)")
            params.append(f"%{card_subtype}%")

        if is_extra_deck is not None:
            extra_cond = """(
                LOWER(card_type) IN ('fusion', 'synchro', 'xyz', 'link') OR
                LOWER(card_subtype) LIKE '%fusion%' OR
                LOWER(card_subtype) LIKE '%synchro%' OR
                LOWER(card_subtype) LIKE '%xyz%' OR
                LOWER(card_subtype) LIKE '%link%'
            )"""
            if is_extra_deck:
                conditions.append(extra_cond)
            else:
                conditions.append(f"NOT {extra_cond}")

        if archetype:
            conditions.append("LOWER(archetype) = LOWER(?)")
            params.append(archetype)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if clean:
                order_clause = """
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
                """
                order_params = [clean, clean, clean, clean, clean, clean]
            else:
                order_clause = """
                    ORDER BY 
                        CASE WHEN set_number IS NOT NULL THEN 0 ELSE 1 END,
                        set_number ASC,
                        id ASC
                """
                order_params = []

            sql = f"""
                SELECT id, set_number, name, card_type, card_subtype, rarity, attribute,
                       monster_type, level_or_rank_or_link, scale
                FROM custom_cards
                {where_clause}
                {order_clause}
                LIMIT ?
            """
            cur = await db.execute(sql, (*params, *order_params, limit))
            rows = await cur.fetchall()

            results = []
            for r in rows:
                d = dict(r)
                d["autocomplete_label"] = format_card_autocomplete_choice(d)
                results.append(d)
            return results

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

    async def get_all_cards_partitioned(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns the complete Set 1 cardpool partitioned into Main Deck and Extra Deck categories.
        """
        all_cards = await self.get_all_cards()
        main_deck = []
        extra_deck = []
        for c in all_cards:
            ctype = (c.get("card_type") or "").lower()
            csub = (c.get("card_subtype") or "").lower()
            if ctype in ("fusion", "synchro", "xyz", "link") or any(m in csub for m in ("fusion", "synchro", "xyz", "link")):
                extra_deck.append(c)
            else:
                main_deck.append(c)
        return {"main_deck": main_deck, "extra_deck": extra_deck}

    async def get_random_card(
        self,
        card_type: Optional[str] = None,
        card_subtype: Optional[str] = None,
        is_extra_deck: Optional[bool] = None,
        archetype: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Selects a random card from the active pool, optionally filtered by card_type,
        card_subtype, extra deck status, or archetype.
        """
        conditions = []
        params: List[Any] = []

        if card_type:
            conditions.append("LOWER(c.card_type) = LOWER(?)")
            params.append(card_type)
        if card_subtype:
            conditions.append("LOWER(c.card_subtype) LIKE LOWER(?)")
            params.append(f"%{card_subtype}%")
        if is_extra_deck is not None:
            extra_cond = """(
                LOWER(c.card_type) IN ('fusion', 'synchro', 'xyz', 'link') OR
                LOWER(c.card_subtype) LIKE '%fusion%' OR
                LOWER(c.card_subtype) LIKE '%synchro%' OR
                LOWER(c.card_subtype) LIKE '%xyz%' OR
                LOWER(c.card_subtype) LIKE '%link%'
            )"""
            if is_extra_deck:
                conditions.append(extra_cond)
            else:
                conditions.append(f"NOT {extra_cond}")
        if archetype:
            conditions.append("LOWER(c.archetype) = LOWER(?)")
            params.append(archetype)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(f"""
                SELECT {CARD_RECORD_PROJECTION}
                {CARD_RECORD_JOINS}
                {where_clause}
                ORDER BY RANDOM() LIMIT 1
            """, params)
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
        """
        Fetches comprehensive telemetry stats for a card:
        - Times decked, drawn, played, won, lost.
        - Calculated metrics: total_matches, win_rate (%), play_to_draw_ratio (%).
        - Joined card metadata: name, set_number, card_type, card_subtype, attribute,
          monster_type, archetype, level_or_rank_or_link (as level), scale, rarity.
        If no stats row exists yet, returns initialized zero-counts with card identity.
        """
        async with aiosqlite.connect(self.db_path) as db:
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
        self,
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
            extra_cond = """(
                LOWER(c.card_type) IN ('fusion', 'synchro', 'xyz', 'link') OR
                LOWER(c.card_subtype) LIKE '%fusion%' OR
                LOWER(c.card_subtype) LIKE '%synchro%' OR
                LOWER(c.card_subtype) LIKE '%xyz%' OR
                LOWER(c.card_subtype) LIKE '%link%'
            )"""
            if is_extra_deck:
                conditions.append(extra_cond)
            else:
                conditions.append(f"NOT {extra_cond}")
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

        async with aiosqlite.connect(self.db_path) as db:
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
        self,
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

        async with aiosqlite.connect(self.db_path) as db:
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

    async def get_archetype_meta_stats(self, archetype: str) -> Dict[str, Any]:
        """
        Aggregates meta telemetry across all registered cards in a specific archetype.
        """
        clean = archetype.strip()
        async with aiosqlite.connect(self.db_path) as db:
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

    async def get_cardpool_telemetry_summary(self) -> Dict[str, Any]:
        """
        Returns macro server-wide health and activity metrics for the cardpool.
        """
        async with aiosqlite.connect(self.db_path) as db:
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

    async def get_underused_cards(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Identifies cards with lowest deck inclusion and play activity.
        Useful for community deck ideas and cardpool balance reviews.
        """
        async with aiosqlite.connect(self.db_path) as db:
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

    # -------------------------------------------------------------------------
    # 3.4 Live Duel Event Tracking Mutators
    # -------------------------------------------------------------------------

    async def track_card_draw(self, card_id: int, count: int = 1):
        """Increments draw count for a card during live duels."""
        if count <= 0:
            return
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_drawn, last_used_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_drawn = times_drawn + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (card_id, count, count))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record card draw for ID {card_id}: {e}")

    async def track_cards_drawn(self, card_ids: Sequence[int]):
        """
        Atomically records multi-card draws (e.g. 5-card opening hand) in a single transaction.
        """
        if not card_ids:
            return
        counts: Dict[int, int] = {}
        for cid in card_ids:
            counts[cid] = counts.get(cid, 0) + 1
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for cid, count in counts.items():
                    await db.execute("""
                        INSERT INTO card_usage_stats (card_id, times_drawn, last_used_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(card_id) DO UPDATE SET
                            times_drawn = times_drawn + ?,
                            last_used_at = CURRENT_TIMESTAMP
                    """, (cid, count, count))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to batch record card draws: {e}")

    async def track_card_play(self, card_id: int, count: int = 1):
        """Increments play count for a card when summoned or activated."""
        if count <= 0:
            return
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, times_played, last_used_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        times_played = times_played + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (card_id, count, count))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record card play for ID {card_id}: {e}")

    async def track_cards_played(self, card_ids: Sequence[int]):
        """
        Atomically records multi-card plays in a single transaction.
        """
        if not card_ids:
            return
        counts: Dict[int, int] = {}
        for cid in card_ids:
            counts[cid] = counts.get(cid, 0) + 1
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for cid, count in counts.items():
                    await db.execute("""
                        INSERT INTO card_usage_stats (card_id, times_played, last_used_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(card_id) DO UPDATE SET
                            times_played = times_played + ?,
                            last_used_at = CURRENT_TIMESTAMP
                    """, (cid, count, count))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to batch record card plays: {e}")

    async def track_card_match_result(self, card_id: int, is_win: bool):
        """
        Records a match win or loss for a single card in an active deck.
        """
        w = 1 if is_win else 0
        l = 0 if is_win else 1
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(card_id) DO UPDATE SET
                        wins = wins + ?,
                        losses = losses + ?,
                        last_used_at = CURRENT_TIMESTAMP
                """, (card_id, w, l, w, l))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record match result for card ID {card_id}: {e}")

    async def track_cards_match_result(self, card_ids: Sequence[int], is_win: bool):
        """
        Atomically records match outcome for all distinct cards in a player's deck.
        Deduplicates card IDs so each distinct card receives 1 win or 1 loss per match.
        """
        if not card_ids:
            return
        unique_ids = set(card_ids)
        w = 1 if is_win else 0
        l = 0 if is_win else 1
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for cid in unique_ids:
                    await db.execute("""
                        INSERT INTO card_usage_stats (card_id, wins, losses, last_used_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(card_id) DO UPDATE SET
                            wins = wins + ?,
                            losses = losses + ?,
                            last_used_at = CURRENT_TIMESTAMP
                    """, (cid, w, l, w, l))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to batch record match results for cards: {e}")

    async def track_deck_inclusion(self, card_id: int, delta: int):
        """Updates the count of player decks including this card."""
        if delta == 0:
            return
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

    async def batch_track_deck_inclusions(self, card_deltas: Dict[int, int]):
        """
        Atomically updates deck inclusion counts for multiple cards in a single transaction.
        """
        if not card_deltas:
            return
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for cid, delta in card_deltas.items():
                    if delta != 0:
                        await db.execute("""
                            INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                            VALUES (?, MAX(0, ?), CURRENT_TIMESTAMP)
                            ON CONFLICT(card_id) DO UPDATE SET
                                times_decked = MAX(0, times_decked + ?),
                                last_used_at = CURRENT_TIMESTAMP
                        """, (cid, delta, delta))
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to batch track deck inclusions: {e}")

    async def reset_card_telemetry(self, card_id: Optional[int] = None):
        """
        Resets telemetry counters to zero for a specific card or all cards (maintenance/testing).
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if card_id is not None:
                    await db.execute("""
                        UPDATE card_usage_stats
                        SET times_decked = 0, times_drawn = 0, times_played = 0,
                            wins = 0, losses = 0, last_used_at = CURRENT_TIMESTAMP
                        WHERE card_id = ?
                    """, (card_id,))
                else:
                    await db.execute("""
                        UPDATE card_usage_stats
                        SET times_decked = 0, times_drawn = 0, times_played = 0,
                            wins = 0, losses = 0, last_used_at = CURRENT_TIMESTAMP
                    """)
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to reset card telemetry: {e}")


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "CardService",
    "format_card_autocomplete_choice",
    "CardRecordDict",
    "CardSummaryDict",
    "CardUsageStatsDict",
    "MetaOverviewDict",
    "ArchetypeMetaDict",
    "CardpoolTelemetrySummaryDict",
    "DEFAULT_AUTOCOMPLETE_LIMIT",
    "DEFAULT_RECENT_LIMIT",
    "DEFAULT_META_LIMIT",
    "CARD_RECORD_PROJECTION",
    "CARD_RECORD_JOINS",
    "CARD_TYPE_MONSTER",
    "CARD_TYPE_SPELL",
    "CARD_TYPE_TRAP",
    "CARD_TYPES",
    "CARD_ATTRIBUTES",
]

