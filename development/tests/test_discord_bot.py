#!/usr/bin/env python3
"""
=============================================================================
Unit & Integration Tests: Discord Bot Formatting, Autocomplete & Live Queries
=============================================================================
Verifies card frame color selection, rich Discord embed generation,
autocomplete query resolution against the canonical Set 1 cardpool,
lore lookups, and player deck management.
=============================================================================
"""

import os
import sys
import pytest
import sqlite3
import discord
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

BOT_DIR = os.path.join(BASE_DIR, "production", "main", "discord_bot")
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config.paths import STORY_DB_PATH
from production.main.discord_bot.utils import (
    FRAME_COLORS, get_card_color, build_card_embed
)
from production.main.discord_bot.cogs.cardpool import card_name_autocomplete
from production.main.discord_bot.cogs.lore import lore_autocomplete, deck_name_autocomplete
from production.main.discord_bot.cogs.deckbuilding import character_deck_autocomplete, user_deck_slot_autocomplete


def test_frame_colors_and_card_color():
    """Validates Yu-Gi-Oh! card frame palette and color assignment rules."""
    required_frames = [
        'normal', 'effect', 'ritual', 'fusion', 'synchro',
        'xyz', 'link', 'spell', 'trap', 'divine'
    ]
    for frame in required_frames:
        assert frame in FRAME_COLORS, f"Missing frame color: {frame}"
        assert isinstance(FRAME_COLORS[frame], int), f"Frame {frame} color must be an integer hex"

    # Spell and Trap rules
    assert get_card_color("Spell", "Normal") == FRAME_COLORS['spell']
    assert get_card_color("Trap", "Continuous") == FRAME_COLORS['trap']

    # Monster summoning mechanics
    assert get_card_color("Monster", "Xyz") == FRAME_COLORS['xyz']
    assert get_card_color("Monster", "Synchro") == FRAME_COLORS['synchro']
    assert get_card_color("Monster", "Fusion") == FRAME_COLORS['fusion']
    assert get_card_color("Monster", "Ritual") == FRAME_COLORS['ritual']
    assert get_card_color("Monster", "Link") == FRAME_COLORS['link']
    assert get_card_color("Monster", "Normal") == FRAME_COLORS['normal']
    assert get_card_color("Monster", "Effect") == FRAME_COLORS['effect']

    # Divine-Beast / DIVINE attribute override
    assert get_card_color("Monster", "Effect", attribute="DIVINE") == FRAME_COLORS['divine']
    assert get_card_color("Monster", "Divine-Beast") == FRAME_COLORS['divine']


def test_build_card_embed_monster():
    """Validates rich Discord embed generation for a Divine-Beast monster."""
    card = {
        "id": 50000101,
        "set_number": "TLOK-001",
        "name": "Kasutamaiza, the Creator of Kustomazi",
        "card_type": "Monster",
        "card_subtype": "Effect",
        "attribute": "DIVINE",
        "monster_type": "Divine-Beast",
        "level_or_rank_or_link": 10,
        "atk": 4000,
        "def": 4000,
        "scale": None,
        "link_arrows": None,
        "effect_text": "Cannot be Special Summoned. Requires 3 Tributes to Normal Summon.",
        "pendulum_effect": None,
        "duelingbook_id": "999999",
        "duelingbook_url": "https://www.duelingbook.com/card?id=999999",
        "image_url": "https://images.duelingbook.com/custom-pics/999999.jpg",
        "creator_name": "ProfessorSeanEX",
        "lore_text": "The prime mover of Kustomazi.",
        "faction_name": "The Creators of Kustomazi",
        "character_name": "ProfessorSeanEX",
        "story_significance": "Supreme Deity",
        "rarity": "Common",
        "archetype": "Kasutamaiza",
        "banlist_status": "Unlimited"
    }

    embed = build_card_embed(card)
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Kasutamaiza, the Creator of Kustomazi [TLOK-001]"
    assert embed.color.value == FRAME_COLORS['divine']
    assert "Common" in embed.description
    assert "Unlimited" in embed.description
    assert "Kasutamaiza" in embed.description

    field_names = [f.name for f in embed.fields]
    assert "⚔️ Monster Parameters" in field_names
    assert "📖 Card Effect" in field_names
    assert "🌌 Story Lore" in field_names

    param_field = next(f for f in embed.fields if f.name == "⚔️ Monster Parameters")
    assert "DIVINE" in param_field.value
    assert "Divine-Beast" in param_field.value
    assert "**Level:** 10" in param_field.value
    assert "**ATK:** 4000 / **DEF:** 4000" in param_field.value

    assert "50000101" in embed.footer.text
    assert "ProfessorSeanEX" in embed.footer.text


def test_build_card_embed_spell():
    """Validates rich Discord embed generation for a Spell card."""
    card = {
        "id": 50000103,
        "set_number": "TLOK-003",
        "name": "The Seed of Creation",
        "card_type": "Spell",
        "card_subtype": "Normal",
        "attribute": None,
        "monster_type": None,
        "level_or_rank_or_link": None,
        "atk": None,
        "def": None,
        "effect_text": "Add 1 'Kasutamaiza' card from your Deck to your hand.",
        "creator_name": "ProfessorSeanEX",
        "rarity": "Common",
        "banlist_status": "Unlimited"
    }

    embed = build_card_embed(card)
    assert embed.color.value == FRAME_COLORS['spell']
    assert embed.title == "The Seed of Creation [TLOK-003]"
    field_names = [f.name for f in embed.fields]
    assert "📜 Card Type" in field_names
    type_field = next(f for f in embed.fields if f.name == "📜 Card Type")
    assert "Normal Spell" in type_field.value


@pytest.mark.anyio
async def test_card_name_autocomplete_live_query():
    """Tests real-time autocompletion against canonical database."""
    interaction_mock = MagicMock()

    # Search by partial card name
    choices = await card_name_autocomplete(interaction_mock, "Kasutamaiza")
    assert len(choices) > 0
    names = [c.value for c in choices]
    assert any("Kasutamaiza" in n for n in names)

    # Search by set number
    choices_set = await card_name_autocomplete(interaction_mock, "TLOK-001")
    assert len(choices_set) > 0
    assert choices_set[0].value == "Kasutamaiza, the Creator of Kustomazi"

    # Search by passcode
    choices_id = await card_name_autocomplete(interaction_mock, "50000101")
    assert len(choices_id) > 0
    assert choices_id[0].value == "Kasutamaiza, the Creator of Kustomazi"


@pytest.mark.anyio
async def test_lore_autocomplete_live_query():
    """Tests real-time lore autocompletion for sagas, factions, and duelists."""
    interaction_mock = MagicMock()

    # Saga search
    choices_saga = await lore_autocomplete(interaction_mock, "Genesis")
    assert any("The Genesis of Kustomazi" in c.value for c in choices_saga)

    # Faction search
    choices_faction = await lore_autocomplete(interaction_mock, "Creators")
    assert any("The Creators of Kustomazi" in c.value for c in choices_faction)

    # Duelist search
    choices_duelist = await lore_autocomplete(interaction_mock, "Professor")
    assert any("ProfessorSeanEX" in c.value for c in choices_duelist)


@pytest.mark.anyio
async def test_deck_autocompletes():
    """Tests deck autocompletion for story deck profiles."""
    interaction_mock = MagicMock()

    choices = await deck_name_autocomplete(interaction_mock, "Kasutamaiza")
    assert len(choices) > 0
    assert "Kasutamaiza - Creation Control" in choices[0].value

    choices_char = await character_deck_autocomplete(interaction_mock, "Professor")
    assert len(choices_char) > 0
    assert any("Kasutamaiza - Creation Control" in c.value for c in choices_char)

    interaction_mock.user.id = 123456789
    slot_choices = await user_deck_slot_autocomplete(interaction_mock, "")
    assert isinstance(slot_choices, list)


def test_all_canonical_cards_generate_valid_embeds():
    """Assures all canonical TLOK cards generate complete, non-failing Discord embeds."""
    conn = sqlite3.connect(STORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, f.name AS faction_name, ch.name AS character_name
        FROM custom_cards c
        LEFT JOIN factions f ON c.faction_id = f.id
        LEFT JOIN characters ch ON c.signature_character_id = ch.id
        ORDER BY c.id ASC
    """)
    cards = cur.fetchall()
    conn.close()

    assert len(cards) == 64, f"Expected exactly 64 TLOK cards in database, found {len(cards)}"

    for c in cards:
        card_dict = dict(c)
        embed = build_card_embed(card_dict)
        assert embed.title is not None
        assert card_dict["name"] in embed.title
        assert card_dict["set_number"] in embed.title
        assert embed.description is not None
        assert embed.color is not None
        assert len(embed.fields) >= 2  # At minimum type/params and effect
