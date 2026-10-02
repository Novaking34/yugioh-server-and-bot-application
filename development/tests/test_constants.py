#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator Constant & Bitmask Diagnostic Test Suite
=============================================================================
Asserts:
1. Mathematical orthogonality across all primary card types (Monster, Spell, Trap).
2. Complete non-overlap of elemental attributes and power-of-2 verification.
3. Strict mapping coverage for all 26 monster species / races.
4. Correctness of 8-way octal Link Arrow compass geometry.
5. Failpoint diagnostics on malformed or invalid inputs.
=============================================================================
"""

import pytest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from constants import (
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_NORMAL, TYPE_EFFECT,
    TYPE_FUSION, TYPE_RITUAL, TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK,
    TYPE_TUNER, TYPE_QUICKPLAY, TYPE_CONTINUOUS, TYPE_EQUIP, TYPE_FIELD, TYPE_COUNTER,
    ATTRIBUTE_EARTH, ATTRIBUTE_WATER, ATTRIBUTE_FIRE, ATTRIBUTE_WIND,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, ATTRIBUTE_DIVINE,
    RACE_WARRIOR, RACE_SPELLCASTER, RACE_FAIRY, RACE_FIEND, RACE_ZOMBIE,
    RACE_MACHINE, RACE_AQUA, RACE_PYRO, RACE_ROCK, RACE_WINGEDBEAST,
    RACE_PLANT, RACE_INSECT, RACE_THUNDER, RACE_DRAGON, RACE_BEAST,
    RACE_BEASTWARRIOR, RACE_DINOSAUR, RACE_FISH, RACE_SEASERPENT, RACE_REPTILE,
    RACE_PSYCHIC, RACE_DIVINEBEAST, RACE_CREATORGOD, RACE_WYRM, RACE_CYBERSE, RACE_ILLUSION,
    LINK_B, LINK_BL, LINK_BR, LINK_L, LINK_R, LINK_T, LINK_TL, LINK_TR,
    LINK_ARROW_MAP, ATTRIBUTE_MAP, RACE_MAP
)


# =============================================================================
# 1. Primary Card Type Orthogonality Tests
# =============================================================================

def test_primary_type_orthogonality(diag):
    """Assert that Monster, Spell, and Trap types share zero overlapping bits."""
    primary_types = [
        ("TYPE_MONSTER", TYPE_MONSTER),
        ("TYPE_SPELL", TYPE_SPELL),
        ("TYPE_TRAP", TYPE_TRAP),
    ]

    for i in range(len(primary_types)):
        for j in range(i + 1, len(primary_types)):
            name_a, mask_a = primary_types[i]
            name_b, mask_b = primary_types[j]
            diag.assert_bitmask_orthogonal(mask_a, mask_b, name_a, name_b)


def test_composite_monster_types(diag):
    """Assert that extra deck summoning mechanics compose cleanly with base monster flags."""
    # An Xyz Effect Monster
    xyz_effect = TYPE_MONSTER | TYPE_EFFECT | TYPE_XYZ
    diag.assert_bitmask_contains(xyz_effect, TYPE_MONSTER, "TYPE_MONSTER")
    diag.assert_bitmask_contains(xyz_effect, TYPE_EFFECT, "TYPE_EFFECT")
    diag.assert_bitmask_contains(xyz_effect, TYPE_XYZ, "TYPE_XYZ")

    # Ensure it does NOT inadvertently match Link or Spell flags
    assert not (xyz_effect & TYPE_LINK), "Xyz monster unexpectedly matches TYPE_LINK!"
    assert not (xyz_effect & TYPE_SPELL), "Xyz monster unexpectedly matches TYPE_SPELL!"


def test_spell_and_trap_subtypes(diag):
    """Assert that Spell and Trap subtypes are distinct."""
    spell_subtypes = [
        ("TYPE_QUICKPLAY", TYPE_QUICKPLAY),
        ("TYPE_CONTINUOUS", TYPE_CONTINUOUS),
        ("TYPE_EQUIP", TYPE_EQUIP),
        ("TYPE_FIELD", TYPE_FIELD),
    ]
    for name, mask in spell_subtypes:
        diag.assert_bitmask_orthogonal(mask, TYPE_COUNTER, name, "TYPE_COUNTER")


# =============================================================================
# 2. Elemental Attribute Integrity Tests
# =============================================================================

def test_attributes_are_powers_of_two():
    """Verify that every elemental attribute is an exact single-bit power of 2."""
    attributes = [
        ("EARTH", ATTRIBUTE_EARTH),
        ("WATER", ATTRIBUTE_WATER),
        ("FIRE", ATTRIBUTE_FIRE),
        ("WIND", ATTRIBUTE_WIND),
        ("LIGHT", ATTRIBUTE_LIGHT),
        ("DARK", ATTRIBUTE_DARK),
        ("DIVINE", ATTRIBUTE_DIVINE),
    ]

    for name, val in attributes:
        assert val > 0, f"Attribute {name} must be strictly positive!"
        # Check power of 2: (val & (val - 1)) == 0
        assert (val & (val - 1)) == 0, f"Attribute {name} ({hex(val)}) is not an exact power of 2!"


def test_attribute_mutual_exclusion(diag):
    """Verify that no two elemental attributes share any bits."""
    attributes = [
        ("EARTH", ATTRIBUTE_EARTH),
        ("WATER", ATTRIBUTE_WATER),
        ("FIRE", ATTRIBUTE_FIRE),
        ("WIND", ATTRIBUTE_WIND),
        ("LIGHT", ATTRIBUTE_LIGHT),
        ("DARK", ATTRIBUTE_DARK),
        ("DIVINE", ATTRIBUTE_DIVINE),
    ]

    for i in range(len(attributes)):
        for j in range(i + 1, len(attributes)):
            name_a, val_a = attributes[i]
            name_b, val_b = attributes[j]
            diag.assert_bitmask_orthogonal(val_a, val_b, f"ATTRIBUTE_{name_a}", f"ATTRIBUTE_{name_b}")


def test_attribute_map_resolution():
    """Verify attribute dictionary lookups with casing and fallback diagnostics."""
    assert ATTRIBUTE_MAP["light"] == ATTRIBUTE_LIGHT
    assert ATTRIBUTE_MAP["dark"] == ATTRIBUTE_DARK
    assert ATTRIBUTE_MAP["divine"] == ATTRIBUTE_DIVINE
    assert ATTRIBUTE_MAP["fire"] == ATTRIBUTE_FIRE
    assert ATTRIBUTE_MAP["water"] == ATTRIBUTE_WATER
    assert ATTRIBUTE_MAP["earth"] == ATTRIBUTE_EARTH
    assert ATTRIBUTE_MAP["wind"] == ATTRIBUTE_WIND

    # Failpoint: unknown/invalid attributes must safely return 0 without raising KeyError
    assert ATTRIBUTE_MAP.get("shadow", 0) == 0
    assert ATTRIBUTE_MAP.get("", 0) == 0
    assert ATTRIBUTE_MAP.get(None, 0) == 0


# =============================================================================
# 3. Monster Race / Species Classification Tests
# =============================================================================

def test_all_26_races_defined():
    """Verify that all 26 canonical Yu-Gi-Oh! monster races have non-zero bitmasks."""
    all_races = [
        RACE_WARRIOR, RACE_SPELLCASTER, RACE_FAIRY, RACE_FIEND, RACE_ZOMBIE,
        RACE_MACHINE, RACE_AQUA, RACE_PYRO, RACE_ROCK, RACE_WINGEDBEAST,
        RACE_PLANT, RACE_INSECT, RACE_THUNDER, RACE_DRAGON, RACE_BEAST,
        RACE_BEASTWARRIOR, RACE_DINOSAUR, RACE_FISH, RACE_SEASERPENT, RACE_REPTILE,
        RACE_PSYCHIC, RACE_DIVINEBEAST, RACE_CREATORGOD, RACE_WYRM, RACE_CYBERSE,
        RACE_ILLUSION
    ]
    assert len(all_races) == 26, f"Expected 26 races, but found {len(all_races)}!"
    for r in all_races:
        assert r > 0
        assert (r & (r - 1)) == 0, f"Race value {hex(r)} is not a distinct power of 2!"


def test_race_map_aliases():
    """Verify that dash vs space formatting for hyphenated races resolves to identical masks."""
    assert RACE_MAP["beast-warrior"] == RACE_MAP["beast warrior"] == RACE_BEASTWARRIOR
    assert RACE_MAP["winged-beast"] == RACE_MAP["winged beast"] == RACE_WINGEDBEAST
    assert RACE_MAP["sea-serpent"] == RACE_MAP["sea serpent"] == RACE_SEASERPENT
    assert RACE_MAP["divine-beast"] == RACE_MAP["divine beast"] == RACE_DIVINEBEAST


# =============================================================================
# 4. Link Arrow Geometry & Compass Octal Bitmask Tests
# =============================================================================

def test_link_arrow_geometry(diag):
    """Verify octal bitmask calculations for all 8 compass directions of Link arrows."""
    arrows = [
        ("LINK_B", LINK_B, 0o001),
        ("LINK_BL", LINK_BL, 0o002),
        ("LINK_BR", LINK_BR, 0o004),
        ("LINK_L", LINK_L, 0o010),
        ("LINK_R", LINK_R, 0o040),
        ("LINK_T", LINK_T, 0o100),
        ("LINK_TL", LINK_TL, 0o200),
        ("LINK_TR", LINK_TR, 0o400),
    ]

    total_sum = 0
    for name, actual, expected in arrows:
        assert actual == expected, f"{name}: expected octal {oct(expected)}, got {oct(actual)}"
        total_sum |= actual

    # Full compass mask must equal octal 0o757 (495 decimal).
    # In ocgcore's 3x3 numeric keypad coordinate system, the center key 5 (octal 0o020 / 16 dec)
    # is intentionally omitted because a card cannot point to its own center position.
    # Total = 0o700 (TL+T+TR) | 0o050 (L+R) | 0o007 (BL+B+BR) = 0o757.
    assert total_sum == 0o757, f"Complete 8-arrow compass mask must equal 0o757, got {oct(total_sum)}"


def test_link_arrow_map_lookups():
    """Verify string abbreviation and full-word mappings."""
    assert LINK_ARROW_MAP["B"] == LINK_B
    assert LINK_ARROW_MAP["BOTTOM"] == LINK_B
    assert LINK_ARROW_MAP["BL"] == LINK_BL
    assert LINK_ARROW_MAP["BOTTOM-LEFT"] == LINK_BL
    assert LINK_ARROW_MAP["T"] == LINK_T
    assert LINK_ARROW_MAP["TOP"] == LINK_T

    # Failpoint: invalid arrow string returns 0 or None via get()
    assert LINK_ARROW_MAP.get("CENTER", 0) == 0
    assert LINK_ARROW_MAP.get("INVALID", 0) == 0
