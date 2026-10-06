#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.bot.services.test_card_service
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Discord Bot Services / Card Retrieval, Autocomplete & Telemetry
Description:
    Unit test suite for CardService and its underlying functional modules:
    1. Direct indexed lookups (ID, query, name, set_number).
    2. Autocomplete ranking, formatting, and character truncation ceiling.
    3. Multi-criteria filtering (card_type, subtype, archetype, attribute).
    4. Telemetry analytics and mutators (draws, plays, win rates, deck inclusions).
    5. Modular C-style architecture contracts and zero-regression bridging.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import pytest
import aiosqlite

from config.paths import STORY_DB_PATH
from services.card import (
    CardService,
    format_card_autocomplete_choice,
    build_card_descriptor_tag,
    get_card_by_id,
    get_card_by_query,
    get_cards_by_filter,
    get_all_cards_partitioned,
    search_cards,
    get_card_usage_stats,
    get_meta_overview,
    track_card_draw,
    reset_card_telemetry,
    DEFAULT_AUTOCOMPLETE_LIMIT,
)
from services.card.core import CardService as CoreCardService
from services.card import CardService as RootCardService


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Card Lookup and Basic Telemetry
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_card_service_lookup_and_telemetry(test_db_path):
    service = CardService(test_db_path)

    # 1. Lookup by Set Number
    card = await service.get_card_by_query("TLOK-001")
    assert card is not None
    assert card["id"] == 50000101
    assert "Kasutamaiza" in card["name"]

    # 2. Lookup by Name
    card_name = await service.get_card_by_query("The Void of Creation")
    assert card_name is not None
    assert card_name["set_number"] == "TLOK-002"

    # 3. Lookup by ID
    card_id = await service.get_card_by_query("50000103")
    assert card_id is not None
    assert card_id["name"] == "The Seed of Creation"

    # 4. Search Autocomplete
    suggestions = await service.search_cards("Kasutamaiza", limit=5)
    assert len(suggestions) >= 1
    assert any("Kasutamaiza" in s["name"] for s in suggestions)

    # 5. Track Card Draw & Read Stats
    await service.track_card_draw(50000101)
    stats = await service.get_card_usage_stats(50000101)
    assert stats["times_drawn"] >= 1

    # 6. Meta overview
    meta = await service.get_meta_overview(limit=5)
    assert "most_popular" in meta
    assert "most_victorious" in meta


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Discovery and Autocomplete Engine
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_card_service_discovery_and_autocomplete_engine(test_db_path):
    service = CardService(test_db_path)

    # 1. Direct O(1) indexed lookup
    card_by_id = await service.get_card_by_id(50000101)
    assert card_by_id is not None
    assert "Kasutamaiza" in card_by_id["name"]

    # Non-existent ID returns None
    assert await service.get_card_by_id(99999999) is None

    # 2. Composite label parsing in get_card_by_query
    comp1 = await service.get_card_by_query("TLOK-001 | Kasutamaiza")
    assert comp1 is not None
    assert comp1["id"] == 50000101

    comp2 = await service.get_card_by_query("[50000102] The Void of Creation")
    assert comp2 is not None
    assert comp2["set_number"] == "TLOK-002"

    # Numeric string fast-path
    comp3 = await service.get_card_by_query("50000103")
    assert comp3 is not None
    assert comp3["name"] == "The Seed of Creation"

    # 3. Multi-criteria filtering
    cards = await service.get_cards_by_filter(card_type="Monster")
    assert len(cards) >= 1
    assert any(m["id"] == 50000101 for m in cards)

    # 4. search_cards ranking
    suggestions = await service.search_cards("Kas", limit=10)
    assert len(suggestions) >= 1


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Card Autocomplete Formatting
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_card_service_all_card_types_and_autocomplete_formatting(test_db_path):
    # 1. Test format_card_autocomplete_choice across card frames
    c_mon = {
        "id": 50000101, "set_number": "TLOK-001", "name": "Kasutamaiza, the Creator of Kustomazi",
        "card_type": "Monster", "card_subtype": "Effect", "attribute": "DIVINE",
        "level_or_rank_or_link": 12, "monster_type": "Creator"
    }
    lbl_mon = format_card_autocomplete_choice(c_mon)
    assert len(lbl_mon) <= 100
    assert "TLOK-001 | Kasutamaiza, the Creator of Kustomazi" in lbl_mon

    c_xyz = {
        "id": 50000201, "set_number": "TLOK-050", "name": "Abyssal Emperor",
        "card_type": "Monster", "card_subtype": "Xyz / Effect", "attribute": "WATER",
        "level_or_rank_or_link": 4, "monster_type": "Aqua"
    }
    lbl_xyz = format_card_autocomplete_choice(c_xyz)
    assert len(lbl_xyz) <= 100
    assert "Rank 4" in lbl_xyz

    c_link = {
        "id": 50000301, "set_number": "TLOK-055", "name": "Cybernetic Enforcer",
        "card_type": "Monster", "card_subtype": "Link / Effect", "attribute": "LIGHT",
        "level_or_rank_or_link": 3, "monster_type": "Cyberse"
    }
    lbl_link = format_card_autocomplete_choice(c_link)
    assert len(lbl_link) <= 100
    assert "Link-3" in lbl_link

    c_pen = {
        "id": 50000401, "set_number": "TLOK-060", "name": "Starlight Magician",
        "card_type": "Monster", "card_subtype": "Pendulum / Effect", "attribute": "DARK",
        "level_or_rank_or_link": 7, "scale": 8, "monster_type": "Spellcaster"
    }
    lbl_pen = format_card_autocomplete_choice(c_pen)
    assert len(lbl_pen) <= 100
    assert "S:8" in lbl_pen

    c_field = {"id": 50000102, "set_number": "TLOK-002", "name": "The Void of Creation", "card_type": "Spell", "card_subtype": "Field"}
    lbl_field = format_card_autocomplete_choice(c_field)
    assert "Spell/Field" in lbl_field

    # 2. Partitioned cardpool retrieval
    service = CardService(test_db_path)
    partitioned = await service.get_all_cards_partitioned()
    assert "main_deck" in partitioned
    assert "extra_deck" in partitioned

    # 3. Trailing tag sanitization in get_card_by_query
    q_with_tag = "Kasutamaiza, the Creator of Kustomazi [DIVINE ★12 Creator]"
    found = await service.get_card_by_query(q_with_tag)
    assert found is not None
    assert found["id"] == 50000101


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Telemetry Analytics and Mutators
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_card_service_telemetry_analytics_and_mutators(test_db_path):
    service = CardService(test_db_path)
    cid = 50000101
    cid2 = 50000102

    # 1. Reset target cards to clean baseline
    await service.reset_card_telemetry(cid)
    await service.reset_card_telemetry(cid2)

    stats_initial = await service.get_card_usage_stats(cid)
    assert stats_initial["times_drawn"] == 0

    # 2. Draw mutators
    await service.track_card_draw(cid, count=2)
    await service.track_cards_drawn([cid, cid2, cid2])

    stats_draw = await service.get_card_usage_stats(cid)
    assert stats_draw["times_drawn"] == 3

    # 3. Play mutators
    await service.track_card_play(cid, count=1)
    await service.track_cards_played([cid, cid2])

    stats_play = await service.get_card_usage_stats(cid)
    assert stats_play["times_played"] == 2

    # 4. Match result mutators
    await service.track_card_match_result(cid, is_win=True)
    stats_match = await service.get_card_usage_stats(cid)
    assert stats_match["wins"] == 1

    # 5. Deck inclusion mutators
    await service.track_deck_inclusion(cid, delta=3)
    stats_deck = await service.get_card_usage_stats(cid)
    assert stats_deck["times_decked"] == 3

    # 6. Cleanup test mutations
    await service.reset_card_telemetry(cid)
    await service.reset_card_telemetry(cid2)


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Modular Architecture Invariants
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_card_service_modular_architecture(test_db_path):
    # Direct functional execution
    card_direct = await get_card_by_id(test_db_path, 50000101)
    assert card_direct is not None
    assert card_direct["id"] == 50000101

    # Autocomplete functional unit
    ac_results = await search_cards(test_db_path, "Kas", limit=DEFAULT_AUTOCOMPLETE_LIMIT)
    assert len(ac_results) >= 1

    # Formatter unit
    tag = build_card_descriptor_tag(card_direct)
    assert len(tag) > 0

    # Core & Root engine equivalence
    core_svc = CoreCardService(test_db_path)
    root_svc = RootCardService(test_db_path)
    assert type(core_svc) is type(root_svc)


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_card_service_lookup_and_telemetry",
    "test_card_service_discovery_and_autocomplete_engine",
    "test_card_service_all_card_types_and_autocomplete_formatting",
    "test_card_service_telemetry_analytics_and_mutators",
    "test_card_service_modular_architecture",
]
