# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.domain.discovery
Description:
    Sub-Block 3.1: Card Discovery & Direct Lookups Engine.
    Executes O(1) indexed passcode lookups, set number lookups, composite query
    sanitization, multi-criteria game mechanic filtering, and partitioned
    deck exports against SQLite.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import aiosqlite
from typing import Optional, List, Dict, Any, Union

from ..foundation.constants import (
    CARD_RECORD_PROJECTION,
    CARD_RECORD_JOINS,
    EXTRA_DECK_SQL_CONDITION,
    DEFAULT_RECENT_LIMIT,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Card Discovery Implementation)
# =============================================================================

async def get_card_by_id(db_path: str, card_id: int) -> Optional[Dict[str, Any]]:
    """
    Direct O(1) indexed lookup for a single card by its 8-digit passcode ID.
    Returns the canonical CARD_RECORD_PROJECTION or None if not found.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(f"""
            SELECT {CARD_RECORD_PROJECTION}
            {CARD_RECORD_JOINS}
            WHERE c.id = ?
            LIMIT 1
        """, (card_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_card_by_set_number(db_path: str, set_number: str) -> Optional[Dict[str, Any]]:
    """
    Direct lookup for a single card by its official set number (e.g. TLOK-001).
    Case-insensitive and whitespace-tolerant.
    """
    clean = set_number.strip()
    if not clean:
        return None
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(f"""
            SELECT {CARD_RECORD_PROJECTION}
            {CARD_RECORD_JOINS}
            WHERE LOWER(c.set_number) = LOWER(?)
            LIMIT 1
        """, (clean,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_card_by_query(db_path: str, query: Union[str, int]) -> Optional[Dict[str, Any]]:
    """
    Retrieves a custom card by exact or prioritized fuzzy match across:
    1. Passcode ID (e.g. 50000101)
    2. Set Number (e.g. TLOK-001)
    3. Exact Name (case-insensitive)
    4. Name Prefix or Substring
    Gracefully handles composite autocomplete labels and bracketed labels.
    """
    raw_str = str(query).strip()
    if not raw_str:
        return None

    # Sanitize composite labels e.g. "TLOK-001 | Card Name"
    if " | " in raw_str:
        parts = [p.strip() for p in raw_str.split(" | ") if p.strip()]
        for part in parts:
            found = await get_card_by_query(db_path, part)
            if found:
                return found

    # Sanitize bracketed labels e.g. "[50000101] Card Name"
    if raw_str.startswith("[") and "]" in raw_str:
        bracket_val = raw_str[1:raw_str.index("]")].strip()
        if bracket_val.isdigit():
            found = await get_card_by_id(db_path, int(bracket_val))
            if found:
                return found
        rest = raw_str[raw_str.index("]") + 1:].strip()
        if rest:
            found = await get_card_by_query(db_path, rest)
            if found:
                return found

    # Strip trailing autocomplete metadata tags e.g. "Card Name [Spell/Field]" or "Card Name [DIVINE ★12 Creator]"
    if raw_str.endswith("]") and " [" in raw_str:
        without_tag = raw_str[:raw_str.rindex(" [")].strip()
        if without_tag:
            found = await get_card_by_query(db_path, without_tag)
            if found:
                return found

    # Fast path: numeric string lookup directly by passcode
    if raw_str.isdigit():
        found = await get_card_by_id(db_path, int(raw_str))
        if found:
            return found

    query_clean = raw_str
    like_pattern = f"%{query_clean}%"

    async with aiosqlite.connect(db_path) as db:
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
    db_path: str,
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
    - Mechanics/subtypes: card_subtype ("Ritual", "Fusion", "Synchro", "Xyz", "Link", "Pendulum", "Field"...)
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
        if is_extra_deck:
            conditions.append(EXTRA_DECK_SQL_CONDITION)
        else:
            conditions.append(f"NOT {EXTRA_DECK_SQL_CONDITION}")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit_clause = f"LIMIT {int(limit)}" if limit and limit > 0 else ""

    async with aiosqlite.connect(db_path) as db:
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


async def get_extra_deck_cards(db_path: str) -> List[Dict[str, Any]]:
    """Retrieves all registered Extra Deck cards (Fusion, Synchro, Xyz, Link)."""
    return await get_cards_by_filter(db_path, is_extra_deck=True)


async def get_main_deck_cards(db_path: str) -> List[Dict[str, Any]]:
    """Retrieves all registered Main Deck cards (Monsters, Spells, Traps)."""
    return await get_cards_by_filter(db_path, is_extra_deck=False)


async def get_field_spells(db_path: str) -> List[Dict[str, Any]]:
    """Retrieves all Field Spell cards in the cardpool."""
    return await get_cards_by_filter(db_path, card_type="Spell", card_subtype="Field")


async def get_ritual_monsters(db_path: str) -> List[Dict[str, Any]]:
    """Retrieves all Ritual Monster cards in the cardpool."""
    return await get_cards_by_filter(db_path, card_type="Monster", card_subtype="Ritual")


async def get_cards_by_archetype(db_path: str, archetype: str) -> List[Dict[str, Any]]:
    """Retrieves all cards belonging to a specific archetype (e.g. Kasutamaiza)."""
    return await get_cards_by_filter(db_path, archetype=archetype)


async def get_all_cards(db_path: str) -> List[Dict[str, Any]]:
    """Returns all registered custom cards in Set 1."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(f"""
            SELECT {CARD_RECORD_PROJECTION}
            {CARD_RECORD_JOINS}
            ORDER BY c.id ASC
        """)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_cards_partitioned(db_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns the complete Set 1 cardpool partitioned into Main Deck and Extra Deck categories.
    """
    all_cards = await get_all_cards(db_path)
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
    db_path: str,
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
        if is_extra_deck:
            conditions.append(EXTRA_DECK_SQL_CONDITION)
        else:
            conditions.append(f"NOT {EXTRA_DECK_SQL_CONDITION}")
    if archetype:
        conditions.append("LOWER(c.archetype) = LOWER(?)")
        params.append(archetype)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(f"""
            SELECT {CARD_RECORD_PROJECTION}
            {CARD_RECORD_JOINS}
            {where_clause}
            ORDER BY RANDOM() LIMIT 1
        """, params)
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_recent_cards(db_path: str, limit: int = DEFAULT_RECENT_LIMIT) -> List[Dict[str, Any]]:
    """Returns recently added custom cards with summary identity."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT id, set_number, name, card_type, card_subtype, rarity, created_at
            FROM custom_cards
            ORDER BY created_at DESC, id DESC LIMIT ?
        """, (limit,))
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "get_card_by_id",
    "get_card_by_set_number",
    "get_card_by_query",
    "get_cards_by_filter",
    "get_extra_deck_cards",
    "get_main_deck_cards",
    "get_field_spells",
    "get_ritual_monsters",
    "get_cards_by_archetype",
    "get_all_cards",
    "get_all_cards_partitioned",
    "get_random_card",
    "get_recent_cards",
]
