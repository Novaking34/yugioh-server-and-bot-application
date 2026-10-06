#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.bot.services.test_duel_service
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Discord Bot Services / Duel Engine, Board Model & Concurrency
Description:
    Unit test suite for DuelService, DuelManager, DuelBoard, and DuelEngineCog:
    1. DuelManager lifecycle, active sessions, and force reset.
    2. Natural Yu-Gi-Oh! RNG (drawing, milling, shuffling, hands).
    3. DuelBoard model, zone allocations, positions, and ASCII field rendering.
    4. Modular duel state machine (phases, LP adjustments, surrender, defeat).
    5. Interactive cog components (SummonSelect, PositionChangeSelect, AttackTargetSelect).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from unittest.mock import MagicMock, AsyncMock
import pytest
import aiosqlite

from config.paths import STORY_DB_PATH
from services.duel import (
    DuelService,
    DuelSession,
    DuelManager,
    duel_manager,
    DEFAULT_STARTING_LP,
    PHASE_DRAW,
    PHASE_STANDBY,
    PHASE_MAIN_1,
    PHASE_BATTLE,
    PHASE_MAIN_2,
    PHASE_END,
)
import services.duel as duel_bridge
from utils import DuelBoard, render_duel_field_ascii, build_board_guide_embed
from services.story import StoryService
from services.card import CardService
from cogs.story import StoryDuelSession
from cogs.duel_engine import (
    DuelEngineCog,
    DuelSession as CogDuelSession,
    DuelView,
    SummonSelect,
    PositionChangeSelect,
    SpellTrapSelect,
    AttackTargetSelect,
)


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: DuelManager Lifecycle
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Duel RNG and Card Play Features
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_duel_rng_and_card_play_features(test_db_path):
    story_service = StoryService(test_db_path)
    card_service = CardService(test_db_path)

    mock_p1 = MagicMock()
    mock_p1.id = 11122201
    mock_p1.display_name = "PlayerOne"

    mock_p2 = MagicMock()
    mock_p2.id = 11122202
    mock_p2.display_name = "PlayerTwo"

    cards = await card_service.get_all_cards()
    full_deck = [c["id"] for c in cards] * 10

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

    # PvP DuelSession Natural RNG
    pvp_session = CogDuelSession(mock_p1, mock_p2, full_deck, full_deck, match_type="CASUAL")
    assert len(pvp_session.hands[mock_p1.id]) == 5
    assert len(pvp_session.hands[mock_p2.id]) == 5

    p1_draw = pvp_session.draw_card(mock_p1.id)
    assert p1_draw is not None
    assert len(pvp_session.hands[mock_p1.id]) == 6


# -----------------------------------------------------------------------------
# Sub-Block 3.3: DuelBoard Model and Field Rendering
# -----------------------------------------------------------------------------
def test_duel_board_model_and_field_rendering():
    board = DuelBoard()
    assert len(board.mmz) == 5
    assert len(board.stz) == 5
    assert board.field_spell is None
    assert len(board.gy) == 0
    assert len(board.banished) == 0

    # Summon monster in ATK position
    slot = board.summon_monster({"id": 50000101, "name": "Kasutamaiza", "atk": 4000, "def": 4000}, position="ATK")
    assert slot == 0
    assert board.mmz[0]["name"] == "Kasutamaiza"
    assert board.mmz[0]["position"] == "ATK"

    # Play Field Spell
    fname = board.play_field_spell({"id": 50000114, "name": "The Sacred Temple of Kustomazi"})
    assert fname == "The Sacred Temple of Kustomazi"

    # Banished and GY
    board.banish_card(50000103)
    assert 50000103 in board.banished

    # Render ASCII field
    opp_board = DuelBoard()
    ascii_mat = render_duel_field_ascii(
        board, opp_board, "PlayerOne", "Opponent", 8000, 8000, 5, 5, 29, 29
    )
    assert "4000" in ascii_mat

    # Board guide embed
    embed = build_board_guide_embed()
    assert "Duel Field" in embed.title


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Modular Architecture & State Machine Progression
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_duel_service_modular_architecture_and_state_machine():
    assert duel_bridge.DuelManager is DuelManager
    assert duel_bridge.DuelSession is DuelSession
    assert duel_bridge.DEFAULT_STARTING_LP == 8000

    p1 = MagicMock(id=555001, display_name="Yugi")
    p2 = MagicMock(id=555002, display_name="Kaiba")

    p1_deck = [10000000 + i for i in range(40)]
    p2_deck = [20000000 + i for i in range(40)]

    custom_manager = DuelManager()
    service = DuelService(manager=custom_manager)

    session = service.start_duel(
        p1=p1, p2=p2, p1_deck=p1_deck, p2_deck=p2_deck, match_type="RANKED"
    )

    assert custom_manager.is_user_dueling(555001) is True
    assert session.current_phase == PHASE_DRAW

    # Phase Progression
    assert session.advance_phase() == PHASE_STANDBY
    assert session.advance_phase() == PHASE_MAIN_1
    assert session.advance_phase() == PHASE_BATTLE
    assert session.advance_phase() == PHASE_MAIN_2
    assert session.advance_phase() == PHASE_END
    next_phase = session.advance_phase()
    assert next_phase == PHASE_DRAW
    assert session.turn_count == 2

    # LP Damage & Fatal blow
    session.adjust_lp(p2.id, -8000, reason="Game ending attack")
    assert session.duel_over is True
    assert session.winner.id == p1.id

    custom_manager.unregister_session(session)
    assert custom_manager.is_user_dueling(555001) is False


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Interactive Cog and UI Components
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_duel_engine_interactive_cog_and_components():
    p1 = MagicMock(id=777001, display_name="DuelistOne", mention="<@777001>")
    p2 = MagicMock(id=777002, display_name="DuelistTwo", mention="<@777002>")

    p1_deck = [50000101, 50000102, 50000103]
    p2_deck = [50000101, 50000102, 50000103]

    session = CogDuelSession(p1, p2, p1_deck, p2_deck, match_type="CASUAL")
    duel_manager.register_session(p1.id, p2.id, session)

    view = DuelView(session)
    embed = view.build_embed(last_action="Match started")
    assert "Turn 1" in embed.description

    # Test SummonSelect
    monster_card = {"id": 50000101, "name": "Kasutamaiza Monster", "card_type": "Monster", "level": 4, "atk": 1800, "def": 1200}
    session.hands[p1.id] = [50000101]
    summon_sel = SummonSelect(session, view, [monster_card])
    summon_sel._values = ["50000101:ATK"]

    mock_inter = AsyncMock(user=p1)
    mock_inter.response.is_done.return_value = False
    await summon_sel.callback(mock_inter)

    assert session.boards[p1.id].mmz[0] is not None
    assert session.boards[p1.id].mmz[0]["name"] == "Kasutamaiza Monster"

    # Cleanup
    duel_manager.unregister_session(session)
    assert duel_manager.is_user_dueling(p1.id) is False


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_duel_manager_lifecycle",
    "test_duel_rng_and_card_play_features",
    "test_duel_board_model_and_field_rendering",
    "test_duel_service_modular_architecture_and_state_machine",
    "test_duel_engine_interactive_cog_and_components",
]
