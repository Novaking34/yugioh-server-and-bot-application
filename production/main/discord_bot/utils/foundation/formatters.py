# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.foundation.formatters
Description:
    Foundation Formatting Primitives & Simulator Invariant Resolvers.
    Provides pure string manipulation, stat sentinel translation, Link Arrow
    compass geometry rendering, 8-digit passcode zero-padding, and Spell Speed
    determination for Yu-Gi-Oh! cards under Master Rule (MR5) and EDOPro/YGOPro.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional, Tuple, Union

# =============================================================================
# BLOCK 3: BODY BLOCK (Formatting Primitives & Simulator Invariant Resolvers)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Simulator Constants & Bitmaps
# -----------------------------------------------------------------------------

# Stat sentinel: In SQLite / CDB datas, variable stats ('?') are stored as -2.
STAT_UNKNOWN: int = -2

# Directional glyphs for Link Monster arrow markers
LINK_ARROW_GLYPHS: Dict[str, str] = {
    "TL": "↖",
    "T": "⬆",
    "TR": "↗",
    "L": "⬅",
    "R": "➡",
    "BL": "↙",
    "B": "⬇",
    "BR": "↘",
}

# Octal bitmask mapping for ocgcore / EDOPro datas.def Link Markers
LINK_BIT_MAP: List[Tuple[int, str, str]] = [
    (0o001, "B", "⬇"),
    (0o002, "BL", "↙"),
    (0o004, "BR", "↘"),
    (0o010, "L", "⬅"),
    (0o040, "R", "➡"),
    (0o100, "T", "⬆"),
    (0o200, "TL", "↖"),
    (0o400, "TR", "↗"),
]

# Attribute emoji glyphs for visual recognition in Discord UI
ATTRIBUTE_ICONS: Dict[str, str] = {
    "LIGHT": "☀️",
    "DARK": "🌑",
    "EARTH": "⛰️",
    "WATER": "🌊",
    "FIRE": "🔥",
    "WIND": "🌪️",
    "DIVINE": "✨",
}

# Official Konami Property Icons for Spells and Traps
SPELL_TRAP_ICONS: Dict[str, str] = {
    "quick-play": "⚡",
    "continuous": "∞",
    "field": "⨁",
    "equip": "+",
    "ritual": "🔥",
    "counter": "⤶",
}


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Passcode & Stat Sentinel Resolvers
# -----------------------------------------------------------------------------

def format_passcode(card_id: Any) -> str:
    """
    Formats the card's unique passcode into an 8-digit zero-padded string.
    In EDOPro and YGOPro, every card script is named c{passcode}.lua and
    artwork is keyed to {passcode}.jpg. Canonical 8-digit formatting
    ensures seamless compatibility with the simulator deckbuilder and Lua engine.
    """
    raw_str = str(card_id).strip()
    if raw_str.isdigit():
        return f"{int(raw_str):08d}"
    return raw_str


def format_stat_value(val: Any) -> str:
    """
    Resolves combat stat values (ATK / DEF) honoring official Yu-Gi-Oh!
    rules and EDOPro sentinels. In SQLite / CDB datas, variable stats ('?')
    are stored as -2 (STAT_UNKNOWN). Formats -2, '?', or 'VAR' to '?'.
    """
    if val in (STAT_UNKNOWN, -2, "?", "VAR", "-2"):
        return "?"
    if val is None:
        return "0"
    return str(val)


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Directional Compass & Geometry Resolvers
# -----------------------------------------------------------------------------

def format_link_arrows(arrows: Union[str, int, None]) -> str:
    """
    Converts Link arrows into visual Unicode directional glyphs and codes.
    Accepts:
    - Comma-separated strings, e.g. "BL,BR,T" -> "↙ ⬆ ↘ [BL, BR, T]"
    - Integer / octal bitmasks, e.g. 0o105 -> "⬇ ↘ ⬆ [B, BR, T]"
    Returns an empty string if no arrows are present.
    """
    if not arrows:
        return ""

    if isinstance(arrows, int):
        bits = arrows
        active_codes = []
        active_glyphs = []
        for bit, code, glyph in LINK_BIT_MAP:
            if bits & bit:
                active_codes.append(code)
                active_glyphs.append(glyph)
        if not active_codes:
            return ""
        return f"{' '.join(active_glyphs)} [{', '.join(active_codes)}]"

    raw_str = str(arrows).strip()
    if not raw_str or raw_str.upper() in ("NONE", "N/A"):
        return ""

    parts = [p.strip().upper() for p in raw_str.split(",") if p.strip()]
    glyphs = [LINK_ARROW_GLYPHS.get(p, p) for p in parts]
    return f"{' '.join(glyphs)} [{', '.join(parts)}]"


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Spell & Trap Speed Resolvers
# -----------------------------------------------------------------------------

def format_spell_trap_property(card_type: str, card_subtype: str) -> Tuple[str, str, int]:
    """
    Resolves official Konami property icon, classification label,
    and Spell Speed tier for Spell and Trap cards.
    Returns:
        (property_icon, speed_tag, spell_speed_int)
    """
    ctype = (card_type or "").strip().lower()
    csub = (card_subtype or "").strip().lower()

    if ctype == "spell":
        if "quick" in csub:
            return "⚡", "⚡ Quick-Play [Speed 2]", 2
        elif "continuous" in csub:
            return "∞", "∞ Continuous [Speed 1]", 1
        elif "field" in csub:
            return "⨁", "⨁ Field [Speed 1]", 1
        elif "equip" in csub:
            return "+", "+ Equip [Speed 1]", 1
        elif "ritual" in csub:
            return "🔥", "🔥 Ritual [Speed 1]", 1
        else:
            return "", "Normal [Speed 1]", 1
    elif ctype == "trap":
        if "counter" in csub:
            return "⤶", "⤶ Counter [Speed 3]", 3
        elif "continuous" in csub:
            return "∞", "∞ Continuous [Speed 2]", 2
        else:
            return "", "Normal [Speed 2]", 2

    return "", f"{card_subtype} [Speed 1]", 1


def get_spell_speed(card_type: str, card_subtype: str) -> int:
    """
    Returns the integer Spell Speed (1, 2, or 3) for a card.
    - Speed 1: Normal, Continuous, Equip, Field, Ritual Spells.
    - Speed 2: Quick-Play Spells, Normal Traps, Continuous Traps.
    - Speed 3: Counter Traps.
    """
    _, _, speed = format_spell_trap_property(card_type, card_subtype)
    return speed


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Monster Classification & Parameter Formatter
# -----------------------------------------------------------------------------

def format_monster_classification(race: Optional[str], subtype: Optional[str]) -> str:
    """
    Constructs the official Konami bracketed monster classification line:
    e.g. '[Divine-Beast / Effect]', '[Cyberse / Link / Effect]', '[Warrior / Tuner / Effect]'.
    """
    clean_race = (race or "Monster").strip()
    clean_sub = (subtype or "Normal").strip()
    return f"[{clean_race} / {clean_sub}]"


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Constants & Bitmaps
    "STAT_UNKNOWN",
    "LINK_ARROW_GLYPHS",
    "LINK_BIT_MAP",
    "ATTRIBUTE_ICONS",
    "SPELL_TRAP_ICONS",
    # Passcode & Stat Resolvers
    "format_passcode",
    "format_stat_value",
    # Geometry & Compass Resolvers
    "format_link_arrows",
    # Spell Speed & Property Resolvers
    "format_spell_trap_property",
    "get_spell_speed",
    # Monster Classification
    "format_monster_classification",
]
