# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.visual.analytics
Description:
    Section 4 (Closing Block): Tactical Analytics & Master Rule Legality Engine.
    Performs deep profiling on a deck:
    - Main, Extra, Side sections, and monster/spell/trap ratios.
    - Level curves, Tribute curves (1-4, 5-6, 7+), and Extra Deck mechanics.
    - Elemental attributes and monster species distribution.
    - Official booster rarity distribution.
    - Field Awareness engine & hypergeometric opening hand probabilities.
    - Official Master Rule 5 construction constraints validation.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import List, Dict, Any

from ..foundation.constants import (
    STANDARD_MIN_MAIN_DECK,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
    STANDARD_MAX_SIDE_DECK,
    MAX_COPIES_PER_CARD,
    SET_1_CARD_COUNT,
    SET_1_MAIN_DECK_EXPECTED,
    SET_1_EXTRA_DECK_EXPECTED,
)
from ..foundation.classifier import is_extra_deck_card, is_field_spell, has_field_awareness
from ..foundation.math import calculate_opening_hand_prob
from ..foundation.types import DeckAnalysisResult, LegalityResult

# =============================================================================
# BLOCK 3: BODY BLOCK (Tactical Profiling & Legality Verification Engine)
# =============================================================================


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Deep Tactical Ratio & Curve Profiling
# -----------------------------------------------------------------------------

def analyze_deck_structure(cards: List[Dict[str, Any]]) -> DeckAnalysisResult:
    """
    Performs in-depth tactical telemetry and legal structure validation on a deck.

    Analytical Dimensions:
    1. Deck Sections: Main, Extra, Side, and Total counts.
    2. Primary Types: Monster, Spell, and Trap counts.
    3. Level & Tribute Curves:
       - No Tribute: Level 1 to 4 Normal summonable monsters
       - 1 Tribute: Level 5 to 6 monsters
       - 2+ Tributes: Level 7+ boss monsters
       - Extra Deck Mechanics: Fusions, Synchros, Xyz, and Links
    4. Elemental Attributes: DIVINE, DARK, LIGHT, EARTH, WATER, FIRE, WIND.
    5. Monster Species / Races: Divine-Beast, Zombie, Fiend, Spellcaster, etc.
    6. Official Rarities: Secret Rare, Ultra Rare, Super Rare, Rare, Common.
    7. Field Awareness Engine & Probability:
       - Detection of Field Spells vs Field-dependent effect cards
       - Hypergeometric opening-hand probability of drawing an active Field Spell
       - Active diagnostic warnings when field-dependent monsters lack Field Spells.
    8. Master Rule Format Assessment: Verifies minimum 40 Main Deck cards.
    """
    main_cards: List[Dict[str, Any]] = []
    extra_cards: List[Dict[str, Any]] = []
    side_cards: List[Dict[str, Any]] = []
    monsters = 0
    spells = 0
    traps = 0

    levels: Dict[str, int] = {}
    tributes = {"level_1_to_4": 0, "level_5_to_6": 0, "level_7_plus": 0}
    extra_mechanics = {"Fusion": 0, "Synchro": 0, "Xyz": 0, "Link": 0}
    attributes: Dict[str, int] = {}
    races: Dict[str, int] = {}
    rarities: Dict[str, int] = {}

    field_spells: List[Dict[str, Any]] = []
    field_dependent_cards: List[Dict[str, Any]] = []
    field_spell_count = 0
    field_dependent_count = 0

    for c in cards:
        cid = c.get("id")
        csub = (c.get("card_subtype") or "").lower()
        qty = c.get("quantity", 1)
        ctype = c.get("card_type")
        section = (c.get("section") or "").upper()
        rarity = c.get("rarity") or "Common"

        rarities[rarity] = rarities.get(rarity, 0) + qty

        is_extra = is_extra_deck_card(c)
        is_field_sp = is_field_spell(c)
        has_field_req = not is_field_sp and has_field_awareness(c)

        if is_field_sp:
            field_spell_count += qty
            field_spells.append({"name": c.get("name", "Unknown"), "quantity": qty, "id": cid})
        elif has_field_req:
            field_dependent_count += qty
            field_dependent_cards.append({"name": c.get("name", "Unknown"), "quantity": qty, "id": cid})

        if section == "SIDE":
            side_cards.append(c)
            continue

        if is_extra:
            extra_cards.append(c)
            if "fusion" in csub:
                extra_mechanics["Fusion"] += qty
            elif "synchro" in csub:
                extra_mechanics["Synchro"] += qty
            elif "xyz" in csub:
                extra_mechanics["Xyz"] += qty
            elif "link" in csub:
                extra_mechanics["Link"] += qty
        else:
            main_cards.append(c)
            if ctype == "Monster":
                monsters += qty
            elif ctype == "Spell":
                spells += qty
            elif ctype == "Trap":
                traps += qty

        if ctype == "Monster":
            attr = c.get("attribute") or "DIVINE"
            attributes[attr] = attributes.get(attr, 0) + qty

            race = c.get("monster_type") or "Unknown"
            races[race] = races.get(race, 0) + qty

            lvl = c.get("level_or_rank_or_link") or c.get("level") or 0
            if "link" in csub:
                lbl = f"Link-{lvl}"
                levels[lbl] = levels.get(lbl, 0) + qty
            elif "xyz" in csub:
                lbl = f"Rank {lvl}"
                levels[lbl] = levels.get(lbl, 0) + qty
            else:
                lbl = f"Level {lvl}"
                levels[lbl] = levels.get(lbl, 0) + qty
                if not is_extra:
                    if lvl <= 4:
                        tributes["level_1_to_4"] += qty
                    elif lvl in (5, 6):
                        tributes["level_5_to_6"] += qty
                    elif lvl >= 7:
                        tributes["level_7_plus"] += qty

    main_count = sum(c.get("quantity", 1) for c in main_cards)
    extra_count = sum(c.get("quantity", 1) for c in extra_cards)
    side_count = sum(c.get("quantity", 1) for c in side_cards)
    total_count = main_count + extra_count + side_count

    is_set_1_standard = (
        main_count == SET_1_MAIN_DECK_EXPECTED and 
        extra_count == SET_1_EXTRA_DECK_EXPECTED
    )

    field_spell_opening_prob = calculate_opening_hand_prob(
        deck_size=main_count,
        target_count=field_spell_count,
        hand_size=5,
        min_hits=1
    )
    starter_monster_opening_prob = calculate_opening_hand_prob(
        deck_size=main_count,
        target_count=tributes.get("level_1_to_4", 0),
        hand_size=5,
        min_hits=1
    )

    if field_dependent_count > 0 and field_spell_count == 0:
        field_status = (
            f"⚠️ **Field Engine Warning**: Contains **{field_dependent_count}** Field-dependent card(s) "
            f"but **0** Field Spells! (Effects cannot trigger without a Field Spell)."
        )
    elif field_dependent_count > 0 and field_spell_count > 0:
        field_status = (
            f"✅ **Field Engine Active**: **{field_spell_count}** Field Spell(s) "
            f"supporting **{field_dependent_count}** Field-aware card(s). "
            f"*(Opening Hand P(Field): {field_spell_opening_prob}%)*"
        )
    elif field_dependent_count == 0 and field_spell_count > 0:
        field_status = (
            f"ℹ️ **Field Utility Active**: **{field_spell_count}** Field Spell(s) "
            f"supporting autonomous cards."
        )
    else:
        field_status = "⚪ **Field Independent**: Strategy functions without relying on Field Spells."

    notes = []
    if main_count < STANDARD_MIN_MAIN_DECK:
        notes.append(
            f"⚠️ **Set 1 Alpha Cardpool Note**: Main Deck has **{main_count}** cards. "
            f"The standard minimum ({STANDARD_MIN_MAIN_DECK}) is relaxed during Set 1 testing ({SET_1_CARD_COUNT} unique cards available)."
        )
    elif main_count > STANDARD_MAX_MAIN_DECK:
        notes.append(f"❌ **Deck Limit Exceeded**: Main Deck has **{main_count}** cards (Max allowed: {STANDARD_MAX_MAIN_DECK}).")

    if extra_count > STANDARD_MAX_EXTRA_DECK:
        notes.append(f"❌ **Extra Deck Exceeded**: Extra Deck has **{extra_count}** cards (Max allowed: {STANDARD_MAX_EXTRA_DECK}).")

    return {
        "total_count": total_count,
        "main_count": main_count,
        "extra_count": extra_count,
        "side_count": side_count,
        "monsters": monsters,
        "spells": spells,
        "traps": traps,
        "main_cards": main_cards,
        "extra_cards": extra_cards,
        "side_cards": side_cards,
        "is_set_1_standard": is_set_1_standard,
        "levels": levels,
        "tributes": tributes,
        "extra_mechanics": extra_mechanics,
        "attributes": attributes,
        "races": races,
        "rarities": rarities,
        "field_spells": field_spells,
        "field_spell_count": field_spell_count,
        "field_dependent_cards": field_dependent_cards,
        "field_dependent_count": field_dependent_count,
        "field_status": field_status,
        "field_opening_prob": field_spell_opening_prob,
        "starter_opening_prob": starter_monster_opening_prob,
        "notes": notes,
    }


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Official Master Rule 5 Construction Legality Verification
# -----------------------------------------------------------------------------

def validate_deck_legality(cards: List[Dict[str, Any]]) -> LegalityResult:
    """
    Validates whether a deck adheres to official Master Rule deck construction constraints:
    - Main Deck: 40 - 60 cards
    - Extra Deck: 0 - 15 cards
    - Side Deck: 0 - 15 cards
    - Copies: Max 3 copies per card name
    """
    analysis = analyze_deck_structure(cards)
    errors: List[str] = []
    warnings: List[str] = []

    main_count = analysis["main_count"]
    extra_count = analysis["extra_count"]
    side_count = analysis["side_count"]

    if main_count < STANDARD_MIN_MAIN_DECK:
        errors.append(f"Main Deck has {main_count} cards (Minimum: {STANDARD_MIN_MAIN_DECK}).")
    elif main_count > STANDARD_MAX_MAIN_DECK:
        errors.append(f"Main Deck has {main_count} cards (Maximum: {STANDARD_MAX_MAIN_DECK}).")

    if extra_count > STANDARD_MAX_EXTRA_DECK:
        errors.append(f"Extra Deck has {extra_count} cards (Maximum: {STANDARD_MAX_EXTRA_DECK}).")

    if side_count > STANDARD_MAX_SIDE_DECK:
        errors.append(f"Side Deck has {side_count} cards (Maximum: {STANDARD_MAX_SIDE_DECK}).")

    card_copies: Dict[str, int] = {}
    for c in cards:
        cname = c.get("name", "Unknown")
        qty = c.get("quantity", 1)
        card_copies[cname] = card_copies.get(cname, 0) + qty

    for name, count in card_copies.items():
        if count > MAX_COPIES_PER_CARD:
            errors.append(f"Card '{name}' has {count} copies (Maximum allowed: {MAX_COPIES_PER_CARD}).")

    if analysis["field_dependent_count"] > 0 and analysis["field_spell_count"] == 0:
        warnings.append(f"Deck runs {analysis['field_dependent_count']} Field-dependent cards with 0 Field Spells.")

    return {
        "is_legal": len(errors) == 0,
        "main_count": main_count,
        "extra_count": extra_count,
        "side_count": side_count,
        "errors": errors,
        "warnings": warnings,
    }


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "analyze_deck_structure",
    "validate_deck_legality",
]

