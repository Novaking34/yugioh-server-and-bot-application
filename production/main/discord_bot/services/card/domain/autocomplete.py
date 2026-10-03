# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.domain.autocomplete
Description:
    Sub-Block 3.2: Real-time Autocomplete Engine.
    Executes high-performance ranked fuzzy search queries for live Discord
    slash commands with rich metadata tagging and contextual scoping.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import aiosqlite
from typing import Optional, List, Dict, Any

from ..foundation.constants import DEFAULT_AUTOCOMPLETE_LIMIT, EXTRA_DECK_SQL_CONDITION
from ..foundation.formatters import format_card_autocomplete_choice

# =============================================================================
# BLOCK 3: BODY BLOCK (Autocomplete Implementation)
# =============================================================================

def format_autocomplete_label(card: Dict[str, Any]) -> str:
    """
    Builds a rich, compact single-line label for Discord autocomplete choice menus.
    Enforces Discord's strict 100-character ceiling while displaying frame mechanics.
    """
    return format_card_autocomplete_choice(card)


async def search_cards(
    db_path: str,
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
        if is_extra_deck:
            conditions.append(EXTRA_DECK_SQL_CONDITION)
        else:
            conditions.append(f"NOT {EXTRA_DECK_SQL_CONDITION}")

    if archetype:
        conditions.append("LOWER(archetype) = LOWER(?)")
        params.append(archetype)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    async with aiosqlite.connect(db_path) as db:
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
            FROM custom_cards c
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


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "format_autocomplete_label",
    "search_cards",
]
