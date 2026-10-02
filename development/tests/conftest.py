#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Pytest Configuration, Fixtures & Diagnostic Tools
=============================================================================
Provides:
1. Reusable in-memory SQLite database fixtures (`mock_db`, `populated_db`).
2. Diagnostic assertion helpers with rich, actionable failpoint reporting.
3. Sample card dictionaries representing all Yu-Gi-Oh! card classifications.
4. Test failure inspection hooks to dump contextual debugging info.
=============================================================================
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from typing import Dict, Any, Generator

# Ensure development/tools and production paths are available
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
DEV_DIR = os.path.dirname(TESTS_DIR)
ROOT_DIR = os.path.dirname(DEV_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if os.path.join(DEV_DIR, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(DEV_DIR, "tools"))
if os.path.join(ROOT_DIR, "production", "main", "web") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "production", "main", "web"))

from constants import (
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_NORMAL, TYPE_EFFECT,
    TYPE_FUSION, TYPE_RITUAL, TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, RACE_WARRIOR, RACE_DRAGON,
    LINK_BL, LINK_BR, LINK_T
)


# =============================================================================
# Diagnostic Assertion Helpers (Designed to show exact failpoints)
# =============================================================================

class DiagnosticAssert:
    """Diagnostic assertion utilities designed to pinpoint exact failure causes."""

    @staticmethod
    def assert_bitmask_contains(actual_mask: int, expected_flag: int, flag_name: str) -> None:
        """Asserts that a bitmask contains a specific flag, displaying binary/hex failpoints.
        
        Args:
            actual_mask: The composite bitmask integer.
            expected_flag: The individual bit flag expected to be present.
            flag_name: Human-readable name of the flag for clear diagnostic reporting.
        """
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


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture
def diag():
    """Provides access to the DiagnosticAssert helper in tests."""
    return DiagnosticAssert


@pytest.fixture
def mock_db() -> Generator[sqlite3.Connection, None, None]:
    """Provides an isolated, in-memory SQLite database initialized with schema.sql."""
    schema_path = os.path.join(DEV_DIR, "database", "schema.sql")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
        
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
