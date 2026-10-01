#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Player Deckbuilding & Deck Management
=============================================================================
Allows Discord users to assemble their own personal decks using registered
custom cards, inspect their active card breakdown, or copy pre-built
story character decks (e.g. Valen Vance or Morgana Vex).
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from typing import Optional

from config import BOT_CONFIG
from cogs.cardpool import card_name_autocomplete


class DeckbuildingCog(commands.Cog, name="Deckbuilding"):
    """Commands for player custom deck construction and inspection."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = BOT_CONFIG["db_path"]

    @app_commands.command(name="deck_add", description="Add a custom card to your personal active deck")
    @app_commands.autocomplete(card_name=card_name_autocomplete)
    @app_commands.describe(card_name="Name of the card", quantity="Copies to add (1 to 3)")
    async def deck_add_command(self, interaction: discord.Interaction, card_name: str, quantity: Optional[int] = 1):
        """Adds 1-3 copies of a custom card to the player's active deck."""
        user_id = str(interaction.user.id)
        qty = min(max(1, quantity or 1), 3)

        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT id, name FROM custom_cards WHERE name = ? LIMIT 1", (card_name,))
            card = await cur.fetchone()
            if not card:
                await interaction.response.send_message(f"❌ Card **'{card_name}'** not found.", ephemeral=True)
                return

            cid, cname = card
            await db.execute("""
                INSERT INTO player_decks (user_id, card_id, quantity) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = MIN(3, quantity + ?)
            """, (user_id, cid, qty, qty))
            await db.commit()

        await interaction.response.send_message(
            f"✅ Added **{qty}x {cname}** to your active deck! Use `/mydeck` to view.",
            ephemeral=True
        )

    @app_commands.command(name="deck_remove", description="Remove a card from your personal active deck")
    @app_commands.autocomplete(card_name=card_name_autocomplete)
    @app_commands.describe(card_name="Name of the card to remove")
    async def deck_remove_command(self, interaction: discord.Interaction, card_name: str):
        """Removes a card completely from the player's deck."""
        user_id = str(interaction.user.id)
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT id, name FROM custom_cards WHERE name = ? LIMIT 1", (card_name,))
            card = await cur.fetchone()
            if not card:
                await interaction.response.send_message("❌ Card not found.", ephemeral=True)
                return

            cid, cname = card
            await db.execute("DELETE FROM player_decks WHERE user_id = ? AND card_id = ?", (user_id, cid))
            await db.commit()

        await interaction.response.send_message(f"🗑️ Removed **{cname}** from your deck.", ephemeral=True)

    @app_commands.command(name="mydeck", description="View your current personal active deck")
    async def mydeck_command(self, interaction: discord.Interaction):
        """Displays the player's current card list categorized by Monster, Spell, and Trap."""
        user_id = str(interaction.user.id)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("""
                SELECT pd.quantity, cc.name, cc.card_type, cc.card_subtype, cc.atk, cc.def
                FROM player_decks pd
                JOIN custom_cards cc ON pd.card_id = cc.id
                WHERE pd.user_id = ?
                ORDER BY cc.card_type DESC, cc.name ASC
            """, (user_id,))
            cards = await cur.fetchall()

        if not cards:
            await interaction.response.send_message(
                "📦 Your deck is empty! Use `/deck_add <card>` or `/load_character_deck` to get started.",
                ephemeral=True
            )
            return

        total_count = sum(c['quantity'] for c in cards)
        monsters = [f"{c['quantity']}x {c['name']} ({c['card_subtype']})" for c in cards if c['card_type'] == 'Monster']
        spells = [f"{c['quantity']}x {c['name']} ({c['card_subtype']})" for c in cards if c['card_type'] == 'Spell']
        traps = [f"{c['quantity']}x {c['name']} ({c['card_subtype']})" for c in cards if c['card_type'] == 'Trap']

        embed = discord.Embed(
            title=f"🃏 {interaction.user.display_name}'s Active Deck ({total_count} Cards)",
            color=0xF1C40F
        )
        if monsters:
            embed.add_field(name=f"⚔️ Monsters ({sum(c['quantity'] for c in cards if c['card_type'] == 'Monster')})", value="\n".join(monsters), inline=False)
        if spells:
            embed.add_field(name=f"✨ Spells ({sum(c['quantity'] for c in cards if c['card_type'] == 'Spell')})", value="\n".join(spells), inline=False)
        if traps:
            embed.add_field(name=f"🛡️ Traps ({sum(c['quantity'] for c in cards if c['card_type'] == 'Trap')})", value="\n".join(traps), inline=False)

        status_text = "✅ Ready for Duels!" if total_count >= 5 else "⚠️ Minimum 5 cards recommended to duel."
        embed.set_footer(text=f"{status_text} • Challenge someone with /duel challenge @user")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="load_character_deck", description="Copy a story character's pre-made deck into your personal deck")
    @app_commands.describe(character="Story duelist name (e.g. Valen Vance or Morgana Vex)")
    async def load_character_deck_command(self, interaction: discord.Interaction, character: str):
        """Loads a story duelist's pre-built deck directly into the user's active deck."""
        user_id = str(interaction.user.id)
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("""
                SELECT d.id, d.name, c.name FROM decks d
                JOIN characters c ON d.character_id = c.id
                WHERE c.name LIKE ? OR d.name LIKE ? LIMIT 1
            """, (f"%{character}%", f"%{character}%"))
            deck = await cur.fetchone()
            if not deck:
                await interaction.response.send_message(
                    f"❌ Character deck matching **'{character}'** not found.",
                    ephemeral=True
                )
                return

            did, dname, cname = deck
            # Clear old deck and load new cards
            await db.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id,))
            cur = await db.execute("SELECT card_id, quantity FROM deck_cards WHERE deck_id = ?", (did,))
            cards = await cur.fetchall()
            for cid, qty in cards:
                await db.execute("INSERT INTO player_decks (user_id, card_id, quantity) VALUES (?, ?, ?)", (user_id, cid, qty))
            await db.commit()

        await interaction.response.send_message(
            f"✨ Loaded **{cname}'s {dname}** into your active deck! Use `/mydeck` to view.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(DeckbuildingCog(bot))
