#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator SQLite CDB Compiler Diagnostic Test Suite
=============================================================================
Asserts:
1. Strict bitmask compilation across all monster summoning classes and spell speeds.
2. 32-bit integer bit-packing for Pendulum Scales and Level/Rank/Link Rating.
3. Link arrow octal mapping in place of DEF for Link monsters.
4. Correct text formatting for split Pendulum Effect / Monster Effect strings.
5. End-to-end SQLite CDB compilation with datas/texts schema verification.
=============================================================================
"""

import pytest
import sqlite3
import tempfile
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from cdb_builder import (
    parse_card_type, parse_attribute, parse_race,
    parse_level_and_scale, parse_link_arrows, format_card_description,
    build_cdb
)
from constants import (
    TYPE_MONSTER, TYPE_NORMAL, TYPE_EFFECT, TYPE_FUSION, TYPE_RITUAL,
    TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK, TYPE_TUNER,
    TYPE_SPELL, TYPE_QUICKPLAY, TYPE_CONTINUOUS, TYPE_EQUIP, TYPE_FIELD,
    TYPE_TRAP, TYPE_COUNTER,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, ATTRIBUTE_FIRE,
    RACE_WARRIOR, RACE_DRAGON, RACE_SPELLCASTER,
    LINK_BL, LINK_BR, LINK_T, LINK_L, LINK_R
)


# =============================================================================
# 1. Card Classification & Subtype Bitmask Parsing Tests
# =============================================================================

def test_parse_monster_summoning_mechanics(diag):
    """Verify bitmask parsing across all major monster card classifications."""
    # Xyz Effect Monster
    xyz_mask = parse_card_type("Monster", "Effect Xyz")
    diag.assert_bitmask_contains(xyz_mask, TYPE_MONSTER, "TYPE_MONSTER")
    diag.assert_bitmask_contains(xyz_mask, TYPE_EFFECT, "TYPE_EFFECT")
    diag.assert_bitmask_contains(xyz_mask, TYPE_XYZ, "TYPE_XYZ")

    # Link Monster
    link_mask = parse_card_type("Monster", "Effect Link")
    diag.assert_bitmask_contains(link_mask, TYPE_MONSTER, "TYPE_MONSTER")
    diag.assert_bitmask_contains(link_mask, TYPE_LINK, "TYPE_LINK")

    # Synchro Tuner Monster
    synchro_tuner = parse_card_type("Monster", "Effect Synchro Tuner")
    diag.assert_bitmask_contains(synchro_tuner, TYPE_SYNCHRO, "TYPE_SYNCHRO")
    diag.assert_bitmask_contains(synchro_tuner, TYPE_TUNER, "TYPE_TUNER")

    # Fusion Monster
    fusion_mask = parse_card_type("Monster", "Fusion Effect")
    diag.assert_bitmask_contains(fusion_mask, TYPE_FUSION, "TYPE_FUSION")

    # Normal Monster
    normal_mask = parse_card_type("Monster", "Normal")
    diag.assert_bitmask_contains(normal_mask, TYPE_NORMAL, "TYPE_NORMAL")
    assert not (normal_mask & TYPE_EFFECT), "Normal monster must not have TYPE_EFFECT flag!"


def test_parse_spell_and_trap_speeds(diag):
    """Verify bitmask resolution for various spell and trap properties."""
    # Quick-Play Spell
    qp_spell = parse_card_type("Spell", "Quick-Play")
    diag.assert_bitmask_contains(qp_spell, TYPE_SPELL, "TYPE_SPELL")
    diag.assert_bitmask_contains(qp_spell, TYPE_QUICKPLAY, "TYPE_QUICKPLAY")

    # Field Spell
    field_spell = parse_card_type("Spell", "Field")
    diag.assert_bitmask_contains(field_spell, TYPE_SPELL, "TYPE_SPELL")
    diag.assert_bitmask_contains(field_spell, TYPE_FIELD, "TYPE_FIELD")

    # Continuous Trap
    cont_trap = parse_card_type("Trap", "Continuous")
    diag.assert_bitmask_contains(cont_trap, TYPE_TRAP, "TYPE_TRAP")
    diag.assert_bitmask_contains(cont_trap, TYPE_CONTINUOUS, "TYPE_CONTINUOUS")

    # Counter Trap
    counter_trap = parse_card_type("Trap", "Counter")
    diag.assert_bitmask_contains(counter_trap, TYPE_TRAP, "TYPE_TRAP")
    diag.assert_bitmask_contains(counter_trap, TYPE_COUNTER, "TYPE_COUNTER")


def test_parse_card_type_failpoints():
    """Verify resilient handling of malformed, None, or empty classification inputs."""
    assert parse_card_type(None, None) == 0
    assert parse_card_type("", "") == 0
    assert parse_card_type("InvalidCategory", "Subtype") == 0

    # Case insensitivity checks
    case_mask = parse_card_type("mOnStEr", "eFfEcT xYz")
    assert case_mask & TYPE_XYZ


# =============================================================================
# 2. Attribute and Race Parsing Tests
# =============================================================================

def test_parse_attribute():
    """Verify parsing of elemental attribute strings with whitespace and casing resilience."""
    assert parse_attribute("LIGHT") == ATTRIBUTE_LIGHT
    assert parse_attribute("  dark  ") == ATTRIBUTE_DARK
    assert parse_attribute("Fire") == ATTRIBUTE_FIRE
    assert parse_attribute(None) == 0
    assert parse_attribute("UNKNOWN_ELEMENT") == 0


def test_parse_race():
    """Verify monster race parsing with hyphens, spaces, and edge cases."""
    assert parse_race("Warrior") == RACE_WARRIOR
    assert parse_race("Dragon") == RACE_DRAGON
    assert parse_race("Spellcaster") == RACE_SPELLCASTER
    assert parse_race(None) == 0
    assert parse_race("AlienSpecies") == 0


# =============================================================================
# 3. Level, Rank, and Pendulum Scale Bit-Packing Tests
# =============================================================================

def test_parse_level_standard():
    """Verify that non-pendulum monsters encode their level into the lowest byte."""
    assert parse_level_and_scale(8, None, "Effect") == 8
    assert parse_level_and_scale(4, None, "Normal") == 4
    assert parse_level_and_scale(12, None, "Fusion") == 12
    assert parse_level_and_scale(None, None, "Spell") == 0


def test_parse_level_and_scale_pendulum(diag):
    """Verify 32-bit bit-packing of Left Scale, Right Scale, and Level for Pendulum cards."""
    # Level 4 monster with Scale 7
    packed = parse_level_and_scale(4, 7, "Pendulum")
    level = packed & 0xFF
    right_scale = (packed >> 16) & 0xFF
    left_scale = (packed >> 24) & 0xFF

    assert level == 4, f"Extracted level was {level}, expected 4"
    diag.assert_pendulum_scale_valid(left_scale)
    diag.assert_pendulum_scale_valid(right_scale)
    assert left_scale == 7
    assert right_scale == 7

    # Boundary test: Level 1 with Scale 0
    packed_zero = parse_level_and_scale(1, 0, "Pendulum")
    assert (packed_zero & 0xFF) == 1
    assert ((packed_zero >> 16) & 0xFF) == 0
    assert ((packed_zero >> 24) & 0xFF) == 0

    # Boundary test: Level 10 with Scale 13
    packed_high = parse_level_and_scale(10, 13, "Pendulum")
    assert (packed_high & 0xFF) == 10
    assert ((packed_high >> 16) & 0xFF) == 13
    assert ((packed_high >> 24) & 0xFF) == 13


def test_parse_link_rating_does_not_pack_scales():
    """Verify that Link monsters store the pure integer rating without scale shift."""
    link_rating = parse_level_and_scale(3, None, "Link")
    assert link_rating == 3
    assert (link_rating >> 16) == 0, "Link rating must not have shifted scale bits!"


# =============================================================================
# 4. Link Arrow Notation Parsing Tests
# =============================================================================

def test_parse_link_arrows():
    """Verify Link Arrow string parsing with various delimiters and whitespace."""
    mask = parse_link_arrows("BL,BR,T")
    assert mask == (LINK_BL | LINK_BR | LINK_T)

    # Semicolon delimiter test
    semi_mask = parse_link_arrows("L; R; T")
    assert semi_mask == (LINK_L | LINK_R | LINK_T)

    # Resilient failpoint: ignore invalid arrow names without crashing
    dirty_mask = parse_link_arrows("BL, INVALID_ARROW, BR")
    assert dirty_mask == (LINK_BL | LINK_BR)

    assert parse_link_arrows("") == 0
    assert parse_link_arrows(None) == 0


# =============================================================================
# 5. Card Text Formatting Tests
# =============================================================================

def test_format_card_description():
    """Verify standard text and combined Pendulum text formatting."""
    normal_text = "Draw 2 cards, then discard 1 card."
    assert format_card_description(normal_text, None) == normal_text

    # Pendulum combined description format
    pend_desc = format_card_description("Monster effect here.", "Scale effect here.")
    assert "[ Pendulum Effect ]" in pend_desc
    assert "Scale effect here." in pend_desc
    assert "----------------------------------------" in pend_desc
    assert "[ Monster Effect ]" in pend_desc
    assert "Monster effect here." in pend_desc


# =============================================================================
# 6. Full End-to-End SQLite CDB Compilation Integration Test
# =============================================================================

def test_build_cdb_integration(mock_db, sample_cards):
    """Verify end-to-end compilation from SQLite Story DB to binary CDB file."""
    # 1. Insert test card into the in-memory database
    card = sample_cards["xyz"]
    mock_db.execute("""
        INSERT INTO custom_cards (
            id, name, card_type, card_subtype, attribute, monster_type,
            level_or_rank_or_link, scale, atk, def, link_arrows,
            effect_text, pendulum_effect
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        card["id"], card["name"], card["card_type"], card["card_subtype"],
        card["attribute"], card["monster_type"], card["level_or_rank_or_link"],
        card["scale"], card["atk"], card["def"], card["link_arrows"],
        card["effect_text"], card["pendulum_effect"]
    ))
    mock_db.commit()

    # 2. Save in-memory DB to a temporary file so build_cdb can connect
    with tempfile.NamedTemporaryFile("wb", suffix=".db", delete=False) as source_f:
        source_path = source_f.name
    with tempfile.NamedTemporaryFile("wb", suffix=".cdb", delete=False) as target_f:
        cdb_path = target_f.name

    try:
        # Dump mock_db to disk
        disk_conn = sqlite3.connect(source_path)
        mock_db.backup(disk_conn)
        disk_conn.close()

        # Run compilation
        compiled = build_cdb(story_db_path=source_path, cdb_output_path=cdb_path)
        assert compiled == 1

        # Inspect generated CDB database
        cdb_conn = sqlite3.connect(cdb_path)
        cdb_cur = cdb_conn.cursor()

        # Verify datas table
        cdb_cur.execute("SELECT id, ot, type, atk, def, level, race, attribute FROM datas WHERE id = ?", (card["id"],))
        data_row = cdb_cur.fetchone()
        assert data_row is not None, "Compiled card missing from datas table!"
        cid, ot, ctype, atk, defense, level, race, attr = data_row

        assert cid == card["id"]
        assert ot == 4  # Custom card format identifier
        assert ctype & TYPE_XYZ
        assert atk == 3000
        assert defense == 2500
        assert level == 8
        assert race == RACE_WARRIOR
        assert attr == ATTRIBUTE_LIGHT

        # Verify texts table
        cdb_cur.execute("SELECT id, name, desc FROM texts WHERE id = ?", (card["id"],))
        text_row = cdb_cur.fetchone()
        assert text_row is not None, "Compiled card missing from texts table!"
        assert text_row[1] == card["name"]
        assert "detach 1 material" in text_row[2]

        cdb_conn.close()
    finally:
        if os.path.exists(source_path):
            os.remove(source_path)
        if os.path.exists(cdb_path):
            os.remove(cdb_path)
