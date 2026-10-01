#!/usr/bin/env python3
"""
Unit tests for tools/duelingbook_importer.py and tools/export_deck.py.
"""

import pytest
import sqlite3
import sys
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from duelingbook_importer import (
    generate_custom_passcode, resolve_card_classification,
    resolve_attribute, import_card_data
)
from export_deck import export_deck, sanitize_filename


def test_sanitize_filename():
    """Verify filename cleaning for .ydk export."""
    assert sanitize_filename("Sol Radiance - Valen Signature") == "Sol Radiance - Valen Signature"
    assert sanitize_filename("Deck / With * Illegal : Chars?") == "Deck  With  Illegal  Chars"


def test_resolve_card_classification():
    """Verify mapping of Duelingbook integer types to strings."""
    ctype, csub = resolve_card_classification({
        "card_type": 1,
        "monster_color": 6  # Xyz
    })
    assert ctype == "Monster"
    assert csub == "Xyz"

    ctype2, csub2 = resolve_card_classification({
        "card_type": 2,
        "property": 5  # Field Spell
    })
    assert ctype2 == "Spell"
    assert csub2 == "Field"


def test_resolve_attribute():
    """Verify attribute resolution."""
    assert resolve_attribute({"attribute": 5}) == "LIGHT"
    assert resolve_attribute({"attribute": "DARK"}) == "DARK"
    assert resolve_attribute({}) is None


def test_generate_custom_passcode():
    """Verify generated passcode falls in the reserved 50000000-59999999 range."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE custom_cards (id INTEGER PRIMARY KEY)")

    code = generate_custom_passcode(conn)
    assert 50000000 <= code <= 59999999
    conn.close()
