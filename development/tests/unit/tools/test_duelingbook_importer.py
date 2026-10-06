#!/usr/bin/env python3
"""
=============================================================================
Duelingbook Importer & Deck Exporter Diagnostic Test Suite
=============================================================================
Asserts:
1. Generation of non-colliding passcodes strictly in the 50,000,000 range.
2. Accurate mapping of Duelingbook internal monster colors, spell, and trap properties.
3. Robust attribute extraction from both integer and string payloads.
4. Security hardening of the deck filename sanitizer against path traversal.
5. End-to-end card dictionary ingestion into SQLite and FTS5 search index.
=============================================================================
"""

import pytest
import sqlite3
import tempfile
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from duelingbook_importer import (
    generate_custom_passcode, resolve_card_classification,
    resolve_attribute, import_card_data
)
from export_deck import export_deck, sanitize_filename


# =============================================================================
# 1. Custom Passcode Allocation Tests
# =============================================================================

def test_generate_custom_passcode_range(mock_db, diag):
    """Verify that all generated passcodes strictly fall within 50000000-59999999."""
    for _ in range(25):
        code = generate_custom_passcode(mock_db)
        diag.assert_passcode_in_range(code)


def test_generate_custom_passcode_collision_handling(mock_db):
    """Verify that passcode generator retries and avoids collisions with existing DB records."""
    # Pre-populate specific ID
    target_id = 50000001
    mock_db.execute("INSERT INTO custom_cards (id, name, card_type, effect_text) VALUES (?, 'Existing', 'Monster', '')", (target_id,))
    mock_db.commit()

    # Generate new ID
    new_code = generate_custom_passcode(mock_db)
    assert new_code != target_id, "Passcode generator returned an already-allocated ID!"


# =============================================================================
# 2. Duelingbook Classification Mapping Tests
# =============================================================================

def test_resolve_card_classification_monsters():
    """Verify mapping of Duelingbook monster_color integers to category strings."""
    mechanics = [
        (1, "Normal"),
        (2, "Effect"),
        (3, "Ritual"),
        (4, "Fusion"),
        (5, "Synchro"),
        (6, "Xyz"),
        (7, "Pendulum"),
        (8, "Link"),
    ]
    for color_code, expected_sub in mechanics:
        ctype, csub = resolve_card_classification({"card_type": 1, "monster_color": color_code})
        assert ctype == "Monster"
        assert expected_sub in csub, f"Color {color_code}: expected '{expected_sub}', got '{csub}'"


def test_resolve_card_classification_spells_and_traps():
    """Verify mapping of Duelingbook spell & trap properties."""
    # Field Spell (property 5 in DB)
    stype, ssub = resolve_card_classification({"card_type": 2, "property": 5})
    assert stype == "Spell"
    assert ssub == "Field"

    # Counter Trap (property 3 in DB)
    ttype, tsub = resolve_card_classification({"card_type": 3, "property": 3})
    assert ttype == "Trap"
    assert tsub == "Counter"

    # Failpoint: unknown/missing property falls back to Normal
    def_type, def_sub = resolve_card_classification({"card_type": 2})
    assert def_type == "Spell"
    assert def_sub == "Normal"


def test_resolve_attribute():
    """Verify attribute resolution from integer codes and string names."""
    # Integer mappings: 1=EARTH, 2=WATER, 3=FIRE, 4=WIND, 5=LIGHT, 6=DARK, 7=DIVINE
    assert resolve_attribute({"attribute": 5}) == "LIGHT"
    assert resolve_attribute({"attribute": 6}) == "DARK"
    assert resolve_attribute({"attribute": 3}) == "FIRE"

    # String pass-through with normalization
    assert resolve_attribute({"attribute": "light"}) == "LIGHT"
    assert resolve_attribute({"attribute": "DARK"}) == "DARK"

    # Failpoint: empty/invalid returns None
    assert resolve_attribute({}) is None
    assert resolve_attribute({"attribute": None}) is None


# =============================================================================
# 3. Security & Filename Sanitization Tests
# =============================================================================

def test_sanitize_filename_security():
    """Verify removal of dangerous filesystem characters and path traversal attempts."""
    # Path traversal attack
    traversal = "../../etc/passwd"
    clean_traversal = sanitize_filename(traversal)
    assert "/" not in clean_traversal
    assert ".." not in clean_traversal
    assert "etcpasswd" in clean_traversal

    # Hostile characters: <>:"/\|?*
    hostile = 'Deck <1> : "Ultimate" *Special* | Test?'
    clean_hostile = sanitize_filename(hostile)
    for bad_char in '<>:"/\\|?*':
        assert bad_char not in clean_hostile, f"Hostile character '{bad_char}' survived sanitization!"

    # Safe name passes through unchanged
    safe_name = "Sol Radiance - Valen Signature"
    assert sanitize_filename(safe_name) == safe_name


# =============================================================================
# 4. End-to-End Ingestion Integration Test
# =============================================================================

def test_import_card_data_integration(mock_db):
    """Verify ingestion of a complete Duelingbook card dictionary into SQLite & FTS5."""
    card_dict = {
        "name": "Astral Resonance Dragon",
        "card_type": 1,
        "monster_color": 6,  # Xyz
        "attribute": 5,      # LIGHT
        "type": "Dragon",
        "level": 8,
        "atk": 3000,
        "def": 2500,
        "effect": "2 Level 8 LIGHT monsters\nOnce per turn: Detach 1 material; destroy 1 card on the field.",
        "author": "ProfSeanEx",
        "id": "db_test_9001"
    }

    imported_id = import_card_data(card_dict, conn=mock_db, sync_simulator=False)
    assert 50000000 <= imported_id <= 59999999

    # Verify custom_cards record
    cur = mock_db.cursor()
    cur.execute("SELECT name, card_type, card_subtype, atk, def, attribute FROM custom_cards WHERE id = ?", (imported_id,))
    row = cur.fetchone()
    assert row is not None, "Imported card not found in custom_cards table!"
    assert row[0] == "Astral Resonance Dragon"
    assert row[1] == "Monster"
    assert row[2] == "Xyz"
    assert row[3] == 3000
    assert row[4] == 2500
    assert row[5] == "LIGHT"

    # Verify Full-Text Search (FTS5) table indexed the card
    cur.execute("SELECT rowid FROM cards_fts WHERE cards_fts MATCH 'Resonance'", ())
    fts_row = cur.fetchone()
    assert fts_row is not None, "Imported card was not indexed in FTS5 search table!"
