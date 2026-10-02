#!/usr/bin/env python3
"""
Unit tests for development/tools/lua_generator.py procedure builders, effect parsers,
and syntax verification with luac.
"""

import pytest
import sys
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from lua_generator import (
    ProcedureGenerator, EffectAnalyzer, LuaScriptBuilder, validate_lua_syntax
)


def test_procedure_generator_xyz():
    """Test generating Xyz summoning procedure."""
    procs = ProcedureGenerator.generate("Xyz", "2 Level 8 LIGHT monsters", 8)
    assert len(procs) == 2
    assert "Xyz.AddProcedure" in procs[0]
    assert "ATTRIBUTE_LIGHT" in procs[0]
    assert "c:EnableReviveLimit()" in procs[1]


def test_procedure_generator_link():
    """Test generating Link summoning procedure."""
    procs = ProcedureGenerator.generate("Link", "3+ Effect Monsters", 4)
    assert len(procs) == 2
    assert "Link.AddProcedure" in procs[0]
    assert "c:EnableReviveLimit()" in procs[1]


def test_procedure_generator_pendulum():
    """Test generating Pendulum procedure."""
    procs = ProcedureGenerator.generate("Pendulum", "", 4)
    assert len(procs) == 1
    assert "Pendulum.AddProcedure(c)" in procs[0]


def test_effect_analyzer_search_and_detach():
    """Test parsing search effect and detach cost."""
    effect_text = 'You can detach 1 material from this card; add 1 "Starforged" Spell from your Deck to your hand.'
    analyzer = EffectAnalyzer(50000001, "Monster", "Xyz", effect_text)
    analyzer.build_all()

    assert len(analyzer.effects) >= 1
    assert len(analyzer.helpers) >= 2

    # Check for detach cost and tohand search category
    effects_str = "\n".join(analyzer.effects)
    assert "CATEGORY_TOHAND" in effects_str
    assert "SetCost(s.cost_detach1)" in effects_str

    helpers_str = "\n".join(analyzer.helpers)
    assert "RemoveOverlayCard" in helpers_str
    assert "Duel.SendtoHand" in helpers_str


def test_full_lua_script_syntax():
    """Test rendering a complete Lua script and validating syntax with luac."""
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
        '2 Level 8 monsters\nOnce per turn (Quick Effect): You can detach 1 material from this card, then target 1 face-up card on the field; banish it. When this card is Normal or Special Summoned: You can add 1 Spell from your Deck to your hand.',
        None,
        "https://www.duelingbook.com/card?id=50000099"
    )

    builder = LuaScriptBuilder(card_tuple)
    lua_code = builder.render()

    assert "GetID()" in lua_code
    assert "s.initial_effect(c)" in lua_code
    assert "Xyz.AddProcedure" in lua_code

    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(lua_code)
        temp_path = f.name

    try:
        is_valid, err = validate_lua_syntax(temp_path)
        assert is_valid, f"Lua syntax error: {err}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
