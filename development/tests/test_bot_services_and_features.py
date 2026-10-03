#!/usr/bin/env python3
"""
=============================================================================
Unit & Integration Tests: Discord Bot Services, ELO & Story Campaign
=============================================================================
Tests:
1. CardService (Lookups, Autocomplete, Telemetry)
2. DeckService (Add/Remove, Set 1 34-Card Validation, Character Decks)
3. RatingService (ELO Algorithm, Tier Badges, Match Logging, Leaderboard)
4. StoryService (Progress Tracking, Stage Progression, Title & Card Unlocks)
5. DuelManager (Concurrency, Recovery, Cleanup)
=============================================================================
"""

import os
import sys
import pytest
import aiosqlite
import asyncio

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BOT_DIR = os.path.join(BASE_DIR, "production", "main", "discord_bot")
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config.paths import STORY_DB_PATH
from services.card_service import CardService
from services.deck import DeckService
from services.rating_service import RatingService
from services.story_service import StoryService
from services.duel_service import DuelManager
from utils import build_rank_embed, build_leaderboard_embed, build_card_stats_embed, build_story_stage_embed


# =============================================================================
# 1. CARD SERVICE TESTS
# =============================================================================

@pytest.mark.anyio
async def test_card_service_lookup_and_telemetry():
    service = CardService(STORY_DB_PATH)

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


# =============================================================================
# 2. DECK SERVICE TESTS
# =============================================================================

@pytest.mark.anyio
async def test_deck_service_and_set_1_validation():
    service = DeckService(STORY_DB_PATH)
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
    assert total_added == 40  # 34 Main + 6 Extra

    # Analyze deck structure - verify Set 1 alpha accommodation
    player_deck = await service.get_player_deck(test_uid)
    analysis = service.analyze_deck_structure(player_deck)
    assert analysis["total_count"] == 40
    assert analysis["main_count"] == 34
    assert analysis["extra_count"] == 6
    assert analysis["is_set_1_standard"] is True
    assert len(analysis["notes"]) >= 1
    assert "Set 1 Alpha Cardpool Note" in analysis["notes"][0]

    # Test copying Deck 2: LeSpookie Singles
    spookie_deck = next(d for d in char_decks if "LeSpookie" in d["name"])
    assert spookie_deck is not None
    ok2, dname2, total_added2 = await service.copy_character_deck_to_player(test_uid, spookie_deck["id"])
    assert ok2 is True
    assert total_added2 == 50  # 36 Main + 14 Extra
    player_deck2 = await service.get_player_deck(test_uid)
    analysis2 = service.analyze_deck_structure(player_deck2)
    assert analysis2["total_count"] == 50
    assert analysis2["main_count"] == 36
    assert analysis2["extra_count"] == 14

    # Cleanup
    await service.clear_deck(test_uid)


# =============================================================================
# 3. RATING SERVICE & ELO ENGINE TESTS
# =============================================================================

@pytest.mark.anyio
async def test_rating_service_elo_calculations():
    service = RatingService(STORY_DB_PATH)

    # 1. Mathematical Elo Calculation
    # Equal players: Winner gets ~ +16 to +20, Loser drops equally
    w_elo, l_elo = service.compute_elo_change(1200, 1200, 1.0, 15, 15)
    assert w_elo > 1200
    assert l_elo < 1200
    assert w_elo - 1200 == 1200 - l_elo

    # Draw should yield equal ratings
    d1_elo, d2_elo = service.compute_elo_change(1200, 1200, 0.5, 15, 15)
    assert d1_elo == 1200
    assert d2_elo == 1200

    # Underdog beats favorite: large gain
    underdog_w, favorite_l = service.compute_elo_change(1100, 1500, 1.0, 15, 15)
    assert (underdog_w - 1100) > 25

    # 2. Tier Classification
    tier_kog, badge_kog, _ = service.get_tier_info(2150)
    assert tier_kog == "King of Games"
    assert badge_kog == "👑"

    tier_gold, badge_gold, _ = service.get_tier_info(1550)
    assert tier_gold == "Gold Duelist"
    assert badge_gold == "🥇"

    tier_bronze, badge_bronze, _ = service.get_tier_info(1200)
    assert tier_bronze == "Bronze Duelist"
    assert badge_bronze == "🥉"

    # 3. Live Match Recording
    p1_uid = "888000001"
    p2_uid = "888000002"
    res = await service.record_duel_match(
        p1_uid, p2_uid, winner_id=p1_uid, match_type="RANKED", turns=4,
        summary="P1 achieved OTK with The Great Kasutamaiza.",
        p1_deck=[50000101, 50000107],
        p2_deck=[50000102, 50000103],
        p1_name="TesterAlpha",
        p2_name="TesterBeta"
    )
    assert res["winner_id"] == p1_uid
    assert res["p1_elo_delta"] > 0
    assert res["p2_elo_delta"] < 0

    p1_data = await service.get_or_create_player(p1_uid)
    assert p1_data["wins"] >= 1
    assert p1_data["win_streak"] >= 1

    # 4. Leaderboard Lookup
    lb = await service.get_leaderboard(limit=5)
    assert len(lb) >= 1
    assert any(p["user_id"] == p1_uid for p in lb)


# =============================================================================
# 4. STORY SERVICE TESTS
# =============================================================================

@pytest.mark.anyio
async def test_story_service_progression_and_rewards():
    service = StoryService(STORY_DB_PATH)
    test_uid = "777000001"

    # Reset test user to ensure clean state
    async with aiosqlite.connect(STORY_DB_PATH) as db:
        await db.execute("DELETE FROM player_story_progress WHERE user_id = ?", (test_uid,))
        await db.commit()

    # 1. Initial Progress

    progress = await service.get_or_create_player_progress(test_uid)
    assert progress["current_chapter_id"] == 1
    assert progress["current_stage_number"] == 1

    # 2. Stage Inspection
    stage1 = await service.get_stage(1, 1)
    assert stage1 is not None
    assert stage1["title"] == "Whispers of the Primordial Void"
    assert stage1["reward_title"] == "Void Walker"
    assert stage1["reward_card_id"] == 50000102

    # 3. Complete Stage 1
    result = await service.complete_stage(test_uid, 1)
    assert result["success"] is True
    assert result["next_stage_number"] == 2
    assert result["reward_title"] == "Void Walker"
    assert result["reward_card_name"] == "The Void of Creation"

    # Verify updated player record
    progress_after = await service.get_or_create_player_progress(test_uid)
    assert progress_after["current_stage_number"] == 2
    assert progress_after["highest_stage_completed"] == 1
    assert "Void Walker" in progress_after["titles_list"]
    assert progress_after["total_story_wins"] >= 1

    # 4. Admin Reset
    await service.reset_progress(test_uid, stage_number=1)
    progress_reset = await service.get_or_create_player_progress(test_uid)
    assert progress_reset["current_stage_number"] == 1

    # Clean up test user
    async with aiosqlite.connect(STORY_DB_PATH) as db:
        await db.execute("DELETE FROM player_story_progress WHERE user_id = ?", (test_uid,))
        await db.execute("DELETE FROM player_decks WHERE user_id = ?", (test_uid,))
        await db.commit()


@pytest.mark.anyio
async def test_story_duel_session_scripted_and_ai_encounters():
    """Validates that Story Mode loads from DB with both Scripted and Dynamic AI modes."""
    from unittest.mock import MagicMock
    from cogs.story import StoryDuelSession

    story_service = StoryService(STORY_DB_PATH)
    card_service = CardService(STORY_DB_PATH)
    deck_service = DeckService(STORY_DB_PATH)

    mock_user = MagicMock()
    mock_user.id = 5550001
    mock_user.display_name = "DuelistPlayer"

    cards = await card_service.get_all_cards()
    player_deck = [c["id"] for c in cards] * 2
    npc_deck = [c["id"] for c in cards] * 2

    # --- 1. Test Stage 1: SCRIPTED Encounter ---
    stage1 = await story_service.get_stage(1, 1)
    assert stage1["encounter_type"] == "SCRIPTED"
    assert stage1["script"] is not None

    session1 = StoryDuelSession(mock_user, stage1, player_deck, npc_deck)
    assert session1.encounter_type == "SCRIPTED"
    assert len(session1.player_hand) == 5
    assert len(session1.npc_hand) == 5

    # Execute Scripted Turn 1
    action_text, dmg = await session1.execute_npc_turn(card_service)
    assert dmg > 0
    assert "Seed of Creation" in action_text or "Echo" in action_text

    # --- 2. Test Stage 2: DYNAMIC AI Encounter ---
    stage2 = await story_service.get_stage(1, 2)
    assert stage2["encounter_type"] == "AI"

    session2 = StoryDuelSession(mock_user, stage2, player_deck, npc_deck)
    assert session2.encounter_type == "AI"

    # Execute Dynamic AI Turn: draws card, inspects hand, summons/activates
    action_text_ai, dmg_ai = await session2.execute_npc_turn(card_service)
    assert dmg_ai > 0
    assert session2.npc_name in action_text_ai
    # Assert that cards in hand were tracked with RNG
    assert len(session2.npc_hand) >= 1

    # --- 3. Test Chapter 2 Stage 2: SCRIPTED Encounter (A Wicked Shadow) ---
    stage_spookie_shadow = await story_service.get_stage(2, 2)
    assert stage_spookie_shadow["encounter_type"] == "SCRIPTED"
    assert "Wicked Shadow" in stage_spookie_shadow["opponent_name"]
    session_shadow = StoryDuelSession(mock_user, stage_spookie_shadow, player_deck, npc_deck)
    act_shadow, dmg_shadow = await session_shadow.execute_npc_turn(card_service)
    assert dmg_shadow > 0
    assert "Wicked Shadow" in act_shadow or "Trick-or-Treat" in act_shadow

    # --- 4. Test Chapter 2 Stage 3: SCRIPTED Encounter (Magnolia) ---
    stage_magnolia = await story_service.get_stage(2, 3)
    assert stage_magnolia["encounter_type"] == "SCRIPTED"
    assert "Magnolia" in stage_magnolia["opponent_name"]
    session_magnolia = StoryDuelSession(mock_user, stage_magnolia, player_deck, npc_deck)
    act_mag, dmg_mag = await session_magnolia.execute_npc_turn(card_service)
    assert dmg_mag > 0
    assert "Magnolia" in act_mag


# =============================================================================
# 5. DUEL MANAGER TESTS
# =============================================================================


def test_duel_manager_lifecycle():
    dm = DuelManager()
    assert dm.active_duel_count == 0

    dummy_session = object()
    dm.register_session(101, 102, dummy_session)
    assert dm.is_user_dueling(101) is True
    assert dm.is_user_dueling(102) is True
    assert dm.is_user_dueling(103) is False
    assert dm.active_duel_count == 1

    # Force reset
    ok = dm.force_reset_user(101)
    assert ok is True
    assert dm.is_user_dueling(101) is False
    assert dm.is_user_dueling(102) is False
    assert dm.active_duel_count == 0


# =============================================================================
# 6. UTILITY EMBED BUILDER TESTS
# =============================================================================

def test_utility_embed_builders():
    # 1. Rank Embed
    player_data = {
        "user_id": "123456",
        "username": "TestMaster",
        "elo": 1750,
        "wins": 10,
        "losses": 2,
        "draws": 0,
        "win_streak": 5,
        "highest_streak": 5,
        "highest_elo": 1750,
        "tier": "Platinum Duelist",
        "season_id": "Season 1"
    }
    rank_embed = build_rank_embed(player_data)
    assert "TestMaster" in rank_embed.title
    assert "1750 ELO" in rank_embed.fields[0].value

    # 2. Leaderboard Embed
    lb_embed = build_leaderboard_embed([player_data], "Season 1")
    assert "Leaderboard" in lb_embed.title
    assert "TestMaster" in lb_embed.fields[0].value

    # 3. Card Stats Embed
    card_stats = {
        "name": "Kasutamaiza, the Creator of Kustomazi",
        "set_number": "TLOK-001",
        "card_type": "Monster",
        "card_subtype": "Effect",
        "rarity": "Ultra Rare",
        "times_decked": 4,
        "times_drawn": 12,
        "times_played": 8,
        "wins": 7,
        "losses": 1,
        "win_rate": 87.5
    }
    stats_embed = build_card_stats_embed(card_stats)
    assert "Kasutamaiza" in stats_embed.title
    assert "87.5%" in stats_embed.fields[2].value

    # 4. Story Stage Embed
    stage_data = {
        "stage_number": 1,
        "title": "Whispers of the Primordial Void",
        "intro_dialogue": "The void whispers into the infinite darkness.",
        "opponent_name": "Echo of the Void",
        "opponent_title": "Primordial Emanation",
        "opponent_deck_name": "Kasutamaiza - Creation Control",
        "reward_title": "Void Walker",
        "reward_card_name": "The Void of Creation",
        "reward_card_set": "TLOK-002",
        "opponent_avatar": None
    }
    story_embed = build_story_stage_embed(stage_data, {"highest_stage_completed": 0})
    assert "Stage 1" in story_embed.title
    assert "Echo of the Void" in story_embed.fields[0].value


# =============================================================================
# 7. STORY JSON SYNC & NATURAL DUEL RNG TESTS
# =============================================================================

@pytest.mark.anyio
async def test_story_json_sync_and_data_loading():
    """Validates that story chapters/stages sync dynamically from JSON without code changes."""
    story_service = StoryService(STORY_DB_PATH)
    res = await story_service.sync_all_story_files()
    assert res["chapters_synced"] >= 2
    assert res["stages_synced"] >= 6
    assert "chapter_1_the_genesis_of_kustomazi.json" in res["files"]
    assert "chapter_2_the_lespookiest_night.json" in res["files"]

    stage3 = await story_service.get_stage(1, 3)
    assert stage3 is not None
    assert stage3["opponent_name"] == "ProfessorSeanEX"
    assert stage3["encounter_type"] == "SCRIPTED"
    assert stage3["reward_title"] == "Architect's Champion"

    stage6 = await story_service.get_stage(2, 3)
    assert stage6 is not None
    assert stage6["opponent_name"] == "Magnolia, the Ghost of LeSpookie Street"
    assert stage6["encounter_type"] == "SCRIPTED"
    assert stage6["reward_title"] == "Lantern Maiden's Bond"


@pytest.mark.anyio
async def test_duel_rng_and_card_play_features():
    """Validates natural Yu-Gi-Oh RNG (shuffling, draws, mill, dice, coin) and card plays."""
    from unittest.mock import MagicMock
    from cogs.story import StoryDuelSession
    from cogs.duel_engine import DuelSession

    story_service = StoryService(STORY_DB_PATH)
    card_service = CardService(STORY_DB_PATH)

    mock_p1 = MagicMock()
    mock_p1.id = 11122201
    mock_p1.display_name = "PlayerOne"

    mock_p2 = MagicMock()
    mock_p2.id = 11122202
    mock_p2.display_name = "PlayerTwo"

    cards = await card_service.get_all_cards()
    full_deck = [c["id"] for c in cards] * 2

    # 1. Test StoryDuelSession Natural RNG & Card Play
    stage = await story_service.get_stage(1, 1)
    story_session = StoryDuelSession(mock_p1, stage, full_deck, full_deck)

    # 5-card opening hand
    assert len(story_session.player_hand) == 5
    init_deck_count = len(story_session.player_deck)

    # RNG Card Draw
    drawn = story_session.draw_player_card()
    assert drawn is not None
    assert len(story_session.player_hand) == 6
    assert len(story_session.player_deck) == init_deck_count - 1

    # RNG Card Mill to Graveyard
    milled = story_session.mill_player_card()
    assert milled is not None
    assert milled in story_session.player_gy
    assert len(story_session.player_deck) == init_deck_count - 2

    # Card Play from Hand (Monster)
    hand_count_before = len(story_session.player_hand)
    first_cid = story_session.player_hand[0]
    card_obj = await card_service.get_card_by_query(str(first_cid))
    play_res = story_session.play_player_card(card_obj)
    assert len(story_session.player_hand) == hand_count_before - 1
    if card_obj["card_type"] == "Monster":
        assert any(m["id"] == first_cid for m in story_session.player_field)
    else:
        assert first_cid in story_session.player_gy

    # 2. Test PvP DuelSession Natural RNG
    pvp_session = DuelSession(mock_p1, mock_p2, full_deck, full_deck, match_type="CASUAL")
    assert len(pvp_session.hands[mock_p1.id]) == 5
    assert len(pvp_session.hands[mock_p2.id]) == 5

    # PvP Deck Draw
    p1_draw = pvp_session.draw_card(mock_p1.id)
    assert p1_draw is not None
    assert len(pvp_session.hands[mock_p1.id]) == 6

    # PvP Mill
    p2_mill = pvp_session.mill_card(mock_p2.id)
    assert p2_mill is not None
    assert p2_mill in pvp_session.gy[mock_p2.id]


def test_duel_board_model_and_field_rendering():
    """Validates the DuelBoard model, zone allocations, card positions, and visual renderers."""
    from utils import DuelBoard, render_duel_field_ascii, build_board_guide_embed

    board = DuelBoard()
    assert len(board.mmz) == 5
    assert len(board.stz) == 5
    assert board.field_spell is None
    assert len(board.gy) == 0
    assert len(board.banished) == 0

    # 1. Summon monster in Attack Position
    slot = board.summon_monster({"id": 50000101, "name": "Kasutamaiza", "atk": 4000, "def": 4000}, position="ATK")
    assert slot == 0
    assert board.mmz[0]["name"] == "Kasutamaiza"
    assert board.mmz[0]["position"] == "ATK"
    assert board.highest_atk_monster["atk"] == 4000

    # 2. Summon monster in Defense Position
    slot2 = board.summon_monster({"id": 50000102, "name": "Void of Creation", "atk": 0, "def": 2000}, position="DEF")
    assert slot2 == 1
    assert board.mmz[1]["position"] == "DEF"

    # 3. Play Field Spell
    fname = board.play_field_spell({"id": 50000114, "name": "The Sacred Temple of Kustomazi"})
    assert fname == "The Sacred Temple of Kustomazi"
    assert board.field_spell["name"] == "The Sacred Temple of Kustomazi"

    # 4. Banished Zone & Graveyard
    board.banish_card(50000103)
    assert 50000103 in board.banished
    board.send_to_gy(50000104)
    assert 50000104 in board.gy

    # 5. Render ASCII Mat
    opp_board = DuelBoard()
    ascii_mat = render_duel_field_ascii(
        board, opp_board, "PlayerOne", "Opponent", 8000, 8000, 5, 5, 29, 29
    )
    assert "4000" in ascii_mat
    assert "The Sacred Temple" in ascii_mat

    # 6. Board Guide Embed
    embed = build_board_guide_embed()
    assert "Duel Field" in embed.title
    assert any("Main Monster Zones" in f.name for f in embed.fields)


def test_card_types_and_races_guide_metadata():
    """Validates the card types guide, spell speeds, trap classifications, and 26 races."""
    from utils import (
        SPELL_CARD_TYPES, TRAP_CARD_TYPES, MONSTER_CARD_FRAMES,
        ALL_26_MONSTER_RACES, build_card_types_guide_embed
    )

    # 1. Spell Subtypes (6 Types)
    assert len(SPELL_CARD_TYPES) == 6
    assert "Normal Spell" in SPELL_CARD_TYPES
    assert "Quick-Play Spell" in SPELL_CARD_TYPES
    assert SPELL_CARD_TYPES["Quick-Play Spell"]["speed"] == "Spell Speed 2"

    # 2. Trap Subtypes (3 Types)
    assert len(TRAP_CARD_TYPES) == 3
    assert "Counter Trap" in TRAP_CARD_TYPES
    assert TRAP_CARD_TYPES["Counter Trap"]["speed"] == "Spell Speed 3"

    # 3. Monster Frames
    assert "Normal Monster" in MONSTER_CARD_FRAMES
    assert "Effect Monster" in MONSTER_CARD_FRAMES
    assert "Fusion Monster" in MONSTER_CARD_FRAMES
    assert "Link Monster" in MONSTER_CARD_FRAMES

    # 4. All 26 Races
    assert len(ALL_26_MONSTER_RACES) == 26
    races_names = [r[0] for r in ALL_26_MONSTER_RACES]
    assert "Dragon" in races_names
    assert "Divine-Beast" in races_names
    assert "Creator-God" in races_names
    assert "Illusion" in races_names
    assert "Cyberse" in races_names

    # 5. Embed Generation for all categories
    for cat in ["overview", "spells", "traps", "monsters", "races", "attributes", "levels_ranks"]:
        emb = build_card_types_guide_embed(cat)
        assert emb.title is not None
        assert len(emb.fields) >= 1


def test_card_attributes_levels_ranks_and_combat_calculations():
    """Validates the 7 attributes, levels vs ranks metadata, tribute rules, and battle calculations."""
    from utils import (
        CARD_ATTRIBUTES, LEVELS_AND_RANKS_DATA,
        get_tribute_requirement, calculate_battle_damage
    )
    from cogs.duel_engine import DuelSession
    from unittest.mock import MagicMock

    # 1. Validate 7 Elemental Attributes
    assert len(CARD_ATTRIBUTES) == 7
    expected_attrs = ["LIGHT", "DARK", "EARTH", "WATER", "FIRE", "WIND", "DIVINE"]
    for attr in expected_attrs:
        assert attr in CARD_ATTRIBUTES
        assert "symbol" in CARD_ATTRIBUTES[attr]
        assert "kanji" in CARD_ATTRIBUTES[attr]
        assert "bitmask" in CARD_ATTRIBUTES[attr]

    assert CARD_ATTRIBUTES["LIGHT"]["bitmask"] == 0x10
    assert CARD_ATTRIBUTES["DARK"]["bitmask"] == 0x20
    assert CARD_ATTRIBUTES["DIVINE"]["bitmask"] == 0x40

    # 2. Validate Levels & Ranks Data
    assert "levels" in LEVELS_AND_RANKS_DATA
    assert "ranks" in LEVELS_AND_RANKS_DATA
    assert "link_ratings" in LEVELS_AND_RANKS_DATA
    assert "pendulum_scales" in LEVELS_AND_RANKS_DATA
    assert "RANKS ARE NOT LEVELS" in LEVELS_AND_RANKS_DATA["ranks"]["golden_rule"]

    # 3. Validate Tribute Requirements
    assert get_tribute_requirement(1) == 0
    assert get_tribute_requirement(4) == 0
    assert get_tribute_requirement(5) == 1
    assert get_tribute_requirement(6) == 1
    assert get_tribute_requirement(7) == 2
    assert get_tribute_requirement(10) == 2
    assert get_tribute_requirement(None) == 0

    # 4. Validate Battle Damage Calculations
    # A. Direct Attack
    atk_monster = {"id": 50000101, "name": "The Great Kasutamaiza", "atk": 4000, "def": 4000, "position": "ATK"}
    direct_res = calculate_battle_damage(atk_monster, defender=None, is_direct=True)
    assert direct_res["is_direct"] is True
    assert direct_res["damage"] == 4000
    assert direct_res["damaged_side"] == "defender"

    # B. ATK vs ATK: Attacker destroys Defender
    def_monster_atk = {"id": 50000103, "name": "Kasutamaiza Scout", "atk": 1500, "def": 1200, "position": "ATK"}
    atk_win_res = calculate_battle_damage(atk_monster, def_monster_atk, is_direct=False)
    assert atk_win_res["damage"] == 2500
    assert atk_win_res["damaged_side"] == "defender"
    assert atk_win_res["defender_destroyed"] is True
    assert atk_win_res["attacker_destroyed"] is False

    # C. ATK vs ATK: Defender higher ATK (Attacker crashes)
    atk_lose_res = calculate_battle_damage(def_monster_atk, atk_monster, is_direct=False)
    assert atk_lose_res["damage"] == 2500
    assert atk_lose_res["damaged_side"] == "attacker"
    assert atk_lose_res["attacker_destroyed"] is True
    assert atk_lose_res["defender_destroyed"] is False

    # D. ATK vs ATK: Mutual Destruction (Tie)
    same_atk = {"id": 50000104, "name": "Kasutamaiza Mirror", "atk": 4000, "def": 1000, "position": "ATK"}
    tie_res = calculate_battle_damage(atk_monster, same_atk, is_direct=False)
    assert tie_res["damage"] == 0
    assert tie_res["damaged_side"] == "neither"
    assert tie_res["attacker_destroyed"] is True
    assert tie_res["defender_destroyed"] is True

    # E. ATK vs DEF: Attacker destroys Defender (no damage)
    def_monster_def = {"id": 50000103, "name": "Kasutamaiza Defender", "atk": 1000, "def": 2000, "position": "DEF"}
    def_win_res = calculate_battle_damage(atk_monster, def_monster_def, is_direct=False)
    assert def_win_res["damage"] == 0
    assert def_win_res["defender_destroyed"] is True
    assert def_win_res["attacker_destroyed"] is False

    # F. ATK vs DEF: Defender DEF higher (Attacker takes recoil)
    wall_def = {"id": 50000105, "name": "Iron Wall", "atk": 0, "def": 3000, "position": "DEF"}
    recoil_res = calculate_battle_damage(def_monster_atk, wall_def, is_direct=False)
    assert recoil_res["damage"] == 1500
    assert recoil_res["damaged_side"] == "attacker"
    assert recoil_res["defender_destroyed"] is False

    # 5. DuelSession has active DuelBoards initialized
    u1, u2 = MagicMock(), MagicMock()
    u1.id, u1.display_name = 101, "PlayerOne"
    u2.id, u2.display_name = 102, "PlayerTwo"
    session = DuelSession(u1, u2, [50000101] * 10, [50000102] * 10)
    assert 101 in session.boards
    assert 102 in session.boards
    assert len(session.boards[101].mmz) == 5


@pytest.mark.anyio
async def test_deck_service_field_awareness_and_metadata_analytics():
    """
    Validates DeckService analytical breakdown for:
    - Tribute curves (Level 1-4, Level 5-6, Level 7+)
    - Attribute and Species distribution
    - Field Awareness Engine detection and warning diagnostics
    """
    service = DeckService(STORY_DB_PATH)
    test_uid = "field_test_user_777"

    await service.clear_deck(test_uid)

    # 1. Deck with Field-dependent cards but NO Field Spells -> Warning triggered!
    # Card 50000116: Hexla (requires Field Spell)
    await service.add_card_to_deck(test_uid, 50000116, quantity=3)
    # Card 50000101: Kasutamaiza Lv 12 (requires 3 tributes)
    await service.add_card_to_deck(test_uid, 50000101, quantity=1)

    deck_cards = await service.get_player_deck(test_uid)
    analysis = service.analyze_deck_structure(deck_cards)

    assert analysis["field_spell_count"] == 0
    assert analysis["field_dependent_count"] == 3
    assert "Field Engine Warning" in analysis["field_status"]
    assert analysis["tributes"]["level_1_to_4"] == 3
    assert analysis["tributes"]["level_7_plus"] == 1
    assert "DIVINE" in analysis["attributes"]
    assert "Zombie" in analysis["races"]

    # 2. Add Field Spell -> Field Engine becomes Active!
    # Card 50000138: LeSpookie Street, Cursed Lane (Field Spell)
    await service.add_card_to_deck(test_uid, 50000138, quantity=2)

    deck_cards2 = await service.get_player_deck(test_uid)
    analysis2 = service.analyze_deck_structure(deck_cards2)
    assert analysis2["field_spell_count"] == 2
    assert "Field Engine Active" in analysis2["field_status"]
    assert len(analysis2["field_spells"]) == 1
    assert analysis2["field_spells"][0]["name"] == "LeSpookie Street, Cursed Lane"

    await service.clear_deck(test_uid)


def test_official_rarities_and_set_distribution():
    """
    Validates that:
    1. Official Yu-Gi-Oh! rarity constants are loaded.
    2. All 64 cards in the database have official Yu-Gi-Oh! rarities.
    3. The 14 Kasutamaiza cards have authentic boss/engine rarities.
    """
    import sqlite3
    from constants import OFFICIAL_RARITIES, is_official_rarity, RARITY_SECRET_RARE, RARITY_ULTRA_RARE

    assert len(OFFICIAL_RARITIES) >= 5
    assert is_official_rarity("Secret Rare") is True
    assert is_official_rarity("Ultra Rare") is True
    assert is_official_rarity("Super Rare") is True
    assert is_official_rarity("Rare") is True
    assert is_official_rarity("Common") is True
    assert is_official_rarity("MadeUpRarity") is False

    conn = sqlite3.connect(STORY_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, rarity FROM custom_cards ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    assert len(rows) == 64
    for cid, name, rarity in rows:
        assert is_official_rarity(rarity), f"Card {cid} '{name}' has non-official rarity '{rarity}'"

    # Verify Kasutamaiza deity rarities
    card_map = {r[0]: r[2] for r in rows}
    assert card_map[50000101] == RARITY_SECRET_RARE  # Kasutamaiza, the Creator
    assert card_map[50000107] == RARITY_SECRET_RARE  # The Great Kasutamaiza
    assert card_map[50000106] == RARITY_ULTRA_RARE   # Mohousha the Accursed
    assert card_map[50000109] == RARITY_ULTRA_RARE   # Divine Justice


@pytest.mark.anyio
async def test_full_deck_server_capabilities():
    """
    Validates full deck server capabilities:
    1. Dynamic cardpool stats (> 64 cards, > 40 main singles).
    2. YDK export & import serialization.
    3. Multi-deck named slot management.
    4. Hypergeometric probability calculation.
    5. Master Rule deck legality validation.
    """
    from services.deck import DeckService, calculate_opening_hand_prob

    service = DeckService(STORY_DB_PATH)
    test_uid = "deck_server_tester_888"

    # 1. Dynamic Cardpool Telemetry
    stats = await service.get_cardpool_stats()
    assert stats["total_cards"] >= 64
    assert stats["main_deck_pool"] >= 40
    assert stats["has_legal_40_singles"] is True
    assert stats["extra_monsters"] >= 16

    # Upgraded Section 3.1 verification: Rarities, Mechanics, Zone awareness, formatting
    assert stats["rarity_breakdown"]["secret_rares"] == 5
    assert stats["rarity_breakdown"]["ultra_rares"] == 8
    assert stats["mechanics_breakdown"]["extra_deck"]["fusions"] == 2
    assert stats["mechanics_breakdown"]["extra_deck"]["synchros"] == 9
    assert stats["mechanics_breakdown"]["extra_deck"]["links"] == 5
    assert stats["zone_awareness"]["field_providers"] >= 4
    assert stats["zone_awareness"]["field_beneficiaries"] >= 30
    assert stats["zone_awareness"]["graveyard_interactors"] >= 40

    summary_str = service.format_cardpool_summary(stats)
    assert "Cardpool Telemetry Report" in summary_str
    assert "Secret" in summary_str
    assert "Ultra" in summary_str

    # 2. Hypergeometric Probability Modeling
    # In a 40 card deck with 3 Field Spells, opening 1+ Field Spell in 5 cards
    prob = calculate_opening_hand_prob(deck_size=40, target_count=3, hand_size=5, min_hits=1)
    assert 30.0 <= prob <= 36.0  # Approx 33.8%

    # 3. YDK Export & Import
    await service.clear_deck(test_uid)
    await service.add_card_to_deck(test_uid, 50000101, quantity=3)
    await service.add_card_to_deck(test_uid, 50000110, quantity=3)
    await service.add_card_to_deck(test_uid, 50000107, quantity=2)  # Extra deck fusion

    cards = await service.get_player_deck(test_uid)
    ydk_str = service.export_to_ydk(cards, deck_title="Kasutamaiza Test")
    assert "#main" in ydk_str
    assert "#extra" in ydk_str
    assert "50000101" in ydk_str
    assert "50000107" in ydk_str

    # Test re-importing YDK string into a fresh deck
    import_uid = "deck_server_importer_999"
    await service.clear_deck(import_uid)
    ok_imp, msg_imp, total_imp = await service.import_from_ydk(import_uid, ydk_str)
    assert ok_imp is True
    assert total_imp == 8

    # 4. Multi-Deck Named Slots
    save_ok, saved_name = await service.save_named_deck(test_uid, "Creation Blitz")
    assert save_ok is True
    assert saved_name == "Creation Blitz"

    user_decks = await service.list_user_decks(test_uid)
    assert len(user_decks) >= 1
    assert user_decks[0]["deck_name"] == "Creation Blitz"

    # Wipe active deck and load from named slot
    await service.clear_deck(test_uid)
    assert len(await service.get_player_deck(test_uid)) == 0

    load_ok, load_name, loaded_cards = await service.load_named_deck(test_uid, "Creation Blitz")
    assert load_ok is True
    assert loaded_cards == 8
    assert len(await service.get_player_deck(test_uid)) == 3

    # Clean up
    del_ok = await service.delete_named_deck(test_uid, "Creation Blitz")
    assert del_ok is True
    await service.clear_deck(test_uid)
    await service.clear_deck(import_uid)


@pytest.mark.anyio
async def test_deck_service_section_3_2_crud_and_visual_render():
    """
    Validates Section 3.2 upgrades:
    1. get_player_deck_partitioned min/max checks and legality flags.
    2. Granular copy decrement via remove_card_from_deck(quantity=X).
    3. DuelingBook-style visual deck image rendering via generate_deck_visual.
    """
    import os
    from services.deck import DeckService

    service = DeckService(STORY_DB_PATH)
    test_uid = "section_3_2_tester_123"

    await service.clear_deck(test_uid)

    # 1. Add cards (Main and Extra deck)
    await service.add_card_to_deck(test_uid, 50000101, quantity=3)  # Main monster (Kasutamaiza)
    await service.add_card_to_deck(test_uid, 50000110, quantity=3)  # Main spell (Contact from Beyond)
    await service.add_card_to_deck(test_uid, 50000107, quantity=2)  # Extra deck fusion

    # Partitioned retrieval & min/max legality check
    part = await service.get_player_deck_partitioned(test_uid)
    assert part["main_count"] == 6
    assert part["extra_count"] == 2
    assert part["total_count"] == 8
    assert part["is_legal"] is False  # Under 40 cards!
    assert "Under Minimum" in part["legality_badge"]
    assert len(part["violations"]) >= 1
    assert "Minimum 40 required" in part["violations"][0]

    # 2. Granular copy decrement
    # Remove 1 copy of 50000101 (quantity drops from 3 to 2)
    ok_rem, rem_msg = await service.remove_card_from_deck(test_uid, 50000101, quantity=1)
    assert ok_rem is True
    assert "(-1)" in rem_msg

    deck_after_rem = await service.get_player_deck(test_uid)
    card_101 = next(c for c in deck_after_rem if c["id"] == 50000101)
    assert card_101["quantity"] == 2

    # Remove remaining copies completely
    ok_rem_all, rem_all_msg = await service.remove_card_from_deck(test_uid, 50000101, quantity=2)
    assert ok_rem_all is True
    assert 50000101 not in [c["id"] for c in await service.get_player_deck(test_uid)]

    # 3. DuelingBook-Style Visual Deck Image Rendering
    # Add a few cards back for rendering
    await service.add_card_to_deck(test_uid, 50000102, quantity=2)
    await service.add_card_to_deck(test_uid, 50000106, quantity=1)  # Extra deck

    render_path = await service.generate_deck_visual(test_uid, deck_title="Kasutamaiza Prototype")
    assert render_path is not None
    assert os.path.exists(render_path)
    assert os.path.getsize(render_path) > 10000  # Non-empty valid PNG

    # Clean up
    await service.clear_deck(test_uid)
    if os.path.exists(render_path):
        os.remove(render_path)


@pytest.mark.anyio
async def test_deck_service_section_3_3_and_3_4_slots_and_story():
    """
    Validates Section 3.3 and 3.4 upgrades:
    Section 3.3:
    - Named slot saving with MAX_USER_DECK_SLOTS (20) ceiling.
    - Slot limit rejection on 21st distinct deck, while allowing update of existing.
    - list_user_decks enriched with main_count, extra_count, is_legal, legality_badge.
    - get_saved_deck, rename_saved_deck, load_named_deck, delete_named_deck.
    Section 3.4:
    - get_character_decks enriched with card counts, MR5 legality, ai_elo, story_chapter.
    - get_character_deck_by_id with partitioned card counts and legality.
    - get_ai_deck_for_elo matching appropriate story decks across ELO tiers.
    - generate_character_deck_visual rendering canvas for story decks.
    - format_character_deck_summary producing human-readable reports.
    """
    import os
    from services.deck import DeckService, MAX_USER_DECK_SLOTS

    service = DeckService(STORY_DB_PATH)
    test_uid = "slot_tester_999"

    # Clean up any leftover test data
    await service.clear_deck(test_uid)
    for d in await service.list_user_decks(test_uid):
        await service.delete_named_deck(test_uid, d["deck_name"])

    # 1. Active Deck setup
    await service.add_card_to_deck(test_uid, 50000101, quantity=3)
    await service.add_card_to_deck(test_uid, 50000106, quantity=2)

    # 2. Save named deck
    ok_save, s_name = await service.save_named_deck(test_uid, "Alpha Starter")
    assert ok_save is True
    assert s_name == "Alpha Starter"

    # Enriched list_user_decks
    user_decks = await service.list_user_decks(test_uid)
    assert len(user_decks) == 1
    d0 = user_decks[0]
    assert d0["deck_name"] == "Alpha Starter"
    assert d0["main_count"] == 3
    assert d0["extra_count"] == 2
    assert d0["total_count"] == 5
    assert d0["is_legal"] is False
    assert "Under Min" in d0["legality_badge"]

    # 3. Rename saved deck
    ok_ren, ren_name = await service.rename_saved_deck(test_uid, "Alpha Starter", "Genesis Prototype")
    assert ok_ren is True
    assert ren_name == "Genesis Prototype"

    # Fetch via get_saved_deck
    saved = await service.get_saved_deck(test_uid, "Genesis Prototype")
    assert saved is not None
    assert saved["deck_name"] == "Genesis Prototype"
    assert saved["total_count"] == 5

    # 4. Slot Limit enforcement
    # Fill remaining slots up to MAX_USER_DECK_SLOTS (20)
    for i in range(2, MAX_USER_DECK_SLOTS + 1):
        ok, _ = await service.save_named_deck(test_uid, f"Slot {i}")
        assert ok is True

    # 21st distinct slot should fail
    ok_overflow, err_msg = await service.save_named_deck(test_uid, "Slot Overflow")
    assert ok_overflow is False
    assert "Deck slot limit reached" in err_msg

    # Overwriting an existing slot (e.g. Slot 2) should still succeed
    ok_overwrite, _ = await service.save_named_deck(test_uid, "Slot 2")
    assert ok_overwrite is True

    # 5. Load named deck into cleared deck
    await service.clear_deck(test_uid)
    assert len(await service.get_player_deck(test_uid)) == 0
    ok_load, l_msg, l_count = await service.load_named_deck(test_uid, "Genesis Prototype")
    assert ok_load is True
    assert l_count == 5
    assert len(await service.get_player_deck(test_uid)) == 2

    # Clean up user slots
    for d in await service.list_user_decks(test_uid):
        await service.delete_named_deck(test_uid, d["deck_name"])
    assert len(await service.list_user_decks(test_uid)) == 0
    await service.clear_deck(test_uid)

    # 6. Section 3.4 - Character Decks Telemetry & Progression
    char_decks = await service.get_character_decks()
    assert len(char_decks) >= 4

    # Verify enriched fields
    for cd in char_decks:
        assert "main_count" in cd
        assert "extra_count" in cd
        assert "is_legal" in cd
        assert "legality_badge" in cd
        assert "ai_elo" in cd
        assert "story_chapter" in cd

    # Deck 1 (Kasutamaiza Creation Control)
    k_deck = char_decks[0]
    assert k_deck["id"] == 1
    assert k_deck["main_count"] == 34
    assert k_deck["extra_count"] == 6

    # Deck 4 (Genesis & Mortal Realm - MR5 Legal 43 Main, 6 Extra)
    mortal_deck = next((d for d in char_decks if d["id"] == 4), None)
    if mortal_deck:
        assert mortal_deck["is_legal"] is True
        assert mortal_deck["main_count"] == 43
        assert mortal_deck["extra_count"] == 6
        assert mortal_deck["ai_elo"] == 1100

    # 7. AI ELO Deck Selector
    deck_low = await service.get_ai_deck_for_elo(1100)
    assert deck_low is not None
    assert abs(deck_low["ai_elo"] - 1100) <= 100

    deck_high = await service.get_ai_deck_for_elo(1800)
    assert deck_high is not None
    assert deck_high["ai_elo"] >= 1600

    # 8. Character Deck Visual Rendering
    img_path = await service.generate_character_deck_visual(1)
    assert img_path is not None
    assert os.path.exists(img_path)
    assert os.path.getsize(img_path) > 10000

    # Summary formatting
    summary = service.format_character_deck_summary(char_decks[0])
    assert "Kasutamaiza" in summary
    assert "Dimensions" in summary

    # Clean up render
    if os.path.exists(img_path):
        os.remove(img_path)


def test_deck_service_opening_block_primitives():
    """
    Validates Opening Block primitives in deck_service:
    1. Extra Deck & Hybrid Pendulums (Fusion/Synchro/Xyz + Pendulum).
    2. Main Deck Tribute vs. Ritual vs. Main Deck Pendulums.
    3. Zone awareness (Field Spell, GY, EMZ, PZ, Banishment).
    4. Hand bounds (0-7), End Phase limits, and Deckout detection.
    5. Full-range draw probability, bivariate combos, and fair play distribution.
    """
    from services.deck import (
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
        ZONE_MAIN_DECK,
        ZONE_EXTRA_DECK,
        ZONE_HAND,
        ZONE_FIELD_SPELL,
        ZONE_GRAVEYARD,
        ZONE_BANISHMENT,
        ZONE_EXTRA_MONSTER,
        ZONE_PENDULUM,
        MIN_HAND_SIZE,
        MAX_HAND_SIZE,
    )

    # 1. Extra Deck & Hybrid Pendulum tests
    fusion_card = {"card_type": "Monster", "card_subtype": "Fusion / Effect"}
    assert is_extra_deck_card(fusion_card) is True
    assert is_extra_deck_pendulum(fusion_card) is False

    xyz_pendulum = {"card_type": "Monster", "card_subtype": "Xyz / Pendulum / Effect"}
    assert is_extra_deck_card(xyz_pendulum) is True
    assert is_extra_deck_pendulum(xyz_pendulum) is True
    assert is_main_deck_pendulum(xyz_pendulum) is False

    main_pendulum = {
        "card_type": "Monster",
        "card_subtype": "Pendulum / Normal",
        "effect_text": "Scale: 8. When normal summoned, gain 500 ATK."
    }
    assert is_extra_deck_card(main_pendulum) is False
    assert is_main_deck_pendulum(main_pendulum) is True
    assert get_pendulum_scales(main_pendulum) == (8, 8)

    # 2. Main Deck Tribute vs Ritual
    ritual_boss = {"card_type": "Monster", "card_subtype": "Ritual / Effect", "level": 8}
    assert is_ritual_monster(ritual_boss) is True
    assert is_tribute_monster(ritual_boss) is False
    assert get_tribute_cost(ritual_boss) == 0

    tribute_lv6 = {"card_type": "Monster", "card_subtype": "Effect", "level": 6}
    assert is_tribute_monster(tribute_lv6) is True
    assert get_tribute_cost(tribute_lv6) == 1

    tribute_lv8 = {"card_type": "Monster", "card_subtype": "Normal", "level": 8}
    assert is_tribute_monster(tribute_lv8) is True
    assert get_tribute_cost(tribute_lv8) == 2

    low_lv4 = {"card_type": "Monster", "card_subtype": "Effect", "level": 4}
    assert is_tribute_monster(low_lv4) is False
    assert get_tribute_cost(low_lv4) == 0

    # 3. Zone Awareness & PSCT Keywords
    field_card = {"card_type": "Spell", "card_subtype": "Field", "effect_text": "All Toon monsters gain 300 ATK."}
    assert is_field_spell(field_card) is True
    assert has_field_awareness(field_card) is True

    field_beneficiary = {"card_type": "Monster", "card_subtype": "Effect", "effect_text": "While you control a Field Spell, this card cannot be destroyed."}
    assert is_field_spell(field_beneficiary) is False
    assert has_field_awareness(field_beneficiary) is True

    gy_card = {"card_type": "Trap", "card_subtype": "Normal", "effect_text": "Target 1 monster from your GY; Special Summon it."}
    assert has_graveyard_interaction(gy_card) is True

    banish_card = {"card_type": "Spell", "card_subtype": "Quick-Play", "effect_text": "Banish 1 card on the field face-down."}
    assert has_banishment_interaction(banish_card) is True

    link_card = {"card_type": "Monster", "card_subtype": "Link / Effect", "effect_text": "Must be Special Summoned to an Extra Monster Zone."}
    assert has_extra_monster_zone_interaction(link_card) is True

    pz_card = {"card_type": "Spell", "card_subtype": "Normal", "effect_text": "Place 1 card from your Deck in your Pendulum Zone."}
    assert has_pendulum_zone_interaction(pz_card) is True

    # 4. Hand bounds and Deckout
    assert MIN_HAND_SIZE == 0
    assert MAX_HAND_SIZE == 7
    ok_hand, msg_hand = validate_hand_size(4)
    assert ok_hand is True

    # Standard End Phase: 7 cards requires 1 discard down to 6
    ok_disc, msg_disc = validate_hand_size(7, is_end_phase=True)
    assert ok_disc is True
    assert "discard 1 card" in msg_disc

    # Mid-turn play: 15 cards in hand is completely legal (no limit during turn)
    ok_mid, msg_mid = validate_hand_size(15, is_end_phase=False)
    assert ok_mid is True
    assert "legal during active play" in msg_mid

    # Card modifier: Hieroglyph Lithograph (hand limit is 7)
    ok_hiero, msg_hiero = validate_hand_size(7, is_end_phase=True, hand_limit=7)
    assert ok_hiero is True
    assert "within End Phase limit" in msg_hiero

    # Card modifier: Infinite Cards (hand limit is None)
    ok_inf, msg_inf = validate_hand_size(20, is_end_phase=True, hand_limit=None)
    assert ok_inf is True

    # Discard count calculation
    from services.deck import check_end_phase_discard_requirement
    assert check_end_phase_discard_requirement(7, hand_limit=6) == 1
    assert check_end_phase_discard_requirement(9, hand_limit=6) == 3
    assert check_end_phase_discard_requirement(7, hand_limit=7) == 0
    assert check_end_phase_discard_requirement(15, hand_limit=None) == 0

    assert is_deckout_condition(remaining_deck_count=0, cards_to_draw=1) is True
    assert is_deckout_condition(remaining_deck_count=2, cards_to_draw=3) is True
    assert is_deckout_condition(remaining_deck_count=5, cards_to_draw=5) is False

    # 5. Probabilities & Fair Play Distribution
    # Turn 2 Going 2nd draw prob (6 cards) vs Turn 1 (5 cards)
    p_t1 = calculate_draw_prob(deck_size=40, target_count=3, draw_count=5)
    p_t2 = calculate_draw_prob(deck_size=40, target_count=3, draw_count=6)
    assert p_t2 > p_t1

    # Combo probability: Field Spell (3 copies) + Beneficiary (3 copies) in 5-card hand
    p_combo = calculate_combo_prob(deck_size=40, target_a_count=3, target_b_count=3, draw_count=5)
    assert 5.0 <= p_combo <= 12.0  # Approx 8.5%

    # Fair shuffle with seed reproducibility
    deck = list(range(40))
    s1 = fair_shuffle(deck, seed=12345)
    s2 = fair_shuffle(deck, seed=12345)
    assert s1 == s2
    assert s1 != deck  # Actually shuffled

    # Fair draw simulation with deckout
    drawn, rem, deckout = simulate_fair_draw(deck, draw_count=5)
    assert len(drawn) == 5
    assert len(rem) == 35
    assert deckout is False

    drawn_over, rem_over, deckout_over = simulate_fair_draw(deck[:2], draw_count=5)
    assert deckout_over is True


@pytest.mark.anyio
async def test_deck_service_section_3_5_ydk_upgrades():
    """
    Validates Section 3.5 .YDK serialization & ingestion upgrades:
    - UTF-8 BOM handling in YDK parsing
    - File save/load helpers
    - Passcode validation against SQLite
    - Section capacity and banlist clamping on import
    - Direct export of player active deck
    """
    import tempfile
    from services.deck import (
        DeckService,
        parse_ydk,
        export_to_ydk,
        save_ydk_file,
        load_ydk_file,
        validate_ydk_passcodes,
        STANDARD_MAX_MAIN_DECK,
        STANDARD_MAX_EXTRA_DECK,
    )

    service = DeckService(STORY_DB_PATH)

    # 1. UTF-8 BOM Handling in parse_ydk
    raw_with_bom = "\ufeff#created by EDOPro\n#main\n50000101\n50000101\n#extra\n50000107\n!side\n50000102\n"
    parsed_bom = parse_ydk(raw_with_bom)
    assert parsed_bom["is_valid_format"] is True
    assert parsed_bom["main_count"] == 2
    assert parsed_bom["extra_count"] == 1
    assert parsed_bom["side_count"] == 1
    assert parsed_bom["total_count"] == 4
    assert 50000101 in parsed_bom["passcode_counts"]

    # 2. File Save & Load Helpers
    sample_cards = [
        {"id": 50000101, "name": "Kasutamaiza Vanguard", "quantity": 3},
        {"id": 50000107, "name": "Mohousha, Master of Mimicry", "quantity": 1, "card_type": "Monster", "card_subtype": "Fusion / Effect"},
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
        assert loaded_data["extra_count"] == 1
        assert loaded_data["passcode_counts"][50000101] == 3
        assert loaded_data["passcode_counts"][50000107] == 1
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 3. Passcode Validation against SQLite
    valid_map, missing = await validate_ydk_passcodes([50000101, 50000107, 99999999], STORY_DB_PATH)
    assert 50000101 in valid_map
    assert 50000107 in valid_map
    assert 99999999 in missing
    assert len(missing) == 1

    # 4. Import Clamping: Oversized Main Deck & Banlist Clamping
    # Construct a YDK with over 60 main deck cards and extra copies of cards
    oversized_ydk_lines = ["#main"]
    # Add 25 copies each of 3 different cards (total 75 cards, > 60 max)
    oversized_ydk_lines.extend(["50000101"] * 25)
    oversized_ydk_lines.extend(["50000102"] * 25)
    oversized_ydk_lines.extend(["50000103"] * 25)
    oversized_ydk_lines.append("#extra")
    oversized_ydk_lines.extend(["50000107"] * 20)  # 20 extra deck cards (> 15 max)
    oversized_ydk_lines.append("!side\n")

    test_uid = "ydk_clamp_tester_user"
    await service.clear_deck(test_uid)

    ok_clamp, msg_clamp, total_clamped = await service.import_from_ydk(test_uid, "\n".join(oversized_ydk_lines))
    assert ok_clamp is True

    # Check partitioned deck of imported clamped deck
    clamped_partition = await service.get_player_deck_partitioned(test_uid)
    assert clamped_partition["main_count"] <= STANDARD_MAX_MAIN_DECK
    assert clamped_partition["extra_count"] <= STANDARD_MAX_EXTRA_DECK
    # Banlist clamps each card to max 3 copies
    for c in clamped_partition["main_deck"]:
        assert c["quantity"] <= 3

    # 5. Direct export_player_deck_to_ydk
    exported_str = await service.export_player_deck_to_ydk(test_uid, deck_title="Clamped Export")
    assert "#main" in exported_str
    assert "#extra" in exported_str
    assert "Clamped Export" in exported_str

    # Clean up test user
    await service.clear_deck(test_uid)


@pytest.mark.anyio
async def test_deck_service_modular_architecture():
    """
    Validates the modular C/C++ style architecture ("header" vs "c" compilation units):
    - deck_constants: header limits, hand bounds, zones
    - deck_types: TypedDict declarations
    - deck_cardpool: dynamic cardpool telemetry
    - deck_storage: player active deck CRUD & database persistence
    - deck_slots: multi-deck named slot profiles
    - deck_story: story & character pre-constructed decks
    - deck_analytics: tactical analysis engine & Master Rule legality validation
    - deck_visual: Pillow visual canvas rendering
    - deck_service: central facade orchestration
    """
    from services.deck import (
        CardDict,
        DeckPartition,
        ParsedYDK,
        SavedDeckSlot,
        StoryDeckRecord,
        DeckAnalysisResult,
        LegalityResult,
        query_cardpool_cards,
        calculate_cardpool_stats,
        fetch_player_deck,
        partition_player_deck,
        list_user_deck_slots,
        fetch_character_decks,
        analyze_deck_structure,
        validate_deck_legality,
        DeckService,
    )

    # 1. Direct modular queries (standalone compilation units)
    pool_cards = await query_cardpool_cards(STORY_DB_PATH)
    assert len(pool_cards) >= 60

    pool_stats = await calculate_cardpool_stats(STORY_DB_PATH)
    assert pool_stats["total_cards"] >= 60
    assert pool_stats["has_legal_40_singles"] is True

    # 2. Deck Analytics on modular unit
    mock_cards = [
        {"id": 50000101, "name": "Vanguard", "card_type": "Monster", "card_subtype": "Normal", "level_or_rank_or_link": 4, "quantity": 3},
        {"id": 50000110, "name": "Sanctuary", "card_type": "Spell", "card_subtype": "Field", "quantity": 3},
    ]
    analysis = analyze_deck_structure(mock_cards)
    assert analysis["main_count"] == 6
    assert analysis["field_spell_count"] == 3

    legality = validate_deck_legality(mock_cards)
    assert legality["is_legal"] is False  # 6 cards < 40 min

    # 3. Core Engine Delegation Verification
    service = DeckService(STORY_DB_PATH)
    facade_analysis = service.analyze_deck_structure(mock_cards)
    assert facade_analysis["main_count"] == analysis["main_count"]

    facade_legality = service.validate_deck_legality(mock_cards)
    assert facade_legality["is_legal"] == legality["is_legal"]


@pytest.mark.anyio
async def test_deck_macro_telemetry_and_drift_prevention():
    """
    Validates:
    1. Deck usage and match win/loss recording on player_saved_decks.
    2. Active deck identification via find_matching_saved_deck.
    3. Micro counter drift prevention when overwriting player decks via YDK/story imports.
    4. End-to-end match recording in RatingService with deck names.
    """
    from services.deck import DeckService
    from services.rating_service import RatingService

    deck_service = DeckService(STORY_DB_PATH)
    rating_service = RatingService(STORY_DB_PATH)
    test_uid = "macro_telemetry_user_42"

    await deck_service.clear_deck(test_uid)
    for d in await deck_service.list_user_decks(test_uid):
        await deck_service.delete_named_deck(test_uid, d["deck_name"])

    # 1. Build an active deck and save it
    await deck_service.add_card_to_deck(test_uid, 50000101, quantity=3)
    await deck_service.add_card_to_deck(test_uid, 50000102, quantity=2)
    ok, name = await deck_service.save_named_deck(test_uid, "Control Alpha")
    assert ok is True

    # 2. find_matching_saved_deck matches "Control Alpha"
    matched_name = await deck_service.find_matching_saved_deck(test_uid)
    assert matched_name == "Control Alpha"

    # Modify active deck slightly -> should no longer match
    await deck_service.add_card_to_deck(test_uid, 50000103, quantity=1)
    matched_name_after = await deck_service.find_matching_saved_deck(test_uid)
    assert matched_name_after is None

    # Revert active deck by loading saved deck
    ok_load, _, _ = await deck_service.load_named_deck(test_uid, "Control Alpha")
    assert ok_load is True
    assert await deck_service.find_matching_saved_deck(test_uid) == "Control Alpha"

    # 3. Record match result directly
    ok_rec = await deck_service.record_deck_match_result(test_uid, "Control Alpha", is_win=True)
    assert ok_rec is True

    slot = await deck_service.get_saved_deck(test_uid, "Control Alpha")
    assert slot["times_used"] == 1
    assert slot["wins"] == 1
    assert slot["losses"] == 0
    assert slot["win_rate"] == 100.0

    # Record a loss
    await deck_service.record_deck_match_result(test_uid, "Control Alpha", is_win=False)
    slot2 = await deck_service.get_saved_deck(test_uid, "Control Alpha")
    assert slot2["times_used"] == 2
    assert slot2["wins"] == 1
    assert slot2["losses"] == 1
    assert slot2["win_rate"] == 50.0

    # 4. RatingService.record_duel_match macro integration
    res = await rating_service.record_duel_match(
        p1_id=test_uid,
        p2_id="opponent_bot",
        winner_id=test_uid,
        match_type="CASUAL",
        p1_deck=[50000101, 50000102],
        p1_deck_name="Control Alpha"
    )
    assert res["p1_deck_name"] == "Control Alpha"

    slot3 = await deck_service.get_saved_deck(test_uid, "Control Alpha")
    assert slot3["times_used"] == 3
    assert slot3["wins"] == 2
    assert slot3["losses"] == 1
    assert slot3["win_rate"] == 66.7

    # Clean up
    await deck_service.clear_deck(test_uid)
    await deck_service.delete_named_deck(test_uid, "Control Alpha")


@pytest.mark.anyio
async def test_card_service_discovery_and_autocomplete_engine():
    """
    Validates:
    1. Direct indexed lookup via get_card_by_id.
    2. Composite autocomplete query sanitization ("TLOK-001 | Name" and "[50000101] Name").
    3. Multi-criteria card filtering via get_cards_by_filter.
    4. Real-time autocomplete ranking and empty query set ordering in search_cards.
    5. Type-filtered random card retrieval in get_random_card.
    """
    service = CardService(STORY_DB_PATH)

    # 1. Direct O(1) indexed lookup
    card_by_id = await service.get_card_by_id(50000101)
    assert card_by_id is not None
    assert card_by_id["name"] == "Kasutamaiza, the Creator of Kustomazi"
    assert card_by_id["level"] == 12  # Canonical level alias
    assert card_by_id["faction_name"] is not None

    # Non-existent ID returns None
    assert await service.get_card_by_id(99999999) is None

    # 2. Composite label parsing in get_card_by_query
    comp1 = await service.get_card_by_query("TLOK-001 | Kasutamaiza, the Creator of Kustomazi")
    assert comp1 is not None
    assert comp1["id"] == 50000101

    comp2 = await service.get_card_by_query("[50000102] The Void of Creation")
    assert comp2 is not None
    assert comp2["set_number"] == "TLOK-002"

    # Numeric string fast-path
    comp3 = await service.get_card_by_query("50000103")
    assert comp3 is not None
    assert comp3["name"] == "The Seed of Creation"

    # Case-insensitive exact name
    comp4 = await service.get_card_by_query("kasutamaiza, the creator of kustomazi")
    assert comp4 is not None
    assert comp4["id"] == 50000101

    # 3. Multi-criteria filtering
    monsters_divine = await service.get_cards_by_filter(card_type="Monster", attribute="DIVINE")
    assert len(monsters_divine) >= 1
    assert any(m["id"] == 50000101 for m in monsters_divine)

    field_spells = await service.get_cards_by_filter(card_type="Spell", card_subtype="Field")
    assert len(field_spells) >= 1
    for fs in field_spells:
        assert fs["card_type"] == "Spell"
        assert "Field" in (fs.get("card_subtype") or "")

    archetype_cards = await service.get_cards_by_filter(archetype="Kasutamaiza")
    assert len(archetype_cards) >= 1

    # 4. search_cards ranking
    # Autocomplete with "Kas" should rank cards starting with "Kas" at the top
    suggestions = await service.search_cards("Kas", limit=10)
    assert len(suggestions) >= 1
    assert suggestions[0]["name"].startswith("Kas")
    # Verify rich metadata keys
    s0 = suggestions[0]
    assert "id" in s0
    assert "set_number" in s0
    assert "name" in s0
    assert "card_type" in s0
    assert "card_subtype" in s0
    assert "rarity" in s0

    # Empty query yields canonical Set order (TLOK-001, TLOK-002...)
    empty_suggestions = await service.search_cards("", limit=5)
    assert len(empty_suggestions) == 5
    assert empty_suggestions[0]["set_number"] == "TLOK-001"
    assert empty_suggestions[1]["set_number"] == "TLOK-002"

    # 5. Type-filtered get_random_card
    random_spell = await service.get_random_card(card_type="Spell")
    assert random_spell is not None
    assert random_spell["card_type"] == "Spell"

    random_monster = await service.get_random_card(card_type="Monster")
    assert random_monster is not None
    assert random_monster["card_type"] == "Monster"


@pytest.mark.anyio
async def test_card_service_all_card_types_and_autocomplete_formatting():
    """
    Rigorously verifies:
    1. format_card_autocomplete_choice against all card frames and mechanic combinations:
       - Standard Monster (Level, Attribute, Race)
       - Xyz Monster (Rank, Attribute, Race)
       - Link Monster (Link Rating, Attribute, Race)
       - Pendulum Monster (Level, Scale, Attribute, Race)
       - Fusion / Synchro / Ritual Monsters
       - Spell frames (Normal, Field, Quick-Play, Continuous, Equip, Ritual)
       - Trap frames (Normal, Continuous, Counter)
       - Strict <= 100 character ceiling truncation
    2. Partitioned cardpool retrieval via get_all_cards_partitioned.
    3. Scoped autocomplete filtering (by card_type and is_extra_deck).
    4. Query sanitization with trailing autocomplete metadata tags.
    """
    from production.main.discord_bot.services.card_service import format_card_autocomplete_choice

    # 1. Test format_card_autocomplete_choice across card frames
    # Standard Monster
    c_mon = {
        "id": 50000101, "set_number": "TLOK-001", "name": "Kasutamaiza, the Creator of Kustomazi",
        "card_type": "Monster", "card_subtype": "Effect", "attribute": "DIVINE",
        "level_or_rank_or_link": 12, "monster_type": "Creator"
    }
    lbl_mon = format_card_autocomplete_choice(c_mon)
    assert len(lbl_mon) <= 100
    assert "TLOK-001 | Kasutamaiza, the Creator of Kustomazi" in lbl_mon
    assert "DIVINE" in lbl_mon
    assert "★12" in lbl_mon
    assert "Creator" in lbl_mon

    # Xyz Monster
    c_xyz = {
        "id": 50000201, "set_number": "TLOK-050", "name": "Abyssal Emperor",
        "card_type": "Monster", "card_subtype": "Xyz / Effect", "attribute": "WATER",
        "level_or_rank_or_link": 4, "monster_type": "Aqua"
    }
    lbl_xyz = format_card_autocomplete_choice(c_xyz)
    assert len(lbl_xyz) <= 100
    assert "Rank 4" in lbl_xyz
    assert "WATER" in lbl_xyz
    assert "Aqua" in lbl_xyz

    # Link Monster
    c_link = {
        "id": 50000301, "set_number": "TLOK-055", "name": "Cybernetic Enforcer",
        "card_type": "Monster", "card_subtype": "Link / Effect", "attribute": "LIGHT",
        "level_or_rank_or_link": 3, "monster_type": "Cyberse"
    }
    lbl_link = format_card_autocomplete_choice(c_link)
    assert len(lbl_link) <= 100
    assert "Link-3" in lbl_link
    assert "LIGHT" in lbl_link

    # Pendulum Monster
    c_pen = {
        "id": 50000401, "set_number": "TLOK-060", "name": "Starlight Magician",
        "card_type": "Monster", "card_subtype": "Pendulum / Effect", "attribute": "DARK",
        "level_or_rank_or_link": 7, "scale": 8, "monster_type": "Spellcaster"
    }
    lbl_pen = format_card_autocomplete_choice(c_pen)
    assert len(lbl_pen) <= 100
    assert "★7" in lbl_pen
    assert "S:8" in lbl_pen
    assert "DARK" in lbl_pen

    # Spells: Field, Quick-Play, Normal
    c_field = {"id": 50000102, "set_number": "TLOK-002", "name": "The Void of Creation", "card_type": "Spell", "card_subtype": "Field"}
    lbl_field = format_card_autocomplete_choice(c_field)
    assert "Spell/Field" in lbl_field

    c_qp = {"id": 50000115, "set_number": "TLOK-015", "name": "Quick Strike", "card_type": "Spell", "card_subtype": "Quick-Play"}
    lbl_qp = format_card_autocomplete_choice(c_qp)
    assert "Spell/Quick-Play" in lbl_qp

    c_spell_norm = {"id": 50000116, "set_number": "TLOK-016", "name": "Simple Draw", "card_type": "Spell", "card_subtype": "Normal"}
    lbl_spell_norm = format_card_autocomplete_choice(c_spell_norm)
    assert "[Spell]" in lbl_spell_norm

    # Traps: Counter, Continuous, Normal
    c_counter = {"id": 50000130, "set_number": "TLOK-030", "name": "Judgement Strike", "card_type": "Trap", "card_subtype": "Counter"}
    lbl_counter = format_card_autocomplete_choice(c_counter)
    assert "Trap/Counter" in lbl_counter

    c_trap_cont = {"id": 50000131, "set_number": "TLOK-031", "name": "Endless Stasis", "card_type": "Trap", "card_subtype": "Continuous"}
    lbl_trap_cont = format_card_autocomplete_choice(c_trap_cont)
    assert "Trap/Continuous" in lbl_trap_cont

    # Extreme length truncation check (Discord strict 100-char limit)
    c_long = {
        "id": 50000999, "set_number": "TLOK-999",
        "name": "Super Ultra Hyper Mega Extremely Unusually Tremendously Prodigious Champion of the Nether Realms",
        "card_type": "Monster", "card_subtype": "Fusion / Effect", "attribute": "DIVINE",
        "level_or_rank_or_link": 12, "monster_type": "Divine-Beast"
    }
    lbl_long = format_card_autocomplete_choice(c_long)
    assert len(lbl_long) <= 100
    assert lbl_long.endswith("... [DIVINE ★12 Divine-Beast]") or len(lbl_long) == 100

    # 2. Partitioned cardpool retrieval
    service = CardService(STORY_DB_PATH)
    partitioned = await service.get_all_cards_partitioned()
    assert "main_deck" in partitioned
    assert "extra_deck" in partitioned
    assert len(partitioned["main_deck"]) > 0
    assert len(partitioned["extra_deck"]) > 0
    # Total cards in Set 1 must sum up correctly
    assert len(partitioned["main_deck"]) + len(partitioned["extra_deck"]) == 64

    # Verify Extra Deck contains only Extra Deck card types
    for ed_card in partitioned["extra_deck"]:
        ctype = (ed_card.get("card_type") or "").lower()
        csub = (ed_card.get("card_subtype") or "").lower()
        assert ctype in ("fusion", "synchro", "xyz", "link") or any(m in csub for m in ("fusion", "synchro", "xyz", "link"))

    # 3. Scoped autocomplete filtering
    spell_matches = await service.search_cards("", limit=10, card_type="Spell")
    assert len(spell_matches) > 0
    for sm in spell_matches:
        assert sm["card_type"] == "Spell"

    ed_matches = await service.search_cards("", limit=10, is_extra_deck=True)
    assert len(ed_matches) > 0
    for em in ed_matches:
        csub = (em.get("card_subtype") or "").lower()
        ctype = (em.get("card_type") or "").lower()
        assert ctype in ("fusion", "synchro", "xyz", "link") or any(m in csub for m in ("fusion", "synchro", "xyz", "link"))

    # 4. Trailing tag sanitization in get_card_by_query
    q_with_tag = "Kasutamaiza, the Creator of Kustomazi [DIVINE ★12 Creator]"
    found = await service.get_card_by_query(q_with_tag)
    assert found is not None
    assert found["id"] == 50000101


@pytest.mark.anyio
async def test_card_service_telemetry_analytics_and_mutators():
    """
    Rigorously tests Sub-Blocks 3.3 and 3.4 in CardService:
    1. Single and batch draw mutators (track_card_draw, track_cards_drawn).
    2. Single and batch play mutators (track_card_play, track_cards_played).
    3. Match result mutators (track_card_match_result, track_cards_match_result).
    4. Deck inclusion mutators (track_deck_inclusion, batch_track_deck_inclusions).
    5. Telemetry inspection via get_card_usage_stats (metadata, derived ratios).
    6. Multi-axis format overview via get_meta_overview (popularity, playrate, winrate).
    7. Win rate rankings via get_card_win_rates.
    8. Archetype analytics via get_archetype_meta_stats.
    9. Macro cardpool summary via get_cardpool_telemetry_summary.
    10. Underused card discovery via get_underused_cards.
    11. Maintenance reset via reset_card_telemetry.
    """
    service = CardService(STORY_DB_PATH)
    cid = 50000101  # Kasutamaiza, the Creator of Kustomazi
    cid2 = 50000102 # The Void of Creation

    # 1. Reset target cards to clean baseline
    await service.reset_card_telemetry(cid)
    await service.reset_card_telemetry(cid2)

    stats_initial = await service.get_card_usage_stats(cid)
    assert stats_initial["times_drawn"] == 0
    assert stats_initial["times_played"] == 0
    assert stats_initial["wins"] == 0
    assert stats_initial["losses"] == 0
    assert stats_initial["total_matches"] == 0
    assert stats_initial["win_rate"] == 0.0
    assert stats_initial["name"] == "Kasutamaiza, the Creator of Kustomazi"
    assert stats_initial["attribute"] == "DIVINE"
    assert stats_initial["level"] == 12

    # 2. Draw mutators (single with count, and batch opening hand)
    await service.track_card_draw(cid, count=2)
    await service.track_cards_drawn([cid, cid2, cid2])

    stats_draw = await service.get_card_usage_stats(cid)
    assert stats_draw["times_drawn"] == 3
    stats_draw2 = await service.get_card_usage_stats(cid2)
    assert stats_draw2["times_drawn"] == 2

    # 3. Play mutators (single with count, and batch)
    await service.track_card_play(cid, count=1)
    await service.track_cards_played([cid, cid2])

    stats_play = await service.get_card_usage_stats(cid)
    assert stats_play["times_played"] == 2
    assert stats_play["play_to_draw_ratio"] == round(2 / 3 * 100, 1)

    # 4. Match result mutators
    await service.track_card_match_result(cid, is_win=True)
    await service.track_cards_match_result([cid, cid2], is_win=True)
    await service.track_cards_match_result([cid, cid2], is_win=False)

    stats_match = await service.get_card_usage_stats(cid)
    assert stats_match["wins"] == 2
    assert stats_match["losses"] == 1
    assert stats_match["total_matches"] == 3
    assert stats_match["win_rate"] == round(2 / 3 * 100, 1)

    # 5. Deck inclusion mutators (single and batch)
    await service.track_deck_inclusion(cid, delta=3)
    await service.batch_track_deck_inclusions({cid: -1, cid2: 2})

    stats_deck = await service.get_card_usage_stats(cid)
    assert stats_deck["times_decked"] == 2
    stats_deck2 = await service.get_card_usage_stats(cid2)
    assert stats_deck2["times_decked"] == 2

    # 6. Meta overview across all 5 axes
    meta = await service.get_meta_overview(limit=5)
    assert "most_popular" in meta
    assert "most_victorious" in meta
    assert "most_played" in meta
    assert "highest_win_rate" in meta
    assert "most_drawn" in meta

    assert len(meta["most_popular"]) > 0
    assert len(meta["most_victorious"]) > 0
    assert len(meta["most_played"]) > 0
    assert len(meta["most_drawn"]) > 0

    # With full cardpool limit, verify cid is indexed across telemetry
    meta_all = await service.get_meta_overview(limit=64)
    assert any(c["card_id"] == cid for c in meta_all["most_popular"])
    assert any(c["card_id"] == cid for c in meta_all["most_drawn"])

    # Scoped meta overview by card_type
    spell_meta = await service.get_meta_overview(limit=5, card_type="Spell")
    for sm in spell_meta["most_popular"]:
        assert sm["card_type"] == "Spell"

    # 7. Win rate leaderboard
    wr_rankings = await service.get_card_win_rates(limit=5, min_matches=1)
    assert len(wr_rankings) > 0
    assert any(c["card_id"] == cid for c in wr_rankings)

    # 8. Archetype meta stats
    arch_stats = await service.get_archetype_meta_stats("Kasutamaiza")
    assert arch_stats["archetype"] == "Kasutamaiza"
    assert arch_stats["total_cards"] > 0
    assert arch_stats["times_decked"] >= 2
    assert arch_stats["total_matches"] >= 3
    assert arch_stats["top_card_name"] is not None

    # Non-existent archetype returns zeroed contract safely
    empty_arch = await service.get_archetype_meta_stats("NonExistentArchetypeXYZ")
    assert empty_arch["total_cards"] == 0
    assert empty_arch["win_rate"] == 0.0

    # 9. Cardpool telemetry macro summary
    summary = await service.get_cardpool_telemetry_summary()
    assert summary["total_registered_cards"] == 64
    assert summary["distinct_cards_decked"] >= 1
    assert summary["total_deck_inclusions"] >= 1
    assert summary["total_card_draws"] >= 1
    assert summary["total_card_plays"] >= 1

    # 10. Underused card discovery
    underused = await service.get_underused_cards(limit=5)
    assert len(underused) == 5
    for u in underused:
        assert "times_decked" in u
        assert "times_played" in u

    # 11. Cleanup test mutations
    await service.reset_card_telemetry(cid)
    await service.reset_card_telemetry(cid2)




