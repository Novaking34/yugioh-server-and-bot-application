#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Custom Cardpool, Search & Telemetry
=============================================================================
Provides slash commands and interactive autocompletion for querying custom cards
registered in the Story Database. Displays Duelingbook artwork, stats, lore,
and live card usage telemetry.
Includes:
- /card <name>: Full Duelingbook artwork, stats, and lore card inspection
- /cardpool: Complete overview of Set 1: The Land of Kustomazi
- /card_stats <name>: Real-time card inclusion rate, win rate, and dueling stats
- /meta: Top most popular and most victorious custom cards
- /random_card: Random card spotlight from the active cardpool
- /recent_cards: Chronological list of registered custom cards
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

from services.card_service import CardService
from utils import build_card_embed, build_card_stats_embed, build_card_types_guide_embed
from production.main.logger import get_logger

logger = get_logger("discord_bot.cogs.cardpool")

# Shared card service instance for autocomplete
_card_service = CardService()


async def card_name_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """
    Real-time autocomplete handler fetching matching card names and set numbers.
    Returns up to 20 matching choices with set numbers.
    """
    matches = await _card_service.search_cards(current, limit=20)
    choices = []
    for m in matches:
        cid = m["id"]
        set_num = m["set_number"]
        name = m["name"]
        label = m.get("autocomplete_label") or (f"{set_num} | {name}" if set_num else f"[{cid}] {name}")
        if len(label) > 100:
            label = label[:97] + "..."
        choices.append(app_commands.Choice(name=label, value=name))
    return choices


class CardpoolCog(commands.Cog, name="Cardpool"):
    """Commands for searching and inspecting custom cards in the live pool."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.card_service = _card_service

    @app_commands.command(name="card", description="Search custom card pool with Duelingbook artwork, stats, and lore")
    @app_commands.autocomplete(name=card_name_autocomplete)
    @app_commands.describe(name="Name, Set Number (e.g. TLOK-001), or Passcode of the card")
    async def card_command(self, interaction: discord.Interaction, name: str):
        """Displays rich card details for the queried card name, set number, or ID."""
        card = await self.card_service.get_card_by_query(name)
        if not card:
            await interaction.response.send_message(
                f"❌ Card **'{name}'** not found in the custom card pool.",
                ephemeral=True
            )
            return

        embed = build_card_embed(card)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="card_stats", description="View live usage telemetry, deck inclusion, and win rate for a card")
    @app_commands.autocomplete(name=card_name_autocomplete)
    @app_commands.describe(name="Name or Set Number of the custom card")
    async def card_stats_command(self, interaction: discord.Interaction, name: str):
        """Displays telemetry metrics (times decked, drawn, played, win rate)."""
        card = await self.card_service.get_card_by_query(name)
        if not card:
            await interaction.response.send_message(f"❌ Card **'{name}'** not found.", ephemeral=True)
            return

        stats = await self.card_service.get_card_usage_stats(card["id"])
        embed = build_card_stats_embed(stats)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="meta", description="Overview of top custom cards by popularity and duel win rate")
    async def meta_command(self, interaction: discord.Interaction):
        """Displays meta tier telemetry across player decks and duels."""
        meta = await self.card_service.get_meta_overview(limit=5)
        embed = discord.Embed(
            title="📊 The Land of Kustomazi — Set 1 Meta Telemetry",
            description="Live statistics derived from player decks and live Discord duels.",
            color=0x3B82F6
        )

        pop_lines = []
        for c in meta.get("most_popular", []):
            set_str = f"[{c['set_number']}] " if c.get("set_number") else ""
            pop_lines.append(f"• **{set_str}{c['name']}**: In **{c['times_decked']}** deck(s) | Played **{c['times_played']}**x")

        embed.add_field(
            name="🔥 Most Popular in Decks",
            value="\n".join(pop_lines) if pop_lines else "*No deck data recorded yet.*",
            inline=False
        )

        win_lines = []
        for c in meta.get("most_victorious", []):
            set_str = f"[{c['set_number']}] " if c.get("set_number") else ""
            total = c["wins"] + c["losses"]
            wr = round((c["wins"] / total * 100), 1) if total > 0 else 0.0
            win_lines.append(f"• **{set_str}{c['name']}**: **{c['wins']} Wins** ({wr}% WR)")

        embed.add_field(
            name="🏆 Most Victorious in Matchups",
            value="\n".join(win_lines) if win_lines else "*No match telemetry recorded yet.*",
            inline=False
        )

        embed.set_footer(text="Play in /duel or add cards in /deck_add to influence meta telemetry!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cardpool", description="Browse all cards in Set 1: The Land of Kustomazi grouped by type")
    async def cardpool_command(self, interaction: discord.Interaction):
        """Displays complete Set 1 card catalog organized by Monsters, Spells, and Traps."""
        cards = await self.card_service.get_all_cards()
        if not cards:
            await interaction.response.send_message("❌ No cards currently registered in the database.", ephemeral=True)
            return

        monsters = [c for c in cards if c["card_type"] == "Monster"]
        spells = [c for c in cards if c["card_type"] == "Spell"]
        traps = [c for c in cards if c["card_type"] == "Trap"]

        embed = discord.Embed(
            title="🌌 The Land of Kustomazi — Set 1 Cardpool",
            description=(
                f"**Total Registered Cards:** {len(cards)}\n"
                f"All cards are live in the EDOPro simulator and compiled into `custom_cards.cdb`.\n"
                f"View the web catalog at `http://thelandofkustomazi.com` or local port `8000`."
            ),
            color=0xF59E0B
        )

        def format_card_line(c):
            set_str = f"`{c['set_number']}`" if c['set_number'] else f"`{c['id']}`"
            if c['card_type'] == 'Monster':
                def_str = 'LINK' if c['card_subtype'] and 'link' in c['card_subtype'].lower() else (c['def'] if c['def'] is not None else 0)
                return f"{set_str} **{c['name']}** [{c['attribute']} | {c['card_subtype']}] — ATK {c['atk']} / DEF {def_str}"
            else:
                return f"{set_str} **{c['name']}** [{c['card_subtype']} {c['card_type']}]"

        if monsters:
            lines = [format_card_line(m) for m in monsters]
            embed.add_field(name=f"⚔️ Monster Cards ({len(monsters)})", value="\n".join(lines), inline=False)

        if spells:
            lines = [format_card_line(s) for s in spells]
            embed.add_field(name=f"✨ Spell Cards ({len(spells)})", value="\n".join(lines), inline=False)

        if traps:
            lines = [format_card_line(t) for t in traps]
            embed.add_field(name=f"🛡️ Trap Cards ({len(traps)})", value="\n".join(lines), inline=False)

        embed.set_footer(text="Use /card <name> to view complete card artwork, stats, and effects!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="random_card", description="Spotlight a random custom card from the active pool")
    async def random_card_command(self, interaction: discord.Interaction):
        """Picks a random card from the database and showcases its full embed."""
        card = await self.card_service.get_random_card()
        if not card:
            await interaction.response.send_message("❌ Card pool is currently empty.", ephemeral=True)
            return

        embed = build_card_embed(card)
        await interaction.response.send_message(
            content="🌟 **Card Spotlight — Random Discovery:**",
            embed=embed
        )

    @app_commands.command(name="recent_cards", description="View custom cards in the pool")
    @app_commands.describe(limit="Number of cards to display (1 to 14)")
    async def recent_cards_command(self, interaction: discord.Interaction, limit: Optional[int] = 10):
        """Lists registered custom cards in descending order."""
        card_limit = min(max(1, limit or 10), 14)
        cards = await self.card_service.get_recent_cards(limit=card_limit)

        embed = discord.Embed(
            title=f"🆕 Custom Card Pool ({len(cards)} Cards Displayed)",
            description="These cards are live in the cardpool and ready for duels in the live simulator!",
            color=0x3498DB
        )

        for c in cards:
            stats = f"{c['card_subtype'] or 'Normal'} {c['card_type']}"
            if c['card_type'] == 'Monster':
                def_str = c['def'] if c['def'] is not None else 'LINK'
                stats += f" | {c['attribute']} | ATK {c['atk']}/{def_str}"
            creator = c.get('creator_name') or 'ProfessorSeanEX'
            set_code = c['set_number'] or f"ID:{c['id']}"
            embed.add_field(
                name=f"[{set_code}] {c['name']} ({c['rarity'] or 'Common'})",
                value=f"{stats}\n*Designed by {creator}*",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="card_types", description="Guide to Monster/Spell/Trap types, speeds, 26 races, 7 attributes, and Levels/Ranks")
    @app_commands.describe(category="Category to view: overview, spells, traps, monsters, races, attributes, levels_ranks")
    @app_commands.choices(category=[
        app_commands.Choice(name="🃏 Full Overview", value="overview"),
        app_commands.Choice(name="📗 Spell Cards (6 Types)", value="spells"),
        app_commands.Choice(name="📕 Trap Cards (3 Types)", value="traps"),
        app_commands.Choice(name="📙 Monster Categories & Frames", value="monsters"),
        app_commands.Choice(name="🐉 The 26 Monster Types (Races)", value="races"),
        app_commands.Choice(name="✨ The 7 Elemental Attributes", value="attributes"),
        app_commands.Choice(name="⭐ Levels, Ranks & Scales", value="levels_ranks")
    ])
    async def card_types_command(self, interaction: discord.Interaction, category: Optional[str] = "overview"):
        """Displays rich breakdown of card types, icons, spell speeds, monster races, attributes, and ranks."""
        chosen = category or "overview"
        embed = build_card_types_guide_embed(chosen)
        view = CardTypesView()
        await interaction.response.send_message(embed=embed, view=view)


class CardTypesSelect(discord.ui.Select):
    """Dropdown menu for switching between Spells, Traps, Monsters, Races, Attributes, Levels/Ranks, and Overview."""

    def __init__(self):
        options = [
            discord.SelectOption(label="Full Overview", value="overview", description="Core card types, attributes, levels/ranks summary", emoji="🃏"),
            discord.SelectOption(label="Spell Cards (6 Types)", value="spells", description="Normal, Continuous, Equip, Quick-Play, Field, Ritual", emoji="📗"),
            discord.SelectOption(label="Trap Cards (3 Types)", value="traps", description="Normal, Continuous, and Counter Traps (Speed 3)", emoji="📕"),
            discord.SelectOption(label="Monster Frames & Summons", value="monsters", description="Main Deck vs Extra Deck frames and sub-mechanics", emoji="📙"),
            discord.SelectOption(label="26 Monster Types (Races)", value="races", description="All 26 official monster races/tribes", emoji="🐉"),
            discord.SelectOption(label="7 Elemental Attributes", value="attributes", description="LIGHT, DARK, EARTH, WATER, FIRE, WIND, DIVINE", emoji="✨"),
            discord.SelectOption(label="Levels, Ranks & Scales", value="levels_ranks", description="Level tribute thresholds, Xyz Ranks, and Link/Scale rules", emoji="⭐"),
        ]
        super().__init__(placeholder="Select a card category to inspect...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        embed = build_card_types_guide_embed(selected)
        await interaction.response.edit_message(embed=embed, view=self.view)


class CardTypesView(discord.ui.View):
    """Interactive view holding the category dropdown."""

    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(CardTypesSelect())


async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(CardpoolCog(bot))
