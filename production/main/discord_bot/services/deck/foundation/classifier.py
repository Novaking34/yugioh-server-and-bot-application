# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.foundation.classifier
Description:
    Bottom-Up Foundation: Dynamic card classification, summoning mechanics,
    tribute costs, pendulum scales, and Problem-Solving Card Text (PSCT)
    zone interaction detectors.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import re
from typing import Dict, Any, Tuple

# =============================================================================
# BLOCK 3: BODY BLOCK (Card Classification & Zone Awareness Engine)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Extra Deck & Pendulum Classifiers
# -----------------------------------------------------------------------------

def is_extra_deck_card(card: Dict[str, Any]) -> bool:
    """
    Determines whether a card belongs in the Extra Deck.
    Extra Deck categories: Fusion, Synchro, Xyz, Link.
    (Pendulums go to Extra Deck only if they are also Fusion/Synchro/Xyz).
    """
    card_type = (card.get("card_type") or "").strip().lower()
    card_subtype = (card.get("card_subtype") or "").strip().lower()
    
    if card_type in ("fusion", "synchro", "xyz", "link"):
        return True
    
    for mechanism in ("fusion", "synchro", "xyz", "link"):
        if mechanism in card_subtype:
            return True
            
    return False


def is_extra_deck_pendulum(card: Dict[str, Any]) -> bool:
    """Returns True if the card is a Pendulum Monster that starts in the Extra Deck."""
    subtype = (card.get("card_subtype") or "").lower()
    return "pendulum" in subtype and any(m in subtype for m in ("fusion", "synchro", "xyz"))


def is_main_deck_pendulum(card: Dict[str, Any]) -> bool:
    """Returns True if the card is a Pendulum Monster that starts in the Main Deck."""
    subtype = (card.get("card_subtype") or "").lower()
    return "pendulum" in subtype and not is_extra_deck_pendulum(card)


def get_pendulum_scales(card: Dict[str, Any]) -> Tuple[int, int]:
    """
    Extracts the official left and right pendulum scales for a card.
    Returns (left_scale, right_scale).
    """
    scale = card.get("scale")
    if scale is not None and str(scale).isdigit():
        s = int(scale)
        return (s, s)

    text = f"{card.get('pendulum_effect') or ''} {card.get('effect_text') or ''}"
    match = re.search(r'Scale\s*[:=]?\s*(\d+)', text, re.IGNORECASE)
    if match:
        s = int(match.group(1))
        return (s, s)

    return (0, 0)


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Main Deck Tribute & Ritual Summoning
# -----------------------------------------------------------------------------

def is_ritual_monster(card: Dict[str, Any]) -> bool:
    """Returns True if the card is a Ritual Monster."""
    ctype = (card.get("card_type") or "").lower()
    csub = (card.get("card_subtype") or "").lower()
    return "ritual" in ctype or "ritual" in csub


def is_tribute_monster(card: Dict[str, Any]) -> bool:
    """
    Returns True if the card requires 1 or more Tributes for Normal Summon.
    - Level 1-4: 0 Tributes
    - Level 5-6: 1 Tribute
    - Level 7+: 2+ Tributes
    - Extra Deck & Ritual monsters are special summoned and not tribute monsters.
    """
    if is_extra_deck_card(card) or is_ritual_monster(card):
        return False
    ctype = (card.get("card_type") or "").lower()
    if ctype != "monster":
        return False
    lvl = card.get("level_or_rank_or_link") or card.get("level") or 0
    return lvl >= 5


def get_tribute_cost(card: Dict[str, Any]) -> int:
    """
    Returns the standard number of tributes required to Normal Summon:
    - Level 1-4: 0
    - Level 5-6: 1
    - Level 7+: 2
    - Non-monsters, Rituals, or Extra Deck cards: 0
    """
    if not is_tribute_monster(card):
        return 0
    lvl = card.get("level_or_rank_or_link") or card.get("level") or 0
    if lvl in (5, 6):
        return 1
    elif lvl >= 7:
        return 2
    return 0


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Field Spell & PSCT Zone Interaction Detectors
# -----------------------------------------------------------------------------

def is_field_spell(card: Dict[str, Any]) -> bool:
    """Returns True if the card is an official Field Spell."""
    ctype = (card.get("card_type") or "").strip().lower()
    csub = (card.get("card_subtype") or "").strip().lower()
    return ctype == "spell" and "field" in csub


def has_field_awareness(card: Dict[str, Any]) -> bool:
    """
    Determines if a card is aware of or interacts with Field Spells:
    - Directly by being a Field Spell itself, or
    - By mentioning Field Spell keywords in its effect text.
    """
    if is_field_spell(card):
        return True

    text = (card.get("effect_text") or "").lower()
    keywords = ["field spell", "field zone", "in the field", "on the field", "while a field"]
    return any(kw in text for kw in keywords)


def has_graveyard_interaction(card: Dict[str, Any]) -> bool:
    """Returns True if the card interacts with the Graveyard / GY."""
    text = f"{card.get('effect_text') or ''} {card.get('pendulum_effect') or ''}".lower()
    keywords = ["graveyard", " gy", "(gy)", "from your gy", "to the gy", "in your gy"]
    return any(kw in text for kw in keywords)


def has_banishment_interaction(card: Dict[str, Any]) -> bool:
    """Returns True if the card interacts with banished cards or banishing."""
    text = f"{card.get('effect_text') or ''} {card.get('pendulum_effect') or ''}".lower()
    keywords = ["banish", "banished", "face-down banished", "banish it"]
    return any(kw in text for kw in keywords)


def has_extra_monster_zone_interaction(card: Dict[str, Any]) -> bool:
    """Returns True if the card references or points to the Extra Monster Zone (EMZ)."""
    text = f"{card.get('effect_text') or ''} {card.get('pendulum_effect') or ''}".lower()
    keywords = ["extra monster zone", "emz", "points to", "co-link", "linked"]
    return any(kw in text for kw in keywords) or "link" in (card.get("card_subtype") or "").lower()


def has_pendulum_zone_interaction(card: Dict[str, Any]) -> bool:
    """Returns True if the card interacts with or occupies the Pendulum Zone (PZ)."""
    if "pendulum" in (card.get("card_subtype") or "").lower():
        return True
    text = f"{card.get('effect_text') or ''}".lower()
    return "pendulum zone" in text or "pendulum scale" in text


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "is_extra_deck_card",
    "is_extra_deck_pendulum",
    "is_main_deck_pendulum",
    "get_pendulum_scales",
    "is_ritual_monster",
    "is_tribute_monster",
    "get_tribute_cost",
    "is_field_spell",
    "has_field_awareness",
    "has_graveyard_interaction",
    "has_banishment_interaction",
    "has_extra_monster_zone_interaction",
    "has_pendulum_zone_interaction",
]

