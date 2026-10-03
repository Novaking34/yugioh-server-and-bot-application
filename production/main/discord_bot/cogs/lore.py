#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Lore, Story Sagas & Server Statistics
=============================================================================
Allows community members to explore worldbuilding sagas, faction playstyles,
duelist dossiers, character deck breakdowns, and live card database metrics.
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import os
from typing import Optional, List

from bot_config import BOT_CONFIG


async def lore_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """
    Real-time autocomplete for lore searches across sagas, factions, and characters.
    """
    db_path = BOT_CONFIG["db_path"]
    choices = []
    async with aiosqlite.connect(db_path) as db:
        # Arcs
        cur = await db.execute("SELECT title FROM lore_arcs WHERE title LIKE ? LIMIT 5", (f"%{current}%",))
        for row in await cur.fetchall():
            choices.append(app_commands.Choice(name=f"🌌 Saga: {row[0]}", value=row[0]))

        # Factions
        cur = await db.execute("SELECT name FROM factions WHERE name LIKE ? LIMIT 5", (f"%{current}%",))
        for row in await cur.fetchall():
            choices.append(app_commands.Choice(name=f"⚔️ Faction: {row[0]}", value=row[0]))

        # Characters
        cur = await db.execute("SELECT name, alias FROM characters WHERE name LIKE ? OR alias LIKE ? LIMIT 5", (f"%{current}%", f"%{current}%"))
        for row in await cur.fetchall():
            alias_str = f" ({row[1]})" if row[1] else ""
            choices.append(app_commands.Choice(name=f"👤 Duelist: {row[0]}{alias_str}", value=row[0]))

    return choices[:25]


async def deck_name_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """
    Real-time autocomplete for registered story deck profiles.
    """
    db_path = BOT_CONFIG["db_path"]
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("""
            SELECT d.name, c.name FROM decks d
            LEFT JOIN characters c ON d.character_id = c.id
            WHERE d.name LIKE ? OR c.name LIKE ?
            LIMIT 15
        """, (f"%{current}%", f"%{current}%"))
        rows = await cur.fetchall()
        choices = []
        for dname, cname in rows:
            duelist = cname or "Story Duelist"
            label = f"{dname} ({duelist})"
            if len(label) > 100:
                label = label[:97] + "..."
            choices.append(app_commands.Choice(name=label, value=dname))
        return choices


class LoreCog(commands.Cog, name="Lore"):
    """Commands for exploring story lore, character sagas, and platform stats."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = BOT_CONFIG["db_path"]

    @app_commands.command(name="lore", description="Read world lore, saga chronicles, or duelist dossiers")
    @app_commands.autocomplete(query=lore_autocomplete)
    @app_commands.describe(query="Name of a saga, faction, or character")
    async def lore_command(self, interaction: discord.Interaction, query: str):
        """Searches across lore arcs, factions, and characters."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # 1. Search Lore Arcs
            cur = await db.execute("SELECT * FROM lore_arcs WHERE title LIKE ? LIMIT 1", (f"%{query}%",))
            arc = await cur.fetchone()
            if arc:
                embed = discord.Embed(
                    title=f"🌌 Saga Chronicle: {arc['title']}",
                    description=arc["synopsis"],
                    color=0x4A90E2
                )
                embed.add_field(name="Timeline / Era", value=arc["era_or_season"] or "Era of Creation", inline=True)
                await interaction.response.send_message(embed=embed)
                return

            # 2. Search Factions
            cur = await db.execute("""
                SELECT f.*, a.title AS arc_title 
                FROM factions f 
                LEFT JOIN lore_arcs a ON f.arc_id = a.id 
                WHERE f.name LIKE ? LIMIT 1
            """, (f"%{query}%",))
            faction = await cur.fetchone()
            if faction:
                embed = discord.Embed(
                    title=f"⚔️ Faction Overview: {faction['name']}",
                    description=faction["lore_description"],
                    color=0xE67E22
                )
                embed.add_field(name="Playstyle Dynamics", value=faction["playstyle_overview"] or "Divine Summoning & Continuous World Shaping", inline=False)
                if faction["arc_title"]:
                    embed.add_field(name="Active Saga", value=faction["arc_title"], inline=True)
                await interaction.response.send_message(embed=embed)
                return

            # 3. Search Characters
            cur = await db.execute("""
                SELECT c.*, f.name AS faction_name, a.title AS arc_title 
                FROM characters c 
                LEFT JOIN factions f ON c.faction_id = f.id 
                LEFT JOIN lore_arcs a ON c.arc_id = a.id 
                WHERE c.name LIKE ? OR c.alias LIKE ? LIMIT 1
            """, (f"%{query}%", f"%{query}%"))
            char = await cur.fetchone()
            if char:
                embed = discord.Embed(
                    title=f"👤 Duelist Dossier: {char['name']}",
                    description=char["bio"],
                    color=0x9B59B6
                )
                if char["alias"]:
                    embed.add_field(name="Title / Alias", value=char["alias"], inline=True)
                if char["faction_name"]:
                    embed.add_field(name="Faction", value=char["faction_name"], inline=True)
                if char["arc_title"]:
                    embed.add_field(name="Saga", value=char["arc_title"], inline=True)
                if char["avatar_url"]:
                    embed.set_thumbnail(url=char["avatar_url"])
                await interaction.response.send_message(embed=embed)
                return

        await interaction.response.send_message(
            f"❓ No lore records found matching **'{query}'**.",
            ephemeral=True
        )

    @app_commands.command(name="deck", description="Inspect a story character's pre-constructed deck profile")
    @app_commands.autocomplete(name=deck_name_autocomplete)
    @app_commands.describe(name="Deck name or character name")
    async def deck_command(self, interaction: discord.Interaction, name: str):
        """Displays breakdown of a character deck."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT d.*, c.name AS character_name 
                FROM decks d 
                LEFT JOIN characters c ON d.character_id = c.id 
                WHERE d.name LIKE ? OR c.name LIKE ? LIMIT 1
            """, (f"%{name}%", f"%{name}%"))
            deck = await cur.fetchone()
            if not deck:
                await interaction.response.send_message(f"❌ Deck matching **'{name}'** not found.", ephemeral=True)
                return

            cur = await db.execute("""
                SELECT dc.quantity, dc.section, cc.set_number, cc.name, cc.card_type, cc.card_subtype
                FROM deck_cards dc
                JOIN custom_cards cc ON dc.card_id = cc.id
                WHERE dc.deck_id = ?
                ORDER BY dc.section DESC, cc.id ASC
            """, (deck['id'],))
            cards = await cur.fetchall()

        def format_deck_line(c):
            set_tag = f"`{c['set_number']}` " if c['set_number'] else ""
            return f"{c['quantity']}x {set_tag}**{c['name']}** ({c['card_subtype'] or 'Normal'} {c['card_type']})"

        main_list = [format_deck_line(c) for c in cards if c['section'] == 'MAIN']
        extra_list = [format_deck_line(c) for c in cards if c['section'] == 'EXTRA']

        embed = discord.Embed(
            title=f"🎴 {deck['name']}",
            description=deck['description'] or "No deck description recorded.",
            color=0xF39C12
        )
        if deck['character_name']:
            embed.add_field(name="Signature Duelist", value=deck['character_name'], inline=True)
        if deck['duelingbook_deck_url']:
            embed.add_field(name="Duelingbook Deck", value=f"[Open in Builder]({deck['duelingbook_deck_url']})", inline=True)

        if main_list:
            embed.add_field(name=f"Main Deck ({sum(c['quantity'] for c in cards if c['section'] == 'MAIN')} Cards)", value="\n".join(main_list), inline=False)
        if extra_list:
            embed.add_field(name=f"Extra Deck ({sum(c['quantity'] for c in cards if c['section'] == 'EXTRA')} Cards)", value="\n".join(extra_list), inline=False)

        embed.set_footer(text="Load this deck into your active profile using /load_character_deck")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View custom card database and simulator platform metrics")
    async def stats_command(self, interaction: discord.Interaction):
        """Displays global card counts, factions, players, and duel records."""
        async with aiosqlite.connect(self.db_path) as db:
            c_cards = (await (await db.execute("SELECT COUNT(*) FROM custom_cards")).fetchone())[0]
            c_factions = (await (await db.execute("SELECT COUNT(*) FROM factions")).fetchone())[0]
            c_chars = (await (await db.execute("SELECT COUNT(*) FROM characters")).fetchone())[0]
            c_decks = (await (await db.execute("SELECT COUNT(*) FROM decks")).fetchone())[0]
            c_duels = (await (await db.execute("SELECT COUNT(*) FROM duel_logs")).fetchone())[0]
            c_pdecks = (await (await db.execute("SELECT COUNT(DISTINCT user_id) FROM player_decks")).fetchone())[0]

        db_size_kb = os.path.getsize(self.db_path) / 1024 if os.path.exists(self.db_path) else 0

        embed = discord.Embed(title="📊 The Land of Kustomazi — Platform Stats", color=0x2ECC71)
        embed.add_field(name="🃏 Set 1 Cards (TLOK)", value=f"**{c_cards}** Cards", inline=True)
        embed.add_field(name="⚔️ Factions", value=f"**{c_factions}** Factions", inline=True)
        embed.add_field(name="👤 Story Duelists", value=f"**{c_chars}** Duelists", inline=True)
        embed.add_field(name="👥 Active Duelists", value=f"**{c_pdecks}** Players", inline=True)
        embed.add_field(name="📜 Pre-Made Decks", value=f"**{c_decks}** Decks", inline=True)
        embed.add_field(name="💾 Database Size", value=f"**{db_size_kb:.1f}** KB", inline=True)
        embed.add_field(name="⚔️ Story Duels Logged", value=f"**{c_duels}** Duels", inline=True)
        embed.set_footer(text="Live Duel Simulator on Port 7911 • Web Catalog on Port 8000 / thelandofkustomazi.com")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(LoreCog(bot))

