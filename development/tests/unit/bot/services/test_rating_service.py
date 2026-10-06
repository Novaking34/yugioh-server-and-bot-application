#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.bot.services.test_rating_service
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Discord Bot Services / ELO Calculations, Tiers & Leaderboards
Description:
    Unit test suite for RatingService and its underlying mathematical functions:
    1. Mathematical ELO algorithms (equal players, draws, underdogs, K-factor).
    2. Tier classifications, badge mappings, and threshold brackets.
    3. Live match recording and player profile lifecycle.
    4. Leaderboard querying and sorting.
    5. Modular C-style architecture contracts and RankingCog slash commands.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from unittest.mock import MagicMock, AsyncMock
import pytest
import aiosqlite

from config.paths import STORY_DB_PATH
from services.rating import (
    RatingService,
    rating_service,
    TIER_BRACKETS,
    DEFAULT_STARTING_ELO,
    resolve_tier_info,
    compute_elo_change,
    calculate_win_rate,
)
import services.rating as rating_bridge
from cogs.ranking import RankingCog


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Mathematical ELO Calculations & Profile Lifecycle
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_rating_service_elo_calculations(test_db_path):
    service = RatingService(test_db_path)

    # 1. Mathematical Elo Calculation
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
    import uuid
    test_id = uuid.uuid4().hex[:6]
    p1_uid = f"888_{test_id}"
    p2_uid = f"999_{test_id}"
    try:
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
        lb = await service.get_leaderboard(limit=25)
        assert len(lb) >= 1
        assert any(p["user_id"] == p1_uid for p in lb)
    finally:
        async with aiosqlite.connect(service.db_path) as db:
            await db.execute("DELETE FROM player_ratings WHERE user_id IN (?, ?)", (p1_uid, p2_uid))
            await db.execute("DELETE FROM duel_matches WHERE p1_user_id = ? OR p2_user_id = ?", (p1_uid, p2_uid))
            await db.commit()


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Modular Architecture and Subsystem Verification
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_rating_service_modular_architecture_and_subsystem(test_db_path):
    # 1. Structural Parity & Re-export Verification
    assert rating_bridge.RatingService is RatingService
    assert len(TIER_BRACKETS) == 7
    assert DEFAULT_STARTING_ELO == 1200

    # 2. Math Algorithms
    name, badge, color = resolve_tier_info(1950)
    assert name == "Diamond Duelist"
    assert badge == "💠"

    w_elo, l_elo = compute_elo_change(1200, 1200, 1.0)
    assert w_elo > 1200
    assert l_elo < 1200

    wr = calculate_win_rate(10, 5, 0)
    assert wr == 66.7

    # 3. Core Engine Instantiation
    service = RatingService(test_db_path)
    test_uid = "999888777"
    try:
        p_profile = await service.get_or_create_player(test_uid, username="TestDuelist")
        assert p_profile["user_id"] == test_uid
        assert p_profile["elo"] == DEFAULT_STARTING_ELO

        # 4. Cog Commands Inspection
        bot = MagicMock()
        cog = RankingCog(bot)
        assert cog.rank_command is not None
        assert cog.leaderboard_command is not None
        assert cog.rank_tiers_command is not None

        rank_inter = AsyncMock()
        rank_inter.user.id = int(test_uid)
        rank_inter.user.display_name = "TestDuelist"
        await cog.rank_command.callback(cog, rank_inter, user=None, hidden=True)
        rank_inter.response.send_message.assert_called_once()

        tiers_inter = AsyncMock()
        await cog.rank_tiers_command.callback(cog, tiers_inter, hidden=True)
        tiers_inter.response.send_message.assert_called_once()
    finally:
        async with aiosqlite.connect(service.db_path) as db:
            await db.execute("DELETE FROM player_ratings WHERE user_id = ?", (test_uid,))
            await db.commit()


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_rating_service_elo_calculations",
    "test_rating_service_modular_architecture_and_subsystem",
]
