#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.conftest
Architecture: Hybrid Systems Engineering (Testing & Diagnostic Infrastructure)
Domain: Test Harness, Fixtures, Diagnostic Assertions & Dual Data Mode (Live/Sample)
Description:
    Master Pytest configuration and shared fixtures for the Yu-Gi-Oh! platform test suite.
    Provides:
    1. Dual Data Mode Engine: Supports execution against Live Data (STORY_DB_PATH)
       and Isolated Sample Data (temporary on-disk seeded SQLite database or in-memory mock).
    2. CLI Flags: Adds `--data-mode` (`live`, `sample`, `both`) and environment variable
       `YGO_TEST_DATA_MODE` control.
    3. Diagnostic Assertion Helpers (`DiagnosticAssert`): Pinpoints exact bitmask,
       scale, and passcode boundary failpoints.
    4. Representative Sample Card Fixtures across all summoning mechanics (Xyz, Link,
       Pendulum, Spells, Traps).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import sqlite3
import tempfile
import pytest
from typing import Dict, Any, Generator

# Path bootstrap to ensure internal packages resolve cleanly
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
DEV_DIR = os.path.dirname(TESTS_DIR)
ROOT_DIR = os.path.dirname(DEV_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if os.path.join(DEV_DIR, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(DEV_DIR, "tools"))
if os.path.join(ROOT_DIR, "production", "main", "web") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "production", "main", "web"))
if os.path.join(ROOT_DIR, "production", "main", "discord_bot") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "production", "main", "discord_bot"))

from config.paths import STORY_DB_PATH, CONTENT_DB_PATH, TELEMETRY_DB_PATH, SCHEMA_PATH

try:
    import aiosqlite
    if not getattr(aiosqlite, "_two_tier_attached", False):
        _original_aiosqlite_connect = aiosqlite.connect

        class _TwoTierContextManager:
            def __init__(self, db_path, *args, **kwargs):
                self._cm = _original_aiosqlite_connect(db_path, *args, **kwargs)
                self.db_path = str(db_path)

            async def __aenter__(self):
                conn = await self._cm.__aenter__()
                if (self.db_path == CONTENT_DB_PATH or self.db_path.endswith("content.db")) and os.path.exists(TELEMETRY_DB_PATH):
                    try:
                        await conn.execute(f"ATTACH DATABASE '{TELEMETRY_DB_PATH}' AS telemetry")
                    except Exception:
                        pass
                elif (self.db_path == TELEMETRY_DB_PATH or self.db_path.endswith("telemetry.db")) and os.path.exists(CONTENT_DB_PATH):
                    try:
                        await conn.execute(f"ATTACH DATABASE '{CONTENT_DB_PATH}' AS content")
                    except Exception:
                        pass
                return conn

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return await self._cm.__aexit__(exc_type, exc_val, exc_tb)

        aiosqlite.connect = _TwoTierContextManager
        aiosqlite._two_tier_attached = True
except ImportError:
    pass
from constants import (
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_NORMAL, TYPE_EFFECT,
    TYPE_FUSION, TYPE_RITUAL, TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, RACE_WARRIOR, RACE_DRAGON,
    LINK_BL, LINK_BR, LINK_T
)


# =============================================================================
# BLOCK 3: BODY BLOCK (Assertion Helpers, Seeding Logic & Fixtures)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Diagnostic Assertion Helpers
# -----------------------------------------------------------------------------
class DiagnosticAssert:
    """Diagnostic assertion utilities designed to pinpoint exact failure causes."""

    @staticmethod
    def assert_bitmask_contains(actual_mask: int, expected_flag: int, flag_name: str) -> None:
        """Asserts that a bitmask contains a specific flag, displaying binary/hex failpoints."""
        has_flag = (actual_mask & expected_flag) == expected_flag
        if not has_flag:
            fail_report = (
                f"\n[FAILPOINT] Bitmask missing flag '{flag_name}'!\n"
                f"  Expected Flag : {hex(expected_flag)} ({bin(expected_flag)})\n"
                f"  Actual Mask   : {hex(actual_mask)} ({bin(actual_mask)})\n"
                f"  Bitwise AND   : {hex(actual_mask & expected_flag)}\n"
            )
            assert False, fail_report

    @staticmethod
    def assert_bitmask_orthogonal(mask_a: int, mask_b: int, name_a: str, name_b: str) -> None:
        """Asserts that two bitmasks share zero overlapping bits."""
        overlap = mask_a & mask_b
        if overlap != 0:
            fail_report = (
                f"\n[FAILPOINT] Bitmask collision detected between '{name_a}' and '{name_b}'!\n"
                f"  Mask A        : {hex(mask_a)} ({bin(mask_a)})\n"
                f"  Mask B        : {hex(mask_b)} ({bin(mask_b)})\n"
                f"  Collision Bits: {hex(overlap)} ({bin(overlap)})\n"
            )
            assert False, fail_report

    @staticmethod
    def assert_passcode_in_range(passcode: int) -> None:
        """Asserts that a custom card passcode is in the reserved 50,000,000 - 59,999,999 range."""
        if not (50000000 <= passcode <= 59999999):
            fail_report = (
                f"\n[FAILPOINT] Custom passcode {passcode} outside safe reserved range!\n"
                f"  Allowed Range : 50,000,000 - 59,999,999 (Community custom reserve)\n"
                f"  Received ID   : {passcode}\n"
                f"  Note          : IDs outside this range risk collisions with official Konami cards."
            )
            assert False, fail_report

    @staticmethod
    def assert_pendulum_scale_valid(scale: int) -> None:
        """Asserts that a Pendulum scale is within legal game rules (0 - 13)."""
        if not (0 <= scale <= 13):
            fail_report = (
                f"\n[FAILPOINT] Illegal Pendulum Scale value {scale}!\n"
                f"  Allowed Range : 0 to 13\n"
                f"  Received      : {scale}"
            )
            assert False, fail_report


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Sample Database Seeder Helper
# -----------------------------------------------------------------------------
def seed_sample_database(conn: sqlite3.Connection) -> None:
    """Seeds an SQLite connection with deterministic sample data for hermetic testing."""
    cur = conn.cursor()

    # 1. Lore Arc
    cur.execute("""
        INSERT OR IGNORE INTO lore_arcs (id, title, synopsis, era_or_season)
        VALUES (1, 'The Land of Kustomazi Genesis', 'First canonical lore arc.', 'Season 1');
    """)

    # 2. Faction
    cur.execute("""
        INSERT OR IGNORE INTO factions (id, name, lore_description, playstyle_overview, arc_id)
        VALUES (1, 'The Genesis Void', 'Primordial entities from the dawn of creation.', 'Control & Banishment', 1);
    """)

    # 3. Characters
    cur.execute("""
        INSERT OR IGNORE INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
        VALUES (1, 'The Great Kasutamaiza', 'Void Archon', 'Arch-creator of the void.', 1, 1, 'https://example.com/kasutamaiza.png');
    """)
    cur.execute("""
        INSERT OR IGNORE INTO characters (id, name, alias, bio, faction_id, arc_id, avatar_url)
        VALUES (2, 'LeSpookie Singles', 'Phantom Blade', 'Spooky phantom wanderer.', 1, 1, 'https://example.com/lespookie.png');
    """)

    # 4. Custom Cards (First 10 authoritative canonical cards)
    sample_custom_cards = [
        (
            50000101, "Kasutamaiza, the Creator of Kustomazi", "Monster", "Effect",
            "DIVINE", "Divine-Beast", 12, None, 4000, 4000, None,
            "Cannot be Normal Summoned/Set. Must be Special Summoned (from your hand) by banishing 3 DIVINE monsters from your field and/or GY.",
            None, 1, "TLOK-001", "TLOK", "Secret Rare", "The Customizer (Creator Deity)"
        ),
        (
            50000102, "The Void of Creation", "Monster", "Normal",
            "DIVINE", "Divine-Beast", 1, None, 0, 0, None,
            "It is quiet and restless. Containing all of the potential of one universe, it must be shaped and forged. Whoever masters the void masters the universe.",
            None, 1, "TLOK-002", "TLOK", "Common", "The Quiet Void (Primordial Origin)"
        ),
        (
            50000103, "The Seed of Creation", "Spell", "Quick-Play",
            None, None, None, None, None, None, None,
            "Add 1 \"Kasutamaiza, the Creator of Kustomazi\" from your Deck to your hand, or if you cannot, draw 1 card, then place 1 card from your hand on the bottom of the Deck.",
            None, 1, "TLOK-003", "TLOK", "Super Rare", "The Seed of the World (Genesis Catalyst)"
        ),
        (
            50000104, "Servants of the Great Kasutamaiza", "Monster", "Effect",
            "DIVINE", "Divine-Beast", 1, None, 100, 100, None,
            "If this card is Normal Summoned: You can Special Summon up to 2 \"Servants of the Great Kasutamaiza\" from your hand and/or Deck.",
            None, 1, "TLOK-004", "TLOK", "Rare", "Devout Heralds of Genesis"
        ),
        (
            50000105, "Formless the True Void of Creation", "Monster", "Effect",
            "DIVINE", "Divine-Beast", 1, None, None, None, None,
            "Cannot be Normal Summoned/Set. Must first be Special Summoned (from your hand) by banishing 1 \"The Void of Creation\", 1 \"Servants of the Great Kasutamaiza\", and 1 \"The Seed of Creation\" from your hand and/or GY.",
            None, 1, "TLOK-005", "TLOK", "Rare", "The Formless Void (Primordial Origin)"
        ),
        (
            50000106, "Mohousha the Accursed of the Great Kasutamaiza", "Monster", "Fusion / Effect",
            "DARK", "Divine-Beast", 1, None, 0, 0, None,
            "\"Formless the True Void of Creation\" + \"The Void of Creation\" + \"Servants of the Great Kasutamaiza\"",
            None, 1, "TLOK-006", "TLOK", "Ultra Rare", "The Accursed Reflection (Post-Genesis Antagonist)"
        ),
        (
            50000107, "The Great Kasutamaiza", "Monster", "Fusion / Effect",
            "DIVINE", "Divine-Beast", 12, None, None, None, None,
            "\"Kasutamaiza, the Creator of Kustomazi\" + 2 monsters with different names Must first be Fusion Summoned.",
            None, 1, "TLOK-007", "TLOK", "Secret Rare", "The Ascended Customizer (Apex Fusion)"
        ),
        (
            50000108, "The Call of the Great Kasutamaiza", "Spell", "Normal",
            None, None, None, None, None, None, None,
            "Add 1 \"Kasutamaiza\" card from your Deck to your hand.",
            None, 1, "TLOK-008", "TLOK", "Super Rare", "The Calling of the First Orders"
        ),
        (
            50000109, "Divine Justice of the Great Kasutamaiza", "Trap", "Counter",
            None, None, None, None, None, None, None,
            "When a monster(s) would be Summoned, OR a Spell/Trap Card or effect is activated: Pay 2000 LP and banish 1 card from your hand or GY; negate the Summon or activation, and if you do, destroy that card.",
            None, 1, "TLOK-009", "TLOK", "Ultra Rare", "The Celestial Law of Kustomazi"
        ),
        (
            50000110, "Planet Kustomazi", "Spell", "Field",
            None, None, None, None, None, None, None,
            "When this card is activated: You can shuffle 1 card from your hand into the Deck, then draw 1 card.",
            None, 1, "TLOK-010", "TLOK", "Super Rare", "The World Born from the Seed (Chapter 1 Climax)"
        ),
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO custom_cards (
            id, name, card_type, card_subtype, attribute, monster_type,
            level_or_rank_or_link, scale, atk, def, link_arrows, effect_text,
            pendulum_effect, faction_id, set_number, set_code, rarity, story_significance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_custom_cards)

    # Full-Text Search FTS5 synchronization
    cur.execute("INSERT INTO cards_fts(cards_fts) VALUES('rebuild');")

    # 5. Decks & Deck Cards
    cur.execute("""
        INSERT OR IGNORE INTO decks (id, character_id, name, description)
        VALUES (1, 1, 'Kasutamaiza - Creation Control', 'Official pre-built control deck.');
    """)
    cur.execute("""
        INSERT OR IGNORE INTO decks (id, character_id, name, description)
        VALUES (2, 2, 'LeSpookie Singles', 'Official aggro singles deck.');
    """)

    # Populate Deck 1 (Main + Extra)
    for cid in [50000101, 50000102, 50000103, 50000104, 50000105, 50000108, 50000109, 50000110]:
        cur.execute("INSERT OR IGNORE INTO deck_cards (deck_id, card_id, quantity, section) VALUES (1, ?, 3, 'MAIN');", (cid,))
    for cid in [50000106, 50000107]:
        cur.execute("INSERT OR IGNORE INTO deck_cards (deck_id, card_id, quantity, section) VALUES (1, ?, 3, 'EXTRA');", (cid,))

    # Populate Deck 2 (Main + Extra)
    for cid in [50000101, 50000102, 50000103, 50000104, 50000105, 50000108, 50000109, 50000110]:
        cur.execute("INSERT OR IGNORE INTO deck_cards (deck_id, card_id, quantity, section) VALUES (2, ?, 3, 'MAIN');", (cid,))
    for cid in [50000106, 50000107]:
        cur.execute("INSERT OR IGNORE INTO deck_cards (deck_id, card_id, quantity, section) VALUES (2, ?, 3, 'EXTRA');", (cid,))

    # Pre-populate saved deck profiles in player_saved_decks
    sample_ydk = "#main\n50000101\n50000102\n#extra\n50000106\n!side\n"
    cur.execute("""
        INSERT OR IGNORE INTO player_saved_decks (user_id, deck_name, ydk_content, times_used, wins, losses)
        VALUES ('991001', 'Alpha Deck', ?, 0, 0, 0);
    """, (sample_ydk,))
    cur.execute("""
        INSERT OR IGNORE INTO player_saved_decks (user_id, deck_name, ydk_content, times_used, wins, losses)
        VALUES ('991002', 'Beta Deck', ?, 0, 0, 0);
    """, (sample_ydk,))

    # 6. Story Chapters & Stages
    cur.execute("""
        INSERT OR IGNORE INTO story_chapters (id, chapter_number, title, arc_id, synopsis)
        VALUES (1, 1, 'Awakening in the Void', 1, 'The emergence of creation.');
    """)
    cur.execute("""
        INSERT OR IGNORE INTO story_stages (
            id, chapter_id, stage_number, title, intro_dialogue, outro_dialogue,
            opponent_name, opponent_title, opponent_character_id, opponent_deck_id,
            encounter_type, boss_hp, reward_title, reward_card_id
        ) VALUES (
            1, 1, 1, 'The Quiet Void', 'Prepare yourself.', 'Well fought.',
            'The Great Kasutamaiza', 'Void Archon', 1, 1,
            'AI', 8000, 'Void Wanderer', 50000102
        );
    """)
    cur.execute("""
        INSERT OR IGNORE INTO story_stages (
            id, chapter_id, stage_number, title, intro_dialogue, outro_dialogue,
            opponent_name, opponent_title, opponent_character_id, opponent_deck_id,
            encounter_type, boss_hp, reward_title, reward_card_id
        ) VALUES (
            2, 1, 2, 'Echoes of Dust', 'The dust settles.', 'Creation advances.',
            'The Great Kasutamaiza', 'Void Archon', 1, 1,
            'AI', 8000, 'Dust Walker', 50000103
        );
    """)

    conn.commit()


# -----------------------------------------------------------------------------
# Sub-Block 3.3: CLI Option Registration
# -----------------------------------------------------------------------------
def pytest_addoption(parser):
    """Register custom CLI options for test execution."""
    parser.addoption(
        "--data-mode",
        action="store",
        default=os.environ.get("YGO_TEST_DATA_MODE", "live"),
        choices=["live", "sample", "both"],
        help="Data source mode: 'live' (STORY_DB_PATH), 'sample' (isolated seeded db), or 'both'."
    )


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Pytest Fixtures (Live vs. Sample Data)
# -----------------------------------------------------------------------------
@pytest.fixture
def diag():
    """Provides access to the DiagnosticAssert helper in tests."""
    return DiagnosticAssert


@pytest.fixture
def data_mode(request) -> str:
    """Returns the active data mode ('live' or 'sample')."""
    return request.config.getoption("--data-mode")


@pytest.fixture
def live_db_path() -> str:
    """Returns the canonical live authoritative SQLite database path."""
    return STORY_DB_PATH


@pytest.fixture
def sample_db_path(tmp_path) -> Generator[str, None, None]:
    """Provides an isolated, on-disk SQLite database path seeded with canonical sample data."""
    temp_db = str(tmp_path / "sample_story.db")
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    seed_sample_database(conn)
    conn.close()
    yield temp_db


@pytest.fixture
def test_db_path(request, live_db_path, sample_db_path) -> str:
    """Dynamically resolves to live_db_path or sample_db_path based on active data_mode."""
    mode = request.config.getoption("--data-mode")
    if mode == "sample" or not os.path.exists(live_db_path):
        return sample_db_path
    return live_db_path


@pytest.fixture
def mock_db() -> Generator[sqlite3.Connection, None, None]:
    """Provides an isolated, in-memory SQLite database initialized with schema.sql (unseeded)."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    yield conn
    conn.close()


@pytest.fixture
def populated_mock_db() -> Generator[sqlite3.Connection, None, None]:
    """Provides an isolated, in-memory SQLite database initialized with schema.sql and seeded sample data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    seed_sample_database(conn)
    yield conn
    conn.close()


@pytest.fixture
def sample_cards() -> Dict[str, Dict[str, Any]]:
    """Provides representative test card dictionaries across major summoning mechanics."""
    return {
        "xyz": {
            "id": 50000002,
            "name": "Starforged Sovereign - Sol Invictus",
            "card_type": "Monster",
            "card_subtype": "Effect Xyz",
            "attribute": "LIGHT",
            "monster_type": "Warrior",
            "level_or_rank_or_link": 8,
            "scale": None,
            "atk": 3000,
            "def": 2500,
            "link_arrows": None,
            "effect_text": (
                "2 Level 8 LIGHT monsters\n"
                "Once per turn (Quick Effect): You can detach 1 material from this card, "
                "then target 1 face-up card on the field; banish it until the End Phase. "
                "When this card destroys an opponent's monster by battle: You can attach that monster to this card as material."
            ),
            "pendulum_effect": None,
        },
        "link": {
            "id": 50000004,
            "name": "Void Sovereign - Abyssal Ouroboros",
            "card_type": "Monster",
            "card_subtype": "Effect Link",
            "attribute": "DARK",
            "monster_type": "Dragon",
            "level_or_rank_or_link": 3,
            "scale": None,
            "atk": 2400,
            "def": 0,
            "link_arrows": "BL,BR,T",
            "effect_text": (
                "2+ DARK monsters\n"
                "If this card is Link Summoned: You can banish 1 card from your opponent's GY. "
                "While this card points to a monster, neither player can target this card with card effects."
            ),
            "pendulum_effect": None,
        },
        "pendulum": {
            "id": 50000005,
            "name": "Harmonic Starlight Magician",
            "card_type": "Monster",
            "card_subtype": "Effect Pendulum",
            "attribute": "LIGHT",
            "monster_type": "Spellcaster",
            "level_or_rank_or_link": 4,
            "scale": 7,
            "atk": 1500,
            "def": 1000,
            "link_arrows": None,
            "effect_text": "If this card is Normal Summoned: Add 1 Pendulum monster from your Deck to your hand.",
            "pendulum_effect": "Once per turn: You can target 1 face-up monster on the field; increase its ATK by 500.",
        },
        "spell_quickplay": {
            "id": 50000003,
            "name": "Starforged Dawn",
            "card_type": "Spell",
            "card_subtype": "Quick-Play",
            "attribute": None,
            "monster_type": None,
            "level_or_rank_or_link": None,
            "scale": None,
            "atk": None,
            "def": None,
            "link_arrows": None,
            "effect_text": "Special Summon 1 \"Starforged\" monster from your GY, but destroy it during the End Phase.",
            "pendulum_effect": None,
        },
        "trap_counter": {
            "id": 50000006,
            "name": "Astral Reversal",
            "card_type": "Trap",
            "card_subtype": "Counter",
            "attribute": None,
            "monster_type": None,
            "level_or_rank_or_link": None,
            "scale": None,
            "atk": None,
            "def": None,
            "link_arrows": None,
            "effect_text": "When a Spell/Trap Card, or monster effect, is activated: Detach 1 material from an Xyz Monster you control; negate the activation, and if you do, destroy it.",
            "pendulum_effect": None,
        },
    }


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "DiagnosticAssert",
    "seed_sample_database",
    "pytest_addoption",
    "diag",
    "data_mode",
    "live_db_path",
    "sample_db_path",
    "test_db_path",
    "mock_db",
    "sample_cards"
]
