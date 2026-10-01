#!/usr/bin/env python3
"""
=============================================================================
Server Management Tools Cog (Community / Moderation)
=============================================================================
Helpful tools for managing duel communities and discord servers:
- /clear_messages [amount]: Clean up duel chat or bot command spam
- /duel_role: Self-service toggle for @Duelist matchmaking notification role
- /setup_channels: Automatically provisions categorized duel channels
- /coinflip: Fair coinflip with animated embed
- /dice [sides]: Dice roll for duel turn order or card effects
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Optional


class ServerToolsCog(commands.Cog, name="Server Tools"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Flip a coin for turn order or card effects.")
    async def coinflip(self, interaction: discord.Interaction):
        """Simulates a fair coin flip."""
        result = random.choice(["Heads", "Tails"])
        icon = "🪙" if result == "Heads" else "✨"
        color = 0xf59e0b if result == "Heads" else 0x3b82f6

        embed = discord.Embed(
            title=f"{icon} Coin Flip Result",
            description=f"The coin landed on: **{result.upper()}**",
            color=color
        )
        embed.set_footer(text=f"Flipped by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll a die for turn order, effect damage, or random selection.")
    @app_commands.describe(sides="Number of sides on the die (default 6)")
    async def dice(self, interaction: discord.Interaction, sides: Optional[int] = 6):
        """Simulates a dice roll."""
        if sides < 2 or sides > 100:
            await interaction.response.send_message("[-] Please choose between 2 and 100 sides.", ephemeral=True)
            return

        roll = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolled a **d{sides}**: Result is **{roll}**",
            color=0x10b981
        )
        embed.set_footer(text=f"Rolled by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="duel_role", description="Toggle the @Duelist role to receive matchmaking notifications.")
    async def duel_role(self, interaction: discord.Interaction):
        """Allows members to opt-in or opt-out of the @Duelist role."""
        if not interaction.guild:
            await interaction.response.send_message("[-] This command can only be used in a server.", ephemeral=True)
            return

        role_name = "Duelist"
        role = discord.utils.get(interaction.guild.roles, name=role_name)

        if not role:
            # Try to create role if bot has manage_roles
            if interaction.guild.me.guild_permissions.manage_roles:
                try:
                    role = await interaction.guild.create_role(
                        name=role_name,
                        color=discord.Color.from_rgb(139, 92, 246),
                        mentionable=True,
                        reason="Created by Yu-Gi-Oh! bot for matchmaking pings"
                    )
                except Exception as e:
                    await interaction.response.send_message(f"[-] Could not create @Duelist role: {e}", ephemeral=True)
                    return
            else:
                await interaction.response.send_message("[-] '@Duelist' role does not exist and bot lacks permissions to create it.", ephemeral=True)
                return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"[-] Removed **@{role_name}** role. You will no longer receive duel match pings.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"[+] Added **@{role_name}** role! You can now be pinged when players want to duel.", ephemeral=True)

    @app_commands.command(name="clear_messages", description="Clean up recent messages in a duel channel.")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_messages(self, interaction: discord.Interaction, amount: int = 10):
        """Moderation tool: purge chat messages."""
        if amount < 1 or amount > 100:
            await interaction.response.send_message("[-] Please select an amount between 1 and 100.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"[+] Successfully purged **{len(deleted)}** messages.", ephemeral=True)

    @app_commands.command(name="setup_channels", description="Automatically provision categorized duel channels.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def setup_channels(self, interaction: discord.Interaction):
        """Provisions recommended channels for the card game platform."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("[-] Must be used in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # 1. Create Category
            category_name = "⚔️ YU-GI-OH! DUEL ARENA"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(name=category_name)

            channels_to_create = [
                ("duel-chat", "General discussions, rulings, and banter"),
                ("deckbuilder-lab", "Share and test custom decklists"),
                ("card-spoilers", "New card releases and Duelingbook imports"),
                ("bot-commands", "Slash commands and in-chat interactive duels")
            ]

            created = []
            for cname, topic in channels_to_create:
                existing = discord.utils.get(category.text_channels, name=cname)
                if not existing:
                    await guild.create_text_channel(name=cname, category=category, topic=topic)
                    created.append(f"#{cname}")

            if created:
                msg = f"[+] Created category **{category_name}** and channels: {', '.join(created)}"
            else:
                msg = f"[+] All recommended duel channels already exist under **{category_name}**."

            await interaction.followup.send(msg, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"[-] Error setting up channels: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerToolsCog(bot))
