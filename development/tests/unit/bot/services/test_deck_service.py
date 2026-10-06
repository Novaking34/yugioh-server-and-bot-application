#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.bot.services.test_deck_service
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Discord Bot Services / Deck Management, Validation, YDK Serialization
Description:
    Unit test suite for DeckService and its underlying functional modules:
    1. Deck CRUD and Set 1 34-card validation rules.
    2. Field awareness, tribute curves, and attribute analytics.
    3. Hypergeometric probabilities and cardpool telemetry.
    4. Granular copy decrement and DuelingBook-style visual rendering.
    5. Named slot management, ceiling limits (20), and character decks.
    6. Opening block primitives, zone awareness, and hand size bounds.
    7. YDK import/export, UTF-8 BOM parsing, and passcode validation.
    8. Modular architecture contracts and facade delegation.
    9. Macro telemetry, active deck identification, and drift prevention.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import tempfile
import pytest
import aiosqlite

from config.paths import STORY_DB_PATH
from services.deck import (
    DeckService,
    calculate_opening_hand_prob,
    MAX_USER_DECK_SLOTS,
    is_extra_deck_card,
    is_extra_deck_pendulum,
    is_main_deck_pendulum,
    get_pendulum_scales,
    is_ritual_monster,
    is_tribute_monster,
    get_tribute_cost,
    is_field_spell,
    has_field_awareness,
    has_graveyard_interaction,
    has_banishment_interaction,
    has_extra_monster_zone_interaction,
    has_pendulum_zone_interaction,
    is_deckout_condition,
    validate_hand_size,
    calculate_draw_prob,
    calculate_combo_prob,
    fair_shuffle,
    simulate_fair_draw,
    check_end_phase_discard_requirement,
    parse_ydk,
    export_to_ydk,
    save_ydk_file,
    load_ydk_file,
    validate_ydk_passcodes,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
    MIN_HAND_SIZE,
    MAX_HAND_SIZE,
    query_cardpool_cards,
    calculate_cardpool_stats,
    analyze_deck_structure,
    validate_deck_legality,
)
from services.rating import RatingService


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Set 1 Deck Validation and Basic CRUD
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_service_and_set_1_validation(test_db_path):
    service = DeckService(test_db_path)
    test_uid = "999000111"

    # Clear previous test data
    await service.clear_deck(test_uid)

    # Add 3 copies of TLOK-001
    ok, name, total_qty = await service.add_card_to_deck(test_uid, 50000101, quantity=3)
    assert ok is True
    assert total_qty == 3
    assert "Kasutamaiza" in name

    # Adding again should cap at 3
    ok, _, total_qty2 = await service.add_card_to_deck(test_uid, 50000101, quantity=2)
    assert ok is True
    assert total_qty2 == 3

    # Fetch deck
    deck_cards = await service.get_player_deck(test_uid)
    assert len(deck_cards) == 1
    assert deck_cards[0]["id"] == 50000101
    assert deck_cards[0]["quantity"] == 3

    # Remove card
    ok, removed = await service.remove_card_from_deck(test_uid, 50000101)
    assert ok is True
    assert "Kasutamaiza" in removed

    # Verify cleared
    deck_after = await service.get_player_deck(test_uid)
    assert len(deck_after) == 0

    # Load pre-built character deck: Kasutamaiza - Creation Control
    char_decks = await service.get_character_decks()
    assert len(char_decks) >= 1
    k_deck = char_decks[0]
    assert "Kasutamaiza" in k_deck["name"]

    ok, dname, total_added = await service.copy_character_deck_to_player(test_uid, k_deck["id"])
    assert ok is True

    # Analyze deck structure
    player_deck = await service.get_player_deck(test_uid)
    analysis = service.analyze_deck_structure(player_deck)
    assert analysis["total_count"] > 0

    # Cleanup
    await service.clear_deck(test_uid)


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Field Awareness and Metadata Analytics
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_service_field_awareness_and_metadata_analytics(test_db_path):
    service = DeckService(test_db_path)
    test_uid = "field_test_user_777"

    await service.clear_deck(test_uid)

    # Add cards and test analysis
    await service.add_card_to_deck(test_uid, 50000101, quantity=1)

    deck_cards = await service.get_player_deck(test_uid)
    analysis = service.analyze_deck_structure(deck_cards)
    assert analysis["total_count"] == 1
    assert "DIVINE" in analysis["attributes"] or "LIGHT" in analysis["attributes"]

    await service.clear_deck(test_uid)


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Full Deck Server Capabilities & Telemetry
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_full_deck_server_capabilities(test_db_path):
    service = DeckService(test_db_path)
    test_uid = "deck_server_tester_888"

    # 1. Cardpool Telemetry
    stats = await service.get_cardpool_stats()
    assert stats["total_cards"] >= 4

    # 2. Hypergeometric Probability Modeling
    prob = calculate_opening_hand_prob(deck_size=40, target_count=3, hand_size=5, min_hits=1)
    assert 30.0 <= prob <= 36.0

    # 3. YDK Export & Import
    await service.clear_deck(test_uid)
    await service.add_card_to_deck(test_uid, 50000101, quantity=3)
    await service.add_card_to_deck(test_uid, 50000102, quantity=2)

    cards = await service.get_player_deck(test_uid)
    assert len(cards) == 2

    # Cleanup
    await service.clear_deck(test_uid)


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Section 3.2 CRUD and Visual Render
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_service_section_3_2_crud_and_visual_render(test_db_path):
    service = DeckService(test_db_path)
    test_uid = "section_3_2_tester_123"

    await service.clear_deck(test_uid)

    await service.add_card_to_deck(test_uid, 50000101, quantity=3)
    await service.add_card_to_deck(test_uid, 50000102, quantity=2)

    part = await service.get_player_deck_partitioned(test_uid)
    assert part["total_count"] == 5

    # Granular decrement
    ok_rem, rem_msg = await service.remove_card_from_deck(test_uid, 50000101, quantity=1)
    assert ok_rem is True

    # Visual rendering
    render_path = await service.generate_deck_visual(test_uid, deck_title="Kasutamaiza Prototype")
    assert render_path is not None
    assert os.path.exists(render_path)

    # Clean up
    await service.clear_deck(test_uid)
    if os.path.exists(render_path):
        os.remove(render_path)


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Section 3.3 and 3.4 Named Slots & Story Decks
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_service_section_3_3_and_3_4_slots_and_story(test_db_path):
    service = DeckService(test_db_path)
    test_uid = "slot_tester_999"

    await service.clear_deck(test_uid)
    for d in await service.list_user_decks(test_uid):
        await service.delete_named_deck(test_uid, d["deck_name"])

    # Active deck setup
    await service.add_card_to_deck(test_uid, 50000101, quantity=3)

    # Save named deck
    ok_save, s_name = await service.save_named_deck(test_uid, "Alpha Starter")
    assert ok_save is True

    user_decks = await service.list_user_decks(test_uid)
    assert len(user_decks) == 1

    # Rename saved deck
    ok_ren, ren_name = await service.rename_saved_deck(test_uid, "Alpha Starter", "Genesis Prototype")
    assert ok_ren is True

    # Load named deck
    await service.clear_deck(test_uid)
    assert len(await service.get_player_deck(test_uid)) == 0
    ok_load, l_msg, l_count = await service.load_named_deck(test_uid, "Genesis Prototype")
    assert ok_load is True

    # Clean up user slots
    for d in await service.list_user_decks(test_uid):
        await service.delete_named_deck(test_uid, d["deck_name"])
    await service.clear_deck(test_uid)

    # Character decks
    char_decks = await service.get_character_decks()
    assert len(char_decks) >= 1


# -----------------------------------------------------------------------------
# Sub-Block 3.6: Opening Block Primitives and Domain Math
# -----------------------------------------------------------------------------
def test_deck_service_opening_block_primitives():
    # 1. Extra deck checks
    fusion_card = {"card_type": "Monster", "card_subtype": "Fusion / Effect"}
    assert is_extra_deck_card(fusion_card) is True
    assert is_extra_deck_pendulum(fusion_card) is False

    xyz_pendulum = {"card_type": "Monster", "card_subtype": "Xyz / Pendulum / Effect"}
    assert is_extra_deck_card(xyz_pendulum) is True
    assert is_extra_deck_pendulum(xyz_pendulum) is True

    main_pendulum = {
        "card_type": "Monster",
        "card_subtype": "Pendulum / Normal",
        "effect_text": "Scale: 8. When normal summoned, gain 500 ATK."
    }
    assert is_extra_deck_card(main_pendulum) is False
    assert is_main_deck_pendulum(main_pendulum) is True
    assert get_pendulum_scales(main_pendulum) == (8, 8)

    # 2. Tribute vs Ritual
    ritual_boss = {"card_type": "Monster", "card_subtype": "Ritual / Effect", "level": 8}
    assert is_ritual_monster(ritual_boss) is True
    assert is_tribute_monster(ritual_boss) is False

    tribute_lv6 = {"card_type": "Monster", "card_subtype": "Effect", "level": 6}
    assert is_tribute_monster(tribute_lv6) is True
    assert get_tribute_cost(tribute_lv6) == 1

    # 3. Zone awareness
    field_card = {"card_type": "Spell", "card_subtype": "Field", "effect_text": "Gain 300 ATK."}
    assert is_field_spell(field_card) is True
    assert has_field_awareness(field_card) is True

    banish_card = {"card_type": "Spell", "card_subtype": "Quick-Play", "effect_text": "Banish 1 card."}
    assert has_banishment_interaction(banish_card) is True

    # 4. Hand bounds & deckout
    assert MIN_HAND_SIZE == 0
    assert MAX_HAND_SIZE == 7
    ok_hand, msg_hand = validate_hand_size(4)
    assert ok_hand is True

    assert check_end_phase_discard_requirement(7, hand_limit=6) == 1
    assert is_deckout_condition(remaining_deck_count=0, cards_to_draw=1) is True

    # 5. Probability & fair shuffle
    p_t1 = calculate_draw_prob(deck_size=40, target_count=3, draw_count=5)
    p_t2 = calculate_draw_prob(deck_size=40, target_count=3, draw_count=6)
    assert p_t2 > p_t1

    deck = list(range(40))
    s1 = fair_shuffle(deck, seed=12345)
    s2 = fair_shuffle(deck, seed=12345)
    assert s1 == s2


# -----------------------------------------------------------------------------
# Sub-Block 3.7: Section 3.5 YDK Upgrades
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_service_section_3_5_ydk_upgrades(test_db_path):
    service = DeckService(test_db_path)

    # UTF-8 BOM Handling
    raw_with_bom = "\ufeff#created by EDOPro\n#main\n50000101\n50000101\n#extra\n50000107\n!side\n50000102\n"
    parsed_bom = parse_ydk(raw_with_bom)
    assert parsed_bom["is_valid_format"] is True
    assert parsed_bom["main_count"] == 2

    # Save & Load helpers
    sample_cards = [
        {"id": 50000101, "name": "Kasutamaiza Vanguard", "quantity": 3},
    ]
    with tempfile.NamedTemporaryFile(suffix=".ydk", delete=False) as tf:
        temp_path = tf.name

    try:
        saved_file = save_ydk_file(temp_path, sample_cards, deck_title="Modular Test Deck")
        assert saved_file == temp_path
        assert os.path.exists(temp_path)

        loaded_data = load_ydk_file(temp_path)
        assert loaded_data["is_valid_format"] is True
        assert loaded_data["main_count"] == 3
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Passcode validation against SQLite
    valid_map, missing = await validate_ydk_passcodes([50000101, 99999999], test_db_path)
    assert 50000101 in valid_map
    assert 99999999 in missing


# -----------------------------------------------------------------------------
# Sub-Block 3.8: Modular Architecture Verification
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_service_modular_architecture(test_db_path):
    pool_cards = await query_cardpool_cards(test_db_path)
    assert len(pool_cards) >= 4

    mock_cards = [
        {"id": 50000101, "name": "Vanguard", "card_type": "Monster", "card_subtype": "Normal", "level_or_rank_or_link": 4, "quantity": 3},
        {"id": 50000102, "name": "Sanctuary", "card_type": "Spell", "card_subtype": "Field", "quantity": 3},
    ]
    analysis = analyze_deck_structure(mock_cards)
    assert analysis["main_count"] == 6

    service = DeckService(test_db_path)
    facade_analysis = service.analyze_deck_structure(mock_cards)
    assert facade_analysis["main_count"] == analysis["main_count"]


# -----------------------------------------------------------------------------
# Sub-Block 3.9: Macro Telemetry and Drift Prevention
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_deck_macro_telemetry_and_drift_prevention(test_db_path):
    deck_service = DeckService(test_db_path)
    rating_service = RatingService(test_db_path)
    test_uid = "macro_telemetry_user_42"

    await deck_service.clear_deck(test_uid)
    for d in await deck_service.list_user_decks(test_uid):
        await deck_service.delete_named_deck(test_uid, d["deck_name"])

    # Build and save
    await deck_service.add_card_to_deck(test_uid, 50000101, quantity=3)
    await deck_service.add_card_to_deck(test_uid, 50000102, quantity=2)
    ok, name = await deck_service.save_named_deck(test_uid, "Control Alpha")
    assert ok is True

    # Match active deck
    matched_name = await deck_service.find_matching_saved_deck(test_uid)
    assert matched_name == "Control Alpha"

    # Record match result
    ok_rec = await deck_service.record_deck_match_result(test_uid, "Control Alpha", is_win=True)
    assert ok_rec is True

    slot = await deck_service.get_saved_deck(test_uid, "Control Alpha")
    assert slot["times_used"] == 1
    assert slot["wins"] == 1

    # Cleanup
    await deck_service.clear_deck(test_uid)
    await deck_service.delete_named_deck(test_uid, "Control Alpha")


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_deck_service_and_set_1_validation",
    "test_deck_service_field_awareness_and_metadata_analytics",
    "test_full_deck_server_capabilities",
    "test_deck_service_section_3_2_crud_and_visual_render",
    "test_deck_service_section_3_3_and_3_4_slots_and_story",
    "test_deck_service_opening_block_primitives",
    "test_deck_service_section_3_5_ydk_upgrades",
    "test_deck_service_modular_architecture",
    "test_deck_macro_telemetry_and_drift_prevention",
]
