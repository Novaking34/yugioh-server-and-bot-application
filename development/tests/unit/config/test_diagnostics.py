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
    assert ("Authoritative database not found" in result.failpoints[0] or "Story database not found" in result.failpoints[0])
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


# =============================================================================
# 5. Post-Mortem Crash Snapshot & Tracer Span Tests
# =============================================================================

def test_diagnostic_snapshot_generation_and_pruning():
    """Verify that take_debug_snapshot creates snapshot in DEBUG_SNAPSHOTS_DIR and prunes stale files."""
    import json
    import time
    from config.paths import DEBUG_SNAPSHOTS_DIR
    from config.debugger import take_debug_snapshot, prune_debug_snapshots

    # 1. Take snapshot
    incident_id = "test_incident_xyz999"
    path = take_debug_snapshot(incident_id, context={"test_key": "test_val"})
    assert os.path.exists(path)
    assert path.startswith(DEBUG_SNAPSHOTS_DIR)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["incident_id"] == incident_id
    assert data["context"]["test_key"] == "test_val"
    assert "diagnostics" in data

    # 2. Test pruning: set fake mtime to 10 days ago and prune with 7-day retention
    old_time = time.time() - (10 * 86400)
    os.utime(path, (old_time, old_time))
    pruned = prune_debug_snapshots(retention_days=7)
    assert pruned >= 1
    assert not os.path.exists(path)


def test_diagnostic_tracer_span_lifecycle():
    """Verify that trace_span establishes correlation ID, measures latency, and records metadata."""
    import time
    from config.debugger import trace_span, get_current_trace_id

    active_tid = get_current_trace_id()
    assert active_tid.startswith("trc-")

    with trace_span("Unit Test Span", service="TEST") as span:
        time.sleep(0.005)
        span["custom_field"] = "custom_value"

    assert span["span_name"] == "Unit Test Span"
    assert span["service"] == "TEST"
    assert span["duration_ms"] >= 4.0
    assert span["custom_field"] == "custom_value"


# =============================================================================
# 6. Automated Test Suite Diagnostic Auditing & Dual Data Mode Tests
# =============================================================================

def test_diagnostic_audit_test_suite_live_and_sample_modes():
    """Verify that PlatformDiagnostics can programmatically audit test suites across live and sample data."""
    diag = PlatformDiagnostics()

    # 1. Audit functional tier with sample data mode
    res_sample = diag.audit_test_suite(tier="functional", data_mode="sample")
    assert isinstance(res_sample, DiagnosticResult)
    assert res_sample.status == "PASS"
    assert res_sample.checked_count >= 3
    assert len(res_sample.failpoints) == 0

    # 2. Audit functional tier with live data mode
    res_live = diag.audit_test_suite(tier="functional", data_mode="live")
    assert isinstance(res_live, DiagnosticResult)
    assert res_live.status == "PASS"
    assert res_live.checked_count >= 3
    assert len(res_live.failpoints) == 0


def test_diagnostic_run_all_with_dual_data_modes():
    """Verify that run_all with include_tests=True and data_mode='both' audits both live and sample suites."""
    diag = PlatformDiagnostics()
    results = diag.run_all(include_tests=True, tier="functional", data_mode="both")

    names = [r.name for r in results]
    assert any("Live Data" in n for n in names)
    assert any("Sample Data" in n for n in names)
    assert all(r.status == "PASS" for r in results)


def test_diagnostic_audit_test_suite_failpoint_extraction(monkeypatch):
    """Verify that failing test runs properly capture failpoints and remediation suggestions."""
    from unittest.mock import MagicMock
    import subprocess

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = (
        "=== short test summary info ===\n"
        "FAILED development/tests/unit/test_mock.py::test_mock_fail - AssertionError: Mismatch\n"
        "================ 1 failed in 0.05s ================\n"
    )
    mock_proc.stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_proc)

    diag = PlatformDiagnostics()
    res = diag.audit_test_suite(tier="unit", data_mode="sample")
    assert res.status == "FAIL"
    assert len(res.failpoints) == 1
    assert "FAILED development/tests/unit/test_mock.py::test_mock_fail" in res.failpoints[0]
    assert len(res.suggestions) >= 1


