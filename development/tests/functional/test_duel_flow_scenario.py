#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.functional.test_duel_flow_scenario
Architecture: Hybrid Systems Engineering (Functional Testing Subsystem)
Domain: End-to-End Duel Simulation / Match Lifecycle & ELO Resolution
Description:
    Functional test suite simulating a complete multi-step duel between two players:
    1. Match initialization and deck validation.
    2. Turn execution: Draw, Main Phase summon, Battle Phase direct attack.
    3. Match conclusion upon LP reduction to 0.
    4. Rating update, match logging, and session cleanup.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from unittest.mock import MagicMock
import pytest

from services.duel import DuelService, DuelManager
from services.rating import RatingService
from config.paths import STORY_DB_PATH


# =============================================================================
# BLOCK 3: BODY BLOCK (Functional Scenarios)
# =============================================================================

@pytest.mark.anyio
async def test_complete_ranked_duel_scenario(test_db_path):
    """Executes a full functional ranked duel from challenge to ELO recording."""
    manager = DuelManager()
    duel_svc = DuelService(manager=manager)
    rating_svc = RatingService(test_db_path)

    p1 = MagicMock(id=991001, display_name="AlphaDuelist")
    p2 = MagicMock(id=991002, display_name="BetaDuelist")

    # 40-card decks
    p1_deck = [50000101] * 20 + [50000102] * 20
    p2_deck = [50000103] * 20 + [50000107] * 20

    # 1. Start Ranked Match
    session = duel_svc.start_duel(
        p1=p1, p2=p2, p1_deck=p1_deck, p2_deck=p2_deck,
        match_type="RANKED", p1_deck_name="Alpha Deck", p2_deck_name="Beta Deck"
    )
    assert manager.is_user_dueling(p1.id) is True
    assert manager.is_user_dueling(p2.id) is True

    # 2. Turn 1: Advance phases
    assert session.turn_count == 1
    session.advance_phase() # to Standby
    session.advance_phase() # to Main 1

    # Summon monster for P1
    session.boards[p1.id].summon_monster(
        {"id": 50000101, "name": "The Great Kasutamaiza", "atk": 8000, "def": 4000},
        position="ATK"
    )
    assert session.boards[p1.id].mmz[0] is not None

    # 3. Battle Phase & Direct Attack
    session.advance_phase() # to Battle
    old_lp, new_lp, is_concluded = session.adjust_lp(p2.id, -8000, reason="Game ending strike")
    assert new_lp == 0
    assert is_concluded is True
    assert session.duel_over is True

    # 4. Record result in RatingService
    match_record = await rating_svc.record_duel_match(
        p1_id=str(p1.id),
        p2_id=str(p2.id),
        winner_id=str(p1.id),
        match_type="RANKED",
        turns=1,
        p1_deck=p1_deck,
        p2_deck=p2_deck,
        p1_deck_name="Alpha Deck",
        p2_deck_name="Beta Deck",
        p1_name="AlphaDuelist",
        p2_name="BetaDuelist"
    )
    assert match_record["winner_id"] == str(p1.id)
    assert match_record["p1_elo_delta"] > 0
    assert match_record["p2_elo_delta"] < 0

    # 5. Clean up session
    manager.unregister_session(session)
    assert manager.is_user_dueling(p1.id) is False
    assert manager.is_user_dueling(p2.id) is False


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = ["test_complete_ranked_duel_scenario"]
