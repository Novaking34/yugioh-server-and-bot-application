# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.foundation.colors
Description:
    Card Frame Color Palettes & Resolver for Yu-Gi-Oh! Discord Embeds.
    Maps authentic Yu-Gi-Oh! card frame mechanics (Normal, Effect, Ritual,
    Fusion, Synchro, Xyz, Link, Pendulum, Spell, Trap, Divine-Beast) to discord hex colors.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Final, Dict, Optional

# =============================================================================
# BLOCK 3: BODY BLOCK (Frame Colors Palette & Resolution Logic)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Authentic Card Frame Hex Palette (FRAME_COLORS)
# -----------------------------------------------------------------------------
FRAME_COLORS: Final[Dict[str, int]] = {
    'normal': 0xD4B37F,       # Normal Monster Yellow
    'effect': 0xC97434,       # Effect Monster Orange
    'ritual': 0x6E9ED4,       # Ritual Blue
    'fusion': 0x9356A0,       # Fusion Violet
    'synchro': 0xEEEEEE,      # Synchro White
    'xyz': 0x111111,          # Xyz Black
    'link': 0x0055AA,         # Link Dark Blue
    'pendulum': 0x00A88F,     # Pendulum Half-Green / Half-Orange Split Teal
    'spell': 0x1D9E74,        # Spell Green
    'trap': 0xBC3576,         # Trap Magenta
    'divine': 0xF59E0B,       # Divine Gold / Egyptian God Amber
    'token': 0x9E9E9E         # Token Grey
}


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Dynamic Frame Color Resolver (get_card_color)
# -----------------------------------------------------------------------------
def get_card_color(card_type: Optional[str], card_subtype: Optional[str], attribute: Optional[str] = None) -> int:
    """
    Selects the authentic Discord embed border color corresponding to
    the card's frame category and attribute (including Divine-Beast gold).
    Prioritizes:
    1. DIVINE attribute / Divine-Beast race -> Divine Gold
    2. Spell / Trap classification
    3. Extra Deck & Special Frames: Link, Xyz, Synchro, Fusion, Ritual, Pendulum
    4. Main Deck Monster: Effect vs Normal
    """
    ctype = (card_type or '').strip().lower()
    csub = (card_subtype or '').strip().lower()
    attr = (attribute or '').strip().upper()

    # Divine-Beast / DIVINE cards get distinctive Divine Gold border
    if attr == 'DIVINE' or 'divine' in csub:
        return FRAME_COLORS['divine']

    if ctype == 'spell':
        return FRAME_COLORS['spell']
    if ctype == 'trap':
        return FRAME_COLORS['trap']

    # Check Extra Deck & special summon mechanics in priority order
    for mechanic in ['link', 'xyz', 'synchro', 'fusion', 'ritual', 'pendulum', 'effect', 'normal']:
        if mechanic in csub:
            return FRAME_COLORS[mechanic]

    return FRAME_COLORS['effect']


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "FRAME_COLORS",
    "get_card_color",
]
