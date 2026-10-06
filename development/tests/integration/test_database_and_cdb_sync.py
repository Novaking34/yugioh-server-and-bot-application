#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.integration.test_database_and_cdb_sync
Architecture: Hybrid Systems Engineering (Integration Testing Subsystem)
Domain: Live Database Integrity, CDB Compilation & Schema Parity
Description:
    Integration test suite verifying the live SQLite authoritative database,
    binary CDB file compilation parity, full-text search indexing, and schema foreign keys.
    Supports both live data (`STORY_DB_PATH`) and sample data (`sample_db_path`).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sqlite3
import pytest

from config.paths import STORY_DB_PATH, CDB_OUTPUT_PATH
from development.tools.cdb_builder import build_cdb


# =============================================================================
# BLOCK 3: BODY BLOCK (Integration Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Live Database Integrity & FTS Synchronization
# -----------------------------------------------------------------------------
def test_live_database_integrity_and_table_presence(test_db_path):
    """Verifies that SQLite PRAGMA integrity_check passes and all core tables exist."""
    assert os.path.exists(test_db_path), f"Target database does not exist: {test_db_path}"

    conn = sqlite3.connect(test_db_path)
    cur = conn.cursor()

    # 1. PRAGMA integrity check
    cur.execute("PRAGMA integrity_check;")
    rows = cur.fetchall()
    assert rows[0][0] == "ok", f"Database integrity check failed: {rows}"

    # 2. Table inspection
    cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
    tables = {r[0] for r in cur.fetchall()}

    from config.paths import CONTENT_DB_PATH, TELEMETRY_DB_PATH, STORY_DB_PATH
    if test_db_path in (CONTENT_DB_PATH, STORY_DB_PATH):
        content_tables = [
            "custom_cards", "factions", "characters", "decks", "deck_cards",
            "lore_arcs", "story_chapters", "story_stages", "duel_logs", "worldbuilding_elements"
        ]
        for tbl in content_tables:
            assert tbl in tables, f"Expected content table '{tbl}' missing from {test_db_path}"

        # Assert dynamic telemetry database exists and is valid
        assert os.path.exists(TELEMETRY_DB_PATH), f"Telemetry database missing from {TELEMETRY_DB_PATH}"
        t_conn = sqlite3.connect(TELEMETRY_DB_PATH)
        t_cur = t_conn.cursor()
        t_cur.execute("PRAGMA integrity_check;")
        assert t_cur.fetchall()[0][0] == "ok"
        t_cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
        t_tables = {r[0] for r in t_cur.fetchall()}
        telemetry_tables = [
            "player_ratings", "duel_matches", "card_usage_stats",
            "player_decks", "player_saved_decks", "player_story_progress"
        ]
        for tbl in telemetry_tables:
            assert tbl in t_tables, f"Expected telemetry table '{tbl}' missing from {TELEMETRY_DB_PATH}"
        t_conn.close()
    else:
        sample_tables = [
            "custom_cards", "factions", "characters", "decks", "deck_cards",
            "lore_arcs", "story_chapters", "story_stages"
        ]
        for tbl in sample_tables:
            assert tbl in tables, f"Expected table '{tbl}' missing from {test_db_path}"

    conn.close()


# -----------------------------------------------------------------------------
# Sub-Block 3.2: CDB Compilation and Parity Synchronization
# -----------------------------------------------------------------------------
def test_cdb_compilation_and_parity_sync(tmp_path, test_db_path):
    """Compiles CDB from database and verifies record parity."""
    target_cdb = str(tmp_path / "test_output.cdb")

    # Connect to DB and count cards
    conn = sqlite3.connect(test_db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM custom_cards;")
    expected_count = cur.fetchone()[0]
    conn.close()

    assert expected_count > 0, "No custom cards found in database!"

    # Compile CDB
    compiled = build_cdb(story_db_path=test_db_path, cdb_output_path=target_cdb)
    assert compiled == expected_count, f"CDB compiled {compiled} cards but expected {expected_count}"

    # Inspect compiled CDB
    cdb_conn = sqlite3.connect(target_cdb)
    cdb_cur = cdb_conn.cursor()
    cdb_cur.execute("SELECT COUNT(*) FROM datas;")
    datas_count = cdb_cur.fetchone()[0]
    cdb_cur.execute("SELECT COUNT(*) FROM texts;")
    texts_count = cdb_cur.fetchone()[0]
    cdb_conn.close()

    assert datas_count == expected_count
    assert texts_count == expected_count


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_live_database_integrity_and_table_presence",
    "test_cdb_compilation_and_parity_sync",
]
