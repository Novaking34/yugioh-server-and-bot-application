#!/usr/bin/env python3
"""
Unit tests for development/tools/cdb_builder.py parsing functions and binary encoding.
"""

import pytest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from cdb_builder import (
    parse_card_type, parse_attribute, parse_race,
    parse_level_and_scale, parse_link_arrows, format_card_description
)
from constants import (
    TYPE_MONSTER, TYPE_EFFECT, TYPE_XYZ, TYPE_SPELL, TYPE_FIELD,
    TYPE_TRAP, TYPE_COUNTER, ATTRIBUTE_LIGHT, RACE_WARRIOR,
    LINK_BL, LINK_BR
)


def test_parse_card_type():
    """Test parsing card types and subtypes into bitmasks."""
    # Monster Xyz
    xyz_type = parse_card_type("Monster", "Effect Xyz")
    assert xyz_type & TYPE_MONSTER
    assert xyz_type & TYPE_EFFECT
    assert xyz_type & TYPE_XYZ

    # Field Spell
    spell_type = parse_card_type("Spell", "Field")
    assert spell_type & TYPE_SPELL
    assert spell_type & TYPE_FIELD

    # Counter Trap
    trap_type = parse_card_type("Trap", "Counter")
    assert trap_type & TYPE_TRAP
    assert trap_type & TYPE_COUNTER


def test_parse_attribute_and_race():
    """Test attribute and race string parsing."""
    assert parse_attribute("LIGHT") == ATTRIBUTE_LIGHT
    assert parse_attribute(None) == 0

    assert parse_race("Warrior") == RACE_WARRIOR
    assert parse_race(None) == 0


def test_parse_level_and_scale_standard():
    """Test standard level/rank extraction."""
    assert parse_level_and_scale(8, None, "Effect") == 8
    assert parse_level_and_scale(4, None, "Normal") == 4
    assert parse_level_and_scale(None, None, "Spell") == 0


def test_parse_level_and_scale_pendulum():
    """Test bit-packed pendulum scales."""
    # Level 4 with Scale 7
    packed = parse_level_and_scale(4, 7, "Pendulum")
    level = packed & 0xFF
    right_scale = (packed >> 16) & 0xFF
    left_scale = (packed >> 24) & 0xFF

    assert level == 4
    assert right_scale == 7
    assert left_scale == 7


def test_parse_link_arrows():
    """Test parsing Link arrow notation string."""
    mask = parse_link_arrows("BL,BR")
    assert mask == (LINK_BL | LINK_BR)
    assert parse_link_arrows("") == 0
    assert parse_link_arrows(None) == 0


def test_format_card_description():
    """Test formatting card text with and without Pendulum effects."""
    normal_desc = format_card_description("Draw 2 cards.", None)
    assert normal_desc == "Draw 2 cards."

    pend_desc = format_card_description("Monster effect here.", "Scale effect here.")
    assert "[ Pendulum Effect ]" in pend_desc
    assert "Scale effect here." in pend_desc
    assert "[ Monster Effect ]" in pend_desc
    assert "Monster effect here." in pend_desc
