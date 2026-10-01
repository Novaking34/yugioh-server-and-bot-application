#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Custom Cardpool & Search
=============================================================================
Provides slash commands and interactive autocompletion for querying custom cards
registered in the Story Database. Displays Duelingbook artwork, stats, and lore.
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from typing import Optional, List

from config import BOT_CONFIG
from utils import build_card_embed


async def card_name_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """
    Real-time autocomplete handler fetching matching card names from SQLite.
    Returns up to 15 matching choices.
    """
    db_path = BOT_CONFIG["db_path"]
    async with aiosqlite.connect(db_path) as db:
        if current.strip():
            cur = await db.execute(
                "SELECT name FROM custom_cards WHERE name LIKE ? ORDER BY name ASC LIMIT 15",
                (f"%{current}%",)
            )
        else:
            cur = await db.execute(
                "SELECT name FROM custom_cards ORDER BY id DESC LIMIT 15"
            )
        rows = await cur.fetchall()
        return [app_commands.Choice(name=row[0], value=row[0]) for row in rows]


class CardpoolCog(commands.Cog, name="Cardpool"):
    """Commands for searching and inspecting custom cards in the live pool."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = BOT_CONFIG["db_path"]

    @app_commands.command(name="card", description="Search custom card pool with Duelingbook artwork, stats, and lore")
    @app_commands.autocomplete(name=card_name_autocomplete)
    @app_commands.describe(name="Name of the custom card to look up")
    async def card_command(self, interaction: discord.Interaction, name: str):
        """Displays rich card details for the queried card name."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT c.*, f.name AS faction_name, ch.name AS character_name
                FROM custom_cards c
                LEFT JOIN factions f ON c.faction_id = f.id
                LEFT JOIN characters ch ON c.signature_character_id = ch.id
                WHERE c.name = ? OR c.name LIKE ?
                LIMIT 1
            """, (name, f"%{name}%"))
            card = await cur.fetchone()

        if not card:
            await interaction.response.send_message(
                f"❌ Card **'{name}'** not found in the custom card pool.",
                ephemeral=True
            )
            return

        embed = build_card_embed(dict(card))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="recent_cards", description="View the most recently added custom cards in the pool")
    @app_commands.describe(limit="Number of cards to display (1 to 10)")
    async def recent_cards_command(self, interaction: discord.Interaction, limit: Optional[int] = 5):
        """Lists recently registered or imported custom cards."""
        card_limit = min(max(1, limit or 5), 10)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT id, name, card_type, card_subtype, attribute, atk, def, creator_name
                FROM custom_cards
                ORDER BY id DESC
                LIMIT ?
            """, (card_limit,))
            cards = await cur.fetchall()

        embed = discord.Embed(
            title=f"🆕 Recently Added Custom Cards ({len(cards)})",
            description="These cards are live in the cardpool and ready for duels in the live simulator!",
            color=0x3498DB
        )

        for c in cards:
            stats = f"{c['card_subtype'] or 'Normal'} {c['card_type']}"
            if c['card_type'] == 'Monster':
                def_str = c['def'] if c['def'] is not None else 'LINK'
                stats += f" | {c['attribute']} | ATK {c['atk']}/{def_str}"
            creator = c['creator_name'] or 'Anonymous'
            embed.add_field(
                name=f"[{c['id']}] {c['name']}",
                value=f"{stats}\n*Designed by {creator}*",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(CardpoolCog(bot))
