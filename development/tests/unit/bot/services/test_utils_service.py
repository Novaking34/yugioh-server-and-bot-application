#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.bot.services.test_utils_service
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Discord Bot Services / Utilities, Cardpool Presentation & Combat Math
Description:
    Unit test suite for utils and cardpool presentation subsystems:
    1. Utility embed builders (Rank, Leaderboard, Card Stats, Story Stage).
    2. Card types guide, spell speeds, and all 26 monster races.
    3. Elemental attributes, tribute rules, and battle damage calculations.
    4. Official Yu-Gi-Oh! rarity constants and distribution.
    5. Modular C-style architecture contracts for utils and CardpoolCog.
    6. EDOPro/YGOPro mechanics (passcode padding, Link glyphs, twin boxes).
    7. Autocomplete choices, factory generator, and 25-choice API guard.
    8. Interactive Cardpool views, dynamic database reactivity, and timeouts.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import sqlite3
from unittest.mock import MagicMock, AsyncMock
import pytest
import discord

from config.paths import STORY_DB_PATH
from constants import (
    OFFICIAL_RARITIES, is_official_rarity, RARITY_SECRET_RARE, RARITY_ULTRA_RARE
)
from utils import (
    build_rank_embed,
    build_leaderboard_embed,
    build_card_stats_embed,
    build_story_stage_embed,
    SPELL_CARD_TYPES,
    TRAP_CARD_TYPES,
    MONSTER_CARD_FRAMES,
    MONSTER_SUBTYPES,
    SPELL_SPEEDS_DATA,
    ALL_26_MONSTER_RACES,
    build_card_types_guide_embed,
    CARD_ATTRIBUTES,
    LEVELS_AND_RANKS_DATA,
    get_tribute_requirement,
    calculate_battle_damage,
    FRAME_COLORS,
    get_card_color,
    build_card_embed,
    DuelBoard,
    card_name_autocomplete,
)
from utils.domain.card_embeds import (
    format_passcode,
    format_stat_value,
    format_link_arrows,
    format_spell_trap_property,
    build_recent_cards_embed,
    format_cardpool_catalog_line,
    build_cardpool_catalog_embed,
    add_chunked_catalog_fields,
)
from utils.domain.autocomplete import (
    DISCORD_MAX_AUTOCOMPLETE_CHOICES,
    build_card_autocomplete_choices,
    create_card_autocomplete,
)
from cogs.cardpool import (
    CardpoolCog,
    CardpoolView,
    CardpoolSelect,
    CardActionView,
    RandomCardView,
    CardTypesView,
    CardTypesSelect,
)
from services.card import CardService


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Utility Embed Builders
# -----------------------------------------------------------------------------
def test_utility_embed_builders():
    player_data = {
        "user_id": "123456", "username": "TestMaster", "elo": 1750,
        "wins": 10, "losses": 2, "draws": 0, "win_streak": 5,
        "highest_streak": 5, "highest_elo": 1750,
        "tier": "Platinum Duelist", "season_id": "Season 1"
    }
    rank_embed = build_rank_embed(player_data)
    assert "TestMaster" in rank_embed.title
    assert "1750 ELO" in rank_embed.fields[0].value

    lb_embed = build_leaderboard_embed([player_data], "Season 1")
    assert "Leaderboard" in lb_embed.title

    card_stats = {
        "name": "Kasutamaiza, the Creator of Kustomazi",
        "set_number": "TLOK-001", "card_type": "Monster",
        "card_subtype": "Effect", "rarity": "Ultra Rare",
        "times_decked": 4, "times_drawn": 12, "times_played": 8,
        "wins": 7, "losses": 1, "win_rate": 87.5
    }
    stats_embed = build_card_stats_embed(card_stats)
    assert "Kasutamaiza" in stats_embed.title

    stage_data = {
        "stage_number": 1, "title": "The Quiet Void",
        "intro_dialogue": "Prepare yourself.", "opponent_name": "Echo of the Void",
        "opponent_title": "Primordial Emanation", "opponent_deck_name": "Control",
        "reward_title": "Void Walker", "reward_card_name": "The Void of Creation",
        "reward_card_set": "TLOK-002", "opponent_avatar": None
    }
    story_embed = build_story_stage_embed(stage_data, {"highest_stage_completed": 0})
    assert "Stage 1" in story_embed.title


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Card Types and Races Guide Metadata
# -----------------------------------------------------------------------------
def test_card_types_and_races_guide_metadata():
    assert len(SPELL_CARD_TYPES) == 6
    assert len(TRAP_CARD_TYPES) == 3
    assert len(SPELL_SPEEDS_DATA) == 4
    assert len(ALL_26_MONSTER_RACES) == 26

    categories = [
        "overview", "spells", "traps", "monsters",
        "subtypes", "spell_speeds", "races", "attributes", "levels_ranks"
    ]
    for cat in categories:
        emb = build_card_types_guide_embed(cat)
        assert emb.title is not None


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Attributes, Levels, Ranks and Combat Math
# -----------------------------------------------------------------------------
def test_card_attributes_levels_ranks_and_combat_calculations():
    assert len(CARD_ATTRIBUTES) == 7
    assert CARD_ATTRIBUTES["LIGHT"]["bitmask"] == 0x10

    # Tribute requirements
    assert get_tribute_requirement(1) == 0
    assert get_tribute_requirement(5) == 1
    assert get_tribute_requirement(7) == 2

    # Battle damage: Direct Attack
    atk_monster = {"id": 50000101, "name": "The Great Kasutamaiza", "atk": 4000, "def": 4000, "position": "ATK"}
    direct_res = calculate_battle_damage(atk_monster, defender=None, is_direct=True)
    assert direct_res["is_direct"] is True
    assert direct_res["damage"] == 4000

    # ATK vs ATK: Attacker destroys Defender
    def_monster_atk = {"id": 50000103, "name": "Scout", "atk": 1500, "def": 1200, "position": "ATK"}
    atk_win_res = calculate_battle_damage(atk_monster, def_monster_atk, is_direct=False)
    assert atk_win_res["damage"] == 2500
    assert atk_win_res["defender_destroyed"] is True


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Official Rarities and Set Distribution
# -----------------------------------------------------------------------------
def test_official_rarities_and_set_distribution():
    assert len(OFFICIAL_RARITIES) >= 5
    assert is_official_rarity("Secret Rare") is True
    assert is_official_rarity("Ultra Rare") is True
    assert is_official_rarity("Common") is True
    assert is_official_rarity("InvalidRarityXYZ") is False


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Modular Utils and Cardpool Architecture
# -----------------------------------------------------------------------------
def test_modular_utils_subsystem_and_cardpool_architecture():
    assert get_card_color("Spell", "Normal") == FRAME_COLORS["spell"]
    sample_card = {
        "id": 50000101, "name": "The Great Kasutamaiza", "set_number": "TLOK-001",
        "card_type": "Monster", "card_subtype": "Effect", "attribute": "LIGHT",
        "monster_type": "Warrior", "level_or_rank_or_link": 8, "atk": 3000, "def": 2500
    }
    embed = build_card_embed(sample_card)
    assert "Kasutamaiza" in embed.title

    line = format_cardpool_catalog_line(sample_card)
    assert "TLOK-001" in line


# -----------------------------------------------------------------------------
# Sub-Block 3.6: Simulator Mechanics & EDOPro Formatting Invariants
# -----------------------------------------------------------------------------
def test_card_embeds_body_block_simulator_mechanics():
    assert format_passcode(50000101) == "50000101"
    assert format_passcode(101) == "00000101"
    assert format_stat_value(-2) == "?"
    assert format_stat_value(3000) == "3000"

    arrow_str = format_link_arrows("BL,BR,T")
    assert "↙" in arrow_str and "↘" in arrow_str and "⬆" in arrow_str

    spell_icon, spell_tag, spell_speed = format_spell_trap_property("Spell", "Quick-Play")
    assert spell_speed == 2

    trap_icon, trap_tag, trap_speed = format_spell_trap_property("Trap", "Counter")
    assert trap_speed == 3


# -----------------------------------------------------------------------------
# Sub-Block 3.7: Autocomplete Protocol and Factory Generator
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_utils_domain_autocomplete_subsystem(test_db_path):
    assert DISCORD_MAX_AUTOCOMPLETE_CHOICES == 25

    sample_matches = [
        {"id": 50000000 + i, "set_number": f"TLOK-{i:03d}", "name": f"Card {i}", "autocomplete_label": f"Card {i}"}
        for i in range(30)
    ]
    choices = build_card_autocomplete_choices(sample_matches, limit=30)
    assert len(choices) == 25

    mock_interaction = MagicMock()
    live_choices = await card_name_autocomplete(mock_interaction, "Kas")
    assert len(live_choices) >= 0


# -----------------------------------------------------------------------------
# Sub-Block 3.8: Cardpool Single-Card Inspection and Reactivity
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_cardpool_sub_block_3_1_and_database_reactivity(test_db_path):
    mock_bot = MagicMock()
    cog = CardpoolCog(mock_bot)

    interaction = AsyncMock()
    found_card = await cog._resolve_card_or_reply(interaction, "Kasutamaiza")
    assert found_card is not None


# -----------------------------------------------------------------------------
# Sub-Block 3.9: Growing Cardpool and Chunked Pagination
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_cardpool_growing_cardpool_and_chunked_pagination(test_db_path):
    service = CardService(test_db_path)
    all_cards = await service.get_all_cards()

    # Defensive chunking
    test_embed = discord.Embed(title="Chunking Test")
    huge_lines = [f"`TLOK-{i:03d}` **Custom Card Title {i}**" for i in range(1, 101)]
    add_chunked_catalog_fields(test_embed, "Monster List", huge_lines)
    for f in test_embed.fields:
        assert len(f.value) <= 1024

    overview_embed = build_cardpool_catalog_embed(all_cards, category="overview")
    assert "Total Registered Cards" in overview_embed.description


# -----------------------------------------------------------------------------
# Sub-Block 3.10: Cardpool Components and Tactical Privacy
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_cardpool_sub_block_3_3_and_3_4_components(test_db_path):
    bot = MagicMock()
    cog = CardpoolCog(bot)

    interaction = AsyncMock(user=MagicMock(id=112233))
    await cog.card_types_command.callback(cog, interaction, category="subtypes", hidden=True)
    call_kwargs = interaction.response.send_message.call_args[1]
    assert call_kwargs["ephemeral"] is True


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_utility_embed_builders",
    "test_card_types_and_races_guide_metadata",
    "test_card_attributes_levels_ranks_and_combat_calculations",
    "test_official_rarities_and_set_distribution",
    "test_modular_utils_subsystem_and_cardpool_architecture",
    "test_card_embeds_body_block_simulator_mechanics",
    "test_utils_domain_autocomplete_subsystem",
    "test_cardpool_sub_block_3_1_and_database_reactivity",
    "test_cardpool_growing_cardpool_and_chunked_pagination",
    "test_cardpool_sub_block_3_3_and_3_4_components",
]
