# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.domain.ydk
Description:
    Section 3.5: Official EDOPro / Project Ignis .YDK Serialization & Ingestion.
    Handles bidirectional parsing, section partitioning (#main, #extra, !side),
    passcode validation against SQLite, capacity clamping, and file I/O.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import aiosqlite
from typing import List, Dict, Any, Tuple, Optional, Union

from ..foundation.constants import (
    BANLIST_LIMITS,
    MAX_COPIES_PER_CARD,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
)
from ..foundation.classifier import is_extra_deck_card
from ..foundation.types import ParsedYDK

# =============================================================================
# BLOCK 3: BODY BLOCK (YDK Parsing, Serialization & File I/O Engine)
# =============================================================================


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Raw .YDK Parser (with UTF-8 BOM Handling)
# -----------------------------------------------------------------------------

def parse_ydk(ydk_text: str) -> ParsedYDK:
    """
    Parses a raw standard .ydk file or text string into distinct sections.
    Gracefully handles UTF-8 BOM, whitespace, comments, and empty lines.
    """
    if ydk_text.startswith("\ufeff"):
        ydk_text = ydk_text[1:]

    lines = ydk_text.strip().splitlines()
    creator: Optional[str] = None
    main_passcodes: List[int] = []
    extra_passcodes: List[int] = []
    side_passcodes: List[int] = []
    passcode_counts: Dict[int, int] = {}

    current_section = "main"

    for line in lines:
        line = line.strip().lstrip("\ufeff")
        if not line:
            continue
        if line.startswith("#created by"):
            creator = line.replace("#created by", "").strip()
            continue
        if line.startswith("#main"):
            current_section = "main"
            continue
        if line.startswith("#extra"):
            current_section = "extra"
            continue
        if line.startswith("!side"):
            current_section = "side"
            continue
        if line.startswith("#"):
            continue

        if line.isdigit():
            cid = int(line)
            passcode_counts[cid] = passcode_counts.get(cid, 0) + 1
            if current_section == "main":
                main_passcodes.append(cid)
            elif current_section == "extra":
                extra_passcodes.append(cid)
            elif current_section == "side":
                side_passcodes.append(cid)

    main_c = len(main_passcodes)
    extra_c = len(extra_passcodes)
    side_c = len(side_passcodes)
    total_c = main_c + extra_c + side_c

    return {
        "creator": creator,
        "main_passcodes": main_passcodes,
        "extra_passcodes": extra_passcodes,
        "side_passcodes": side_passcodes,
        "main_count": main_c,
        "extra_count": extra_c,
        "side_count": side_c,
        "total_count": total_c,
        "passcode_counts": passcode_counts,
        "is_valid_format": total_c > 0
    }


# -----------------------------------------------------------------------------
# Sub-Block 3.2: .YDK Format Serialization & Passcode Export
# -----------------------------------------------------------------------------

def export_to_ydk(
    cards: Union[List[Dict[str, Any]], Dict[str, Any]],
    deck_title: str = "Custom Deck"
) -> str:
    """
    Serializes a deck into official EDOPro / Project Ignis .ydk format.
    Accepts:
    1. Flat list of card dictionaries with optional 'section' and 'quantity'.
    2. Partitioned dictionary with 'main_deck', 'extra_deck', 'side_deck' lists.
    """
    main_ids: List[int] = []
    extra_ids: List[int] = []
    side_ids: List[int] = []

    if isinstance(cards, dict) and ("main_deck" in cards or "extra_deck" in cards):
        for c in cards.get("main_deck", []):
            cid = c.get("id")
            if cid:
                main_ids.extend([cid] * c.get("quantity", 1))
        for c in cards.get("extra_deck", []):
            cid = c.get("id")
            if cid:
                extra_ids.extend([cid] * c.get("quantity", 1))
        for c in cards.get("side_deck", []):
            cid = c.get("id")
            if cid:
                side_ids.extend([cid] * c.get("quantity", 1))
    elif isinstance(cards, list):
        for c in cards:
            cid = c.get("id")
            if not cid:
                continue
            qty = c.get("quantity", 1)
            section = (c.get("section") or "").upper()

            if section == "SIDE":
                side_ids.extend([cid] * qty)
            elif section == "EXTRA" or is_extra_deck_card(c):
                extra_ids.extend([cid] * qty)
            else:
                main_ids.extend([cid] * qty)

    lines = [f"#created by The Land of Kustomazi Deck Server - {deck_title}", "#main"]
    lines.extend(str(cid) for cid in main_ids)
    lines.append("#extra")
    lines.extend(str(cid) for cid in extra_ids)
    lines.append("!side")
    lines.extend(str(cid) for cid in side_ids)
    return "\n".join(lines) + "\n"


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Database Passcode Verification
# -----------------------------------------------------------------------------

async def validate_ydk_passcodes(
    passcodes: List[int],
    db_path: str
) -> Tuple[Dict[int, Dict[str, Any]], List[int]]:
    """
    Checks a list of passcodes against the custom_cards table in SQLite.
    Returns:
        (valid_cards_map: {id: card_dict}, missing_passcodes: [id, ...])
    """
    if not passcodes:
        return {}, []

    unique_ids = list(set(passcodes))
    placeholders = ",".join("?" for _ in unique_ids)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            f"""
            SELECT id, name, set_number, card_type, card_subtype, attribute,
                   monster_type, level_or_rank_or_link, banlist_status
            FROM custom_cards
            WHERE id IN ({placeholders})
            """,
            unique_ids
        )
        rows = await cur.fetchall()
        valid_map = {r["id"]: dict(r) for r in rows}

    missing = [cid for cid in unique_ids if cid not in valid_map]
    return valid_map, missing


# -----------------------------------------------------------------------------
# Sub-Block 3.4: File System I/O Helpers
# -----------------------------------------------------------------------------

def save_ydk_file(
    file_path: str,
    cards: Union[List[Dict[str, Any]], Dict[str, Any]],
    deck_title: str = "Custom Deck"
) -> str:
    """Writes a deck to a .ydk file on disk, creating parent folders if needed."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    ydk_content = export_to_ydk(cards, deck_title=deck_title)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(ydk_content)
    return file_path


def load_ydk_file(file_path: str) -> ParsedYDK:
    """Reads and parses a .ydk file from disk."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_ydk(content)


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Atomic .YDK Deck Ingestion Engine
# -----------------------------------------------------------------------------

async def import_ydk_to_player_deck(
    db_path: str,
    user_id: str,
    ydk_text: str
) -> Tuple[bool, str, int]:
    """
    Ingests a standard .ydk text representation into the player's active deck:
    - Parses #main, #extra, !side sections via deck_ydk parser.
    - Validates passcodes against SQLite custom cardpool.
    - Enforces banlist copy limits (MAX_COPIES_PER_CARD).
    - Enforces deck section capacity limits (Main <= 60, Extra <= 15).
    - Atomically updates player_decks and card_usage_stats.
    """
    user_id_str = str(user_id)
    parsed = parse_ydk(ydk_text)

    if not parsed["is_valid_format"] or not parsed["passcode_counts"]:
        return False, "No valid card passcodes found in .ydk content.", 0

    valid_cards, missing = await validate_ydk_passcodes(
        list(parsed["passcode_counts"].keys()),
        db_path
    )

    if not valid_cards:
        return False, "None of the cards in the file exist in the custom cardpool.", 0

    # Partition passcodes into Main and Extra deck based on custom_cards classification
    main_to_add: Dict[int, int] = {}
    extra_to_add: Dict[int, int] = {}

    for cid, raw_qty in parsed["passcode_counts"].items():
        if cid not in valid_cards:
            continue
        card_info = valid_cards[cid]
        banlist = card_info.get("banlist_status") or "Unlimited"
        max_c = BANLIST_LIMITS.get(banlist, MAX_COPIES_PER_CARD)
        qty = min(max_c, raw_qty)

        if is_extra_deck_card(card_info):
            extra_to_add[cid] = qty
        else:
            main_to_add[cid] = qty

    # Check section capacity
    main_total = sum(main_to_add.values())
    extra_total = sum(extra_to_add.values())

    if main_total > STANDARD_MAX_MAIN_DECK:
        excess = main_total - STANDARD_MAX_MAIN_DECK
        for cid in list(main_to_add.keys()):
            if excess <= 0:
                break
            can_reduce = main_to_add[cid]
            reduce_by = min(excess, can_reduce)
            main_to_add[cid] -= reduce_by
            excess -= reduce_by
            if main_to_add[cid] <= 0:
                del main_to_add[cid]

    if extra_total > STANDARD_MAX_EXTRA_DECK:
        excess = extra_total - STANDARD_MAX_EXTRA_DECK
        for cid in list(extra_to_add.keys()):
            if excess <= 0:
                break
            can_reduce = extra_to_add[cid]
            reduce_by = min(excess, can_reduce)
            extra_to_add[cid] -= reduce_by
            excess -= reduce_by
            if extra_to_add[cid] <= 0:
                del extra_to_add[cid]

    # Wipe old deck and insert new cards atomically
    async with aiosqlite.connect(db_path) as db:
        # Decrement card_usage_stats for cards being replaced to prevent telemetry drift
        cur = await db.execute("SELECT card_id, quantity FROM player_decks WHERE user_id = ?", (user_id_str,))
        old_cards = await cur.fetchall()
        for old_cid, old_qty in old_cards:
            await db.execute("""
                UPDATE card_usage_stats
                SET times_decked = MAX(0, times_decked - ?)
                WHERE card_id = ?
            """, (old_qty, old_cid))

        await db.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id_str,))
        total_added = 0

        all_to_insert = {**main_to_add, **extra_to_add}
        for cid, qty in all_to_insert.items():
            if qty <= 0:
                continue
            await db.execute("""
                INSERT INTO player_decks (user_id, card_id, quantity)
                VALUES (?, ?, ?)
            """, (user_id_str, cid, qty))
            await db.execute("""
                INSERT INTO card_usage_stats (card_id, times_decked, last_used_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    times_decked = times_decked + ?,
                    last_used_at = CURRENT_TIMESTAMP
            """, (cid, qty, qty))
            total_added += qty

        await db.commit()

    msg = f"Imported {len(all_to_insert)} unique card(s)"
    if missing:
        msg += f" ({len(missing)} unrecognized passcode(s) skipped)"

    return True, msg, total_added


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "parse_ydk",
    "export_to_ydk",
    "save_ydk_file",
    "load_ydk_file",
    "validate_ydk_passcodes",
    "import_ydk_to_player_deck",
]

