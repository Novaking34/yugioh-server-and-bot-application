#!/usr/bin/env python3
"""
=============================================================================
System Diagnostic & Debugging Tool Assertion Test Suite
=============================================================================
Asserts:
1. PlatformDiagnostics accurately detects and reports real failpoints.
2. Deliberate schema corruptions and missing tables trigger DiagnosticResult FAIL status.
3. Out-of-bounds Pendulum scales (e.g., scale 15, scale -1) are isolated as failpoints.
4. Malformed Link arrow bitmasks (e.g., center key 0o020 or out-of-range 0o1000) are flagged.
5. Corrupted .ydk deck files and missing headers trigger descriptive failpoint messages.
=============================================================================
"""

import pytest
import sqlite3
import tempfile
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from debug_diagnostics import PlatformDiagnostics, DiagnosticResult


# =============================================================================
# 1. Database Diagnostic Audit Tests
# =============================================================================

def test_diagnostic_database_missing_file():
    """Verify that a non-existent database file triggers a fatal failpoint."""
    diag = PlatformDiagnostics(db_path="/tmp/non_existent_ygo_db.db")
    result = diag.audit_database()

    assert result.status == "FAIL"
    assert len(result.failpoints) > 0
    assert "Story database not found" in result.failpoints[0]
    assert len(result.suggestions) > 0


def test_diagnostic_database_missing_table():
    """Verify that a database missing required tables (e.g. cards_fts) triggers failpoints."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        conn = sqlite3.connect(db_path)
        # Create minimal table missing cards_fts, factions, characters
        conn.execute("CREATE TABLE custom_cards (id INTEGER PRIMARY KEY, name TEXT);")
        conn.commit()
        conn.close()

        diag = PlatformDiagnostics(db_path=db_path)
        result = diag.audit_database()

        assert result.status == "FAIL"
        missing_tables = [fp for fp in result.failpoints if "Missing required table" in fp]
        assert len(missing_tables) >= 4, f"Expected at least 4 missing tables, got {len(missing_tables)}"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# =============================================================================
# 2. Card Metadata & Bitmask Failpoint Detection Tests
# =============================================================================

def test_diagnostic_card_bitmasks_catches_invalid_passcode():
    """Verify that out-of-range passcodes (<50000000 or >59999999) are flagged."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE custom_cards (
                id INTEGER PRIMARY KEY, name TEXT, card_type TEXT, card_subtype TEXT,
                attribute TEXT, monster_type TEXT, level_or_rank_or_link INTEGER,
                scale INTEGER, atk INTEGER, def INTEGER, link_arrows TEXT
            );
        """)
        # Insert out-of-range card
        conn.execute("INSERT INTO custom_cards (id, name, card_type) VALUES (12345678, 'Invalid ID Card', 'Monster');")
        conn.commit()
        conn.close()

        diag = PlatformDiagnostics(db_path=db_path)
        result = diag.audit_card_bitmasks()

        assert result.status == "FAIL"
        assert any("out of custom card range" in fp for fp in result.failpoints)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_diagnostic_card_bitmasks_catches_invalid_pendulum_scale():
    """Verify that Pendulum monsters with scale > 13 or negative scales trigger failpoints."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE custom_cards (
                id INTEGER PRIMARY KEY, name TEXT, card_type TEXT, card_subtype TEXT,
                attribute TEXT, monster_type TEXT, level_or_rank_or_link INTEGER,
                scale INTEGER, atk INTEGER, def INTEGER, link_arrows TEXT
            );
        """)
        # Insert invalid scale 15
        conn.execute("""
            INSERT INTO custom_cards (id, name, card_type, card_subtype, scale)
            VALUES (50000001, 'Broken Scale Beast', 'Monster', 'Pendulum Effect', 15);
        """)
        conn.commit()
        conn.close()

        diag = PlatformDiagnostics(db_path=db_path)
        result = diag.audit_card_bitmasks()

        assert result.status == "FAIL"
        assert any("invalid scale: 15" in fp for fp in result.failpoints)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_diagnostic_card_bitmasks_catches_invalid_link_arrows():
    """Verify that Link monsters with arrows outside octal 0o757 (e.g. center bit 0o020) are flagged."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE custom_cards (
                id INTEGER PRIMARY KEY, name TEXT, card_type TEXT, card_subtype TEXT,
                attribute TEXT, monster_type TEXT, level_or_rank_or_link INTEGER,
                scale INTEGER, atk INTEGER, def INTEGER, link_arrows INTEGER
            );
        """)
        # Octal 0o777 includes center bit 0o020 (16 dec), which is illegal for link arrows!
        conn.execute("""
            INSERT INTO custom_cards (id, name, card_type, card_subtype, link_arrows, level_or_rank_or_link)
            VALUES (50000002, 'Impossible Link Monster', 'Monster', 'Link Effect', 511, 8);
        """)
        conn.commit()
        conn.close()

        diag = PlatformDiagnostics(db_path=db_path)
        result = diag.audit_card_bitmasks()

        assert result.status == "FAIL"
        assert any("contains invalid bits outside octal 0o757" in fp for fp in result.failpoints)
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# =============================================================================
# 3. Story Deck Failpoint Detection Tests
# =============================================================================

def test_diagnostic_decks_catches_missing_section_headers():
    """Verify that a .ydk file lacking #main or !side triggers a failpoint."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        broken_deck = os.path.join(tmp_dir, "broken.ydk")
        with open(broken_deck, "w", encoding="utf-8") as f:
            f.write("50000001\n50000002\n")

        diag = PlatformDiagnostics(decks_dir=tmp_dir)
        result = diag.audit_decks()

        assert result.status == "FAIL"
        assert any("Missing standard #main or !side" in fp for fp in result.failpoints)


def test_diagnostic_decks_catches_corrupted_passcodes():
    """Verify that a .ydk file containing non-numeric passcodes triggers a failpoint."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        broken_deck = os.path.join(tmp_dir, "corrupted.ydk")
        with open(broken_deck, "w", encoding="utf-8") as f:
            f.write("#main\n50000001\nNOT_A_NUMBER\n!side\n")

        diag = PlatformDiagnostics(decks_dir=tmp_dir)
        result = diag.audit_decks()

        assert result.status == "FAIL"
        assert any("Contains non-numeric passcode 'NOT_A_NUMBER'" in fp for fp in result.failpoints)


# =============================================================================
# 4. Lua Script Diagnostics Tests
# =============================================================================

def test_diagnostic_lua_catches_missing_getid():
    """Verify that a Lua script without 'local s, id = GetID()' is flagged."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    with tempfile.TemporaryDirectory() as script_dir:
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE custom_cards (id INTEGER PRIMARY KEY, name TEXT, card_subtype TEXT);")
            conn.execute("INSERT INTO custom_cards VALUES (50000001, 'No GetID Card', 'Effect');")
            conn.commit()
            conn.close()

            bad_script = os.path.join(script_dir, "c50000001.lua")
            with open(bad_script, "w", encoding="utf-8") as f:
                f.write("function s.initial_effect(c)\nend\n")

            diag = PlatformDiagnostics(db_path=db_path, scripts_dir=script_dir)
            result = diag.audit_lua_scripts()

            assert result.status == "FAIL"
            assert any("Missing mandatory ocgcore header 'local s, id = GetID()'" in fp for fp in result.failpoints)
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
