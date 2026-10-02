#!/usr/bin/env python3
"""
=============================================================================
ocgcore Lua Script Generator Diagnostic Test Suite
=============================================================================
Asserts:
1. Summoning procedure generation across Xyz, Link, Pendulum, and Synchro mechanics.
2. Effect Analyzer classification for detach costs, search effects, and OPT limits.
3. Complete Lua script scaffolding with standard ocgcore conventions.
4. Failpoint diagnostics on malformed inputs and Lua syntax validation via luac.
=============================================================================
"""

import pytest
import tempfile
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from lua_generator import (
    ProcedureGenerator, EffectAnalyzer, LuaScriptBuilder, validate_lua_syntax
)


# =============================================================================
# 1. Summoning Procedure Generation Tests
# =============================================================================

def test_procedure_generator_xyz():
    """Verify Xyz procedure generation with materials, rank, and revive limit."""
    procs = ProcedureGenerator.generate("Xyz", "2 Level 8 LIGHT monsters", 8)
    assert len(procs) == 2, f"Expected 2 lines for Xyz procedure, got {len(procs)}"
    assert "Xyz.AddProcedure" in procs[0]
    assert "ATTRIBUTE_LIGHT" in procs[0]
    assert "c:EnableReviveLimit()" in procs[1]


def test_procedure_generator_link():
    """Verify Link procedure generation with material constraints and revive limit."""
    procs = ProcedureGenerator.generate("Link", "3+ Effect Monsters", 4)
    assert len(procs) == 2
    assert "Link.AddProcedure" in procs[0]
    assert "c:EnableReviveLimit()" in procs[1]


def test_procedure_generator_pendulum():
    """Verify Pendulum procedure registration."""
    procs = ProcedureGenerator.generate("Pendulum", "", 4)
    assert len(procs) == 1
    assert "Pendulum.AddProcedure(c)" in procs[0]


def test_procedure_generator_synchro():
    """Verify Synchro procedure generation with Tuner + Non-Tuner setup."""
    procs = ProcedureGenerator.generate("Synchro", "1 Tuner + 1+ non-Tuner monsters", 8)
    assert len(procs) == 2
    assert "Synchro.AddProcedure" in procs[0]
    assert "c:EnableReviveLimit()" in procs[1]


def test_procedure_generator_non_extra_deck():
    """Verify that main deck monsters without special procedures produce an empty list."""
    procs = ProcedureGenerator.generate("Effect", "Normal effect monster", 4)
    assert procs == []


# =============================================================================
# 2. Effect Analyzer & Mechanical Pattern Detection Tests
# =============================================================================

def test_effect_analyzer_search_and_detach():
    """Verify detection of material detach costs and to-hand search operations."""
    effect_text = 'You can detach 1 material from this card; add 1 "Starforged" Spell from your Deck to your hand.'
    analyzer = EffectAnalyzer(50000001, "Monster", "Xyz", effect_text)
    analyzer.build_all()

    assert len(analyzer.effects) >= 1
    assert len(analyzer.helpers) >= 2

    effects_str = "\n".join(analyzer.effects)
    assert "CATEGORY_TOHAND" in effects_str, "CATEGORY_TOHAND missing from search effect!"
    assert "SetCost(s.cost_detach1)" in effects_str, "Detach cost binding missing from effect!"

    helpers_str = "\n".join(analyzer.helpers)
    assert "RemoveOverlayCard" in helpers_str, "RemoveOverlayCard missing from detach helper!"
    assert "Duel.SendtoHand" in helpers_str, "Duel.SendtoHand missing from search helper!"


def test_effect_analyzer_once_per_turn_detection():
    """Verify that Hard Once Per Turn and Soft Once Per Turn clauses generate count limits."""
    hopt_text = (
        'You can add 1 "Starforged" monster from your Deck to your hand. '
        'You can only use this effect of "Test Card" once per turn.'
    )
    analyzer = EffectAnalyzer(50000001, "Monster", "Effect", hopt_text)
    analyzer.build_all()

    effects_str = "\n".join(analyzer.effects)
    assert "SetCountLimit(1, id)" in effects_str, "Hard Once Per Turn (1, id) was not generated!"


def test_effect_analyzer_protection_mechanics():
    """Verify generation of destruction replacement and targeting immunity."""
    protect_text = (
        'If this card would be destroyed by battle or card effect, you can detach 1 material instead. '
        'Cannot be targeted by your opponent\'s card effects.'
    )
    analyzer = EffectAnalyzer(50000002, "Monster", "Xyz", protect_text)
    analyzer.build_all()

    effects_str = "\n".join(analyzer.effects)
    assert "EFFECT_DESTROY_REPLACE" in effects_str
    assert "EFFECT_CANNOT_BE_EFFECT_TARGET" in effects_str


# =============================================================================
# 3. Full Script Assembly & Lua Syntax Validation Tests
# =============================================================================

def test_full_lua_script_syntax_and_structure():
    """Verify that LuaScriptBuilder generates syntactically sound ocgcore Lua code."""
    card_tuple = (
        50000099,
        "Solar Test Knight",
        "Monster",
        "Effect Xyz",
        "LIGHT",
        "Warrior",
        8,
        None,
        2800,
        2000,
        None,
        (
            "2 Level 8 monsters\n"
            "Once per turn (Quick Effect): You can detach 1 material from this card, "
            "then target 1 face-up card on the field; banish it. "
            "When this card is Normal or Special Summoned: You can add 1 Spell from your Deck to your hand."
        ),
        None,
        "https://www.duelingbook.com/card?id=50000099"
    )

    builder = LuaScriptBuilder(card_tuple)
    lua_code = builder.render()

    # Core ocgcore structural assertions
    assert "local s, id = GetID()" in lua_code
    assert "function s.initial_effect(c)" in lua_code
    assert "Xyz.AddProcedure" in lua_code
    assert "c:EnableReviveLimit()" in lua_code
    assert "s.cost_detach1" in lua_code

    # Validate syntax via luac if installed on the host
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(lua_code)
        temp_path = f.name

    try:
        is_valid, err = validate_lua_syntax(temp_path)
        assert is_valid, f"Generated Lua script contained syntax errors:\n{err}\n\nGenerated Code:\n{lua_code}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_lua_syntax_validator_detects_deliberate_syntax_error():
    """Diagnostic check: Ensure validate_lua_syntax actively catches invalid Lua code."""
    # Write intentionally broken Lua syntax
    invalid_lua = "function s.broken(c \n this is definitely not valid lua syntax !!!"
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(invalid_lua)
        temp_path = f.name

    try:
        is_valid, err = validate_lua_syntax(temp_path)
        # If luac is available, it MUST detect this failpoint
        which_luac = os.system("which luac >/dev/null 2>&1")
        if which_luac == 0:
            assert not is_valid, "Lua syntax validator failed to catch deliberate syntax error!"
            assert err is not None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
