# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.card.foundation.formatters
Description:
    Real-time Autocomplete Choice & Descriptor Formatters.
    Builds rich, compact single-line labels for Discord autocomplete choice menus
    strictly bounded within Discord's 100-character ceiling.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Dict, Any, List

# =============================================================================
# BLOCK 3: BODY BLOCK (Autocomplete Formatting Functions)
# =============================================================================

def build_card_descriptor_tag(card: Dict[str, Any]) -> str:
    """
    Builds the compact mechanic metadata tag (e.g. [DIVINE ★12 Creator], [Spell/Field]).
    """
    card_type = (card.get("card_type") or "").strip()
    subtype = (card.get("card_subtype") or "").strip()

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

    return f"[{' '.join(descriptor_parts)}]" if descriptor_parts else ""


def format_card_autocomplete_choice(card: Dict[str, Any]) -> str:
    """
    Builds a rich, compact single-line label for Discord autocomplete choice menus.
    Enforces Discord's strict 100-character ceiling while displaying frame mechanics:
    - Monsters: [ATTR Lv/Rk/Link Type] (e.g. [DIVINE ★12 Creator], [DARK Rank 4 Dragon], [LIGHT Link-3 Cyberse])
    - Pendulum: includes scale e.g. [DARK ★4 S:8 Spellcaster]
    - Spells: [Spell/Field], [Spell/Quick-Play], [Spell/Continuous], etc.
    - Traps: [Trap/Counter], [Trap/Continuous], etc.
    """
    set_num = (card.get("set_number") or "").strip()
    cid = card.get("id")
    prefix = set_num if set_num else (f"[{cid}]" if cid else "")
    name = (card.get("name") or "").strip()

    tag = build_card_descriptor_tag(card)
    full_tag = f" {tag}" if tag else ""
    full_label = f"{prefix} | {name}{full_tag}" if prefix else f"{name}{full_tag}"

    if len(full_label) > 100:
        overhead = len(f"{prefix} | ") if prefix else 0
        tag_len = len(full_tag)
        available_name = 100 - overhead - tag_len - 3
        if available_name >= 8:
            full_label = f"{prefix} | {name[:available_name]}...{full_tag}" if prefix else f"{name[:available_name]}...{full_tag}"
        else:
            full_label = full_label[:97] + "..."

    return full_label


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports)
# =============================================================================

__all__ = [
    "build_card_descriptor_tag",
    "format_card_autocomplete_choice",
]
