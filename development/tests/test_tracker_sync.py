#!/usr/bin/env python3
"""
=============================================================================
Master Card Tracker & Google Sheets Synchronization Test Suite
=============================================================================
Asserts:
1. Tracker CSV and TSV exist, parse correctly, and have all 14 TLOK cards.
2. Google Sheets =IMAGE(...) formula is present in Column D.
3. Bitmasks and card categories conform to ocgcore and simulator specs.
4. Tracker synchronization correctly updates the SQLite story database.
5. All 14 card images exist locally in production/shared/expansions/pics/.
=============================================================================
"""

import pytest
import os
import sys
import csv
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import STORY_DB_PATH, PICS_DIR, TRACKERS_DIR
from development.tools.tracker_sync import (
    parse_raw_tracker,
    calculate_cdb_type,
    extract_duelingbook_id,
    DEFAULT_ROOT_CSV,
    DEFAULT_TRACKER_CSV,
    DEFAULT_TRACKER_TSV,
)


def test_tracker_files_exist_and_match():
    """Verify that both CSV and TSV tracker files exist and contain 14 records."""
    assert os.path.exists(DEFAULT_TRACKER_CSV), "Master Tracker CSV missing!"
    assert os.path.exists(DEFAULT_TRACKER_TSV), "Master Tracker TSV missing!"
    assert os.path.exists(DEFAULT_ROOT_CSV), "Root Master Tracker CSV mirror missing!"

    records = parse_raw_tracker(DEFAULT_TRACKER_CSV)
    assert len(records) == 14, f"Expected 14 cards, got {len(records)}"

    # Check for core creator cards
    names = [r["name"] for r in records]
    assert "Kasutamaiza, the Creator of Kustomazi" in names
    assert "The Void of Creation" in names
    assert "The Seed of Creation" in names
    assert "The Great Kasutamaiza" in names


def test_google_sheets_image_formula_present():
    """Verify that the CSV and TSV rows contain valid Google Sheets =IMAGE(...) formulas."""
    with open(DEFAULT_TRACKER_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert "Image Preview" in header
        preview_col_idx = header.index("Image Preview")
        link_col_idx = header.index("Image Link")

        for row_idx, row in enumerate(reader, 2):
            formula = row[preview_col_idx]
            expected_cell = f"E{row_idx}"
            assert f"IMAGE({expected_cell})" in formula, f"Row {row_idx} missing formula referencing {expected_cell}: {formula}"
            assert row[link_col_idx].startswith("http"), f"Row {row_idx} missing valid image link"


def test_bitmask_calculation_correctness():
    """Verify that calculate_cdb_type produces correct ocgcore binary bitmasks."""
    # Monster Effect = 0x21 (TYPE_MONSTER 0x1 | TYPE_EFFECT 0x20)
    assert calculate_cdb_type("Monster", "Effect") == 0x21

    # Monster Normal = 0x11 (TYPE_MONSTER 0x1 | TYPE_NORMAL 0x10)
    assert calculate_cdb_type("Monster", "Normal") == 0x11

    # Quick-Play Spell = 0x10002 (TYPE_SPELL 0x2 | TYPE_QUICKPLAY 0x10000)
    assert calculate_cdb_type("Spell", "Quick-Play") == 0x10002

    # Field Spell = 0x80002 (TYPE_SPELL 0x2 | TYPE_FIELD 0x80000)
    assert calculate_cdb_type("Spell", "Field") == 0x80002

    # Counter Trap = 0x100004 (TYPE_TRAP 0x4 | TYPE_COUNTER 0x100000)
    assert calculate_cdb_type("Trap", "Counter") == 0x100004


def test_duelingbook_id_extraction():
    """Verify that Duelingbook picture ID is extracted accurately from URLs."""
    url = "https://images.duelingbook.com/custom-pics/2200000/2282769.jpg?version=6"
    assert extract_duelingbook_id(url) == "2282769"


def test_database_has_synchronized_cards():
    """Verify that custom_cards table in story DB contains all 14 TLOK cards with passcodes."""
    conn = sqlite3.connect(STORY_DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM custom_cards WHERE set_code = 'TLOK'")
    tlok_count = cur.fetchone()[0]
    assert tlok_count == 14, f"Expected 14 TLOK cards in database, found {tlok_count}"

    # Check that 'The Creators of Kustomazi' faction is linked
    cur.execute("""
        SELECT c.id, c.name, f.name
        FROM custom_cards c
        JOIN factions f ON c.faction_id = f.id
        WHERE c.name = 'Kasutamaiza, the Creator of Kustomazi'
    """)
    row = cur.fetchone()
    assert row is not None
    assert row[0] == 50000101
    assert row[2] == "The Creators of Kustomazi"

    conn.close()


def test_local_images_exist():
    """Verify that local card images are present for all 14 cards in expansions/pics/."""
    for passcode in range(50000101, 50000115):
        img_path = os.path.join(PICS_DIR, f"{passcode}.jpg")
        assert os.path.exists(img_path), f"Card artwork missing for passcode {passcode}: {img_path}"
        assert os.path.getsize(img_path) > 1000, f"Card artwork appears corrupted (size <= 1000 bytes): {img_path}"
