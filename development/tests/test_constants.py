#!/usr/bin/env python3
"""
Unit tests for tools/constants.py bitmasks and identifier mappings.
"""

import pytest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from constants import (
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_EFFECT, TYPE_XYZ, TYPE_LINK,
    TYPE_PENDULUM, ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, RACE_WARRIOR, RACE_DRAGON,
    LINK_B, LINK_BL, LINK_BR, LINK_T, LINK_ARROW_MAP, ATTRIBUTE_MAP, RACE_MAP
)


def test_card_type_bitmasks():
    """Verify bitwise orthogonality of primary card types."""
    assert (TYPE_MONSTER & TYPE_SPELL) == 0
    assert (TYPE_MONSTER & TYPE_TRAP) == 0
    assert (TYPE_SPELL & TYPE_TRAP) == 0

    composite = TYPE_MONSTER | TYPE_EFFECT | TYPE_XYZ
    assert composite & TYPE_MONSTER
    assert composite & TYPE_EFFECT
    assert composite & TYPE_XYZ
    assert not (composite & TYPE_LINK)


def test_attribute_mappings():
    """Verify standard attribute lookups."""
    assert ATTRIBUTE_MAP['light'] == ATTRIBUTE_LIGHT
    assert ATTRIBUTE_MAP['dark'] == ATTRIBUTE_DARK
    assert ATTRIBUTE_MAP.get('invalid_attr', 0) == 0


def test_race_mappings():
    """Verify monster race lookups."""
    assert RACE_MAP['warrior'] == RACE_WARRIOR
    assert RACE_MAP['dragon'] == RACE_DRAGON
    assert RACE_MAP['beast-warrior'] == RACE_MAP['beast warrior']


def test_link_arrow_values():
    """Verify Link arrow bit values and mapping resolution."""
    assert LINK_ARROW_MAP['B'] == LINK_B
    assert LINK_ARROW_MAP['BOTTOM'] == LINK_B
    assert LINK_ARROW_MAP['BL'] == LINK_BL
    assert LINK_ARROW_MAP['BR'] == LINK_BR
    assert LINK_ARROW_MAP['T'] == LINK_T

    # Combined arrows (Bottom-Left and Bottom-Right)
    combined = LINK_ARROW_MAP['BL'] | LINK_ARROW_MAP['BR']
    assert combined & LINK_BL
    assert combined & LINK_BR
    assert not (combined & LINK_T)
