#!/usr/bin/env python3
"""
=============================================================================
General Utilities Cog (Public / Player)
=============================================================================
Provides everyday helpful commands for all server members:
- /ping: Bot & database latency check
- /help: Interactive categorized command directory
- /info: Platform statistics & simulator connection info
- /server_status: Live connectivity check for duel simulator & web catalog
- /rules: Yu-Gi-Oh! duel format and custom card rules
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import time
import socket
import aiosqlite
import os

from bot_config import BOT_CONFIG


class GeneralCog(commands.Cog, name="General"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = BOT_CONFIG["db_path"]

    @app_commands.command(name="ping", description="Check bot latency and database connection speed.")
    async def ping(self, interaction: discord.Interaction):
        """Measures Discord WebSocket latency and database query latency."""
        start_time = time.perf_counter()
        await interaction.response.defer()

        # Database latency measurement
        db_start = time.perf_counter()
        db_ok = False
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("SELECT 1")
            db_ok = True
        except Exception:
            db_ok = False
        db_latency = (time.perf_counter() - db_start) * 1000

        bot_latency = round(self.bot.latency * 1000, 1)
        total_latency = (time.perf_counter() - start_time) * 1000

        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x58a6ff
        )
        embed.add_field(name="Gateway Latency", value=f"`{bot_latency} ms`", inline=True)
        embed.add_field(name="Database Roundtrip", value=f"`{db_latency:.1f} ms` {'✅' if db_ok else '❌'}", inline=True)
        embed.add_field(name="Interaction Latency", value=f"`{total_latency:.1f} ms`", inline=True)
        embed.set_footer(text="Yu-Gi-Oh! Story & Duel Simulator Platform")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="info", description="Platform overview, connection details, and card counts.")
    async def info(self, interaction: discord.Interaction):
        """Displays platform info and game connection instructions."""
        card_count = 0
        min_set = "TLOK-001"
        max_set = "TLOK-064"
        factions_count = 0
        decks_count = 0

        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*), MIN(set_number), MAX(set_number) FROM custom_cards") as cur:
                    row = await cur.fetchone()
                    if row:
                        card_count = row[0]
                        if row[1]:
                            min_set = row[1]
                        if row[2]:
                            max_set = row[2]
                async with db.execute("SELECT COUNT(*) FROM factions") as cur:
                    factions_count = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM decks") as cur:
                    decks_count = (await cur.fetchone())[0]
        except Exception:
            pass

        sim_host = os.getenv("SIMULATOR_HOST", "localhost")
        sim_port = os.getenv("SIMULATOR_PORT", "7911")
        web_port = os.getenv("WEB_PORT", "8000")

        embed = discord.Embed(
            title="🌌 The Land of Kustomazi — Platform Overview",
            description=(
                "Official Discord bot, web catalog, and live EDOPro duel simulator platform for "
                "**The Land of Kustomazi (Set 1)**, designed and architected by **ProfessorSeanEX**."
            ),
            color=0x8b5cf6
        )
        embed.add_field(name="🃏 Live Cardpool", value=f"**{card_count}** Cards (`{min_set}` - `{max_set}`)", inline=True)
        embed.add_field(name="🏛️ Lore Factions", value=f"**{factions_count}** Factions", inline=True)
        embed.add_field(name="📦 Official Decks", value=f"**{decks_count}** Decks", inline=True)

        embed.add_field(
            name="🎮 Live Duel Simulator Connection",
            value=(
                f"• **Client:** EDOPro / Project Ignis\n"
                f"• **Host / IP:** `{sim_host}`\n"
                f"• **TCP Port:** `{sim_port}`\n"
                f"• **Web Room Manager:** `http://{sim_host}:7922`"
            ),
            inline=False
        )
        embed.add_field(
            name="🌐 Web Catalog & Lore Dashboard",
            value=f"• **Public Web:** `http://thelandofkustomazi.com`\n• **Direct Access:** `http://{sim_host}:{web_port}`",
            inline=False
        )
        embed.set_footer(text="Type /help for all available slash commands • /cardpool to view Set 1")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server_status", description="Live health check of the duel simulator and web services.")
    async def server_status(self, interaction: discord.Interaction):
        """Checks TCP connectivity of the simulator and web catalog."""
        await interaction.response.defer()

        sim_host = os.getenv("SIMULATOR_HOST", "127.0.0.1")
        sim_port = int(os.getenv("SIMULATOR_PORT", "7911"))
        web_port = int(os.getenv("WEB_PORT", "8000"))

        def check_port(host: str, port: int, timeout: float = 1.5) -> bool:
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except Exception:
                return False

        sim_online = check_port(sim_host, sim_port)
        web_online = check_port(sim_host, web_port)

        embed = discord.Embed(
            title="📡 Live Service Health Check",
            color=0x238636 if (sim_online and web_online) else 0xd29922
        )
        embed.add_field(
            name="🎮 Live Duel Simulator (TCP 7911)",
            value="🟢 **Online & Accepting Duels**" if sim_online else "🔴 **Offline / Not Started**",
            inline=False
        )
        embed.add_field(
            name="🌐 Web Catalog Dashboard (Port 8000 / thelandofkustomazi.com)",
            value="🟢 **Online & Accessible**" if web_online else "🔴 **Offline / Not Started**",
            inline=False
        )
        embed.add_field(
            name="🤖 Discord Bot",
            value="🟢 **Online & Responsive**",
            inline=False
        )

        await interaction.followup.send(embed=embed)


    @app_commands.command(name="rules", description="Quick reference for duel rules, deckbuilding limits, and formats.")
    async def rules(self, interaction: discord.Interaction):
        """Displays standard duel rules and custom card balance guidelines."""
        embed = discord.Embed(
            title="📜 Duel Rules & Tournament Guidelines",
            description="Our live simulator operates under standard **Master Rule (2020 Revision)** with custom lore extensions.",
            color=0xf59e0b
        )
        embed.add_field(
            name="⚔️ Standard Duel Settings",
            value=(
                "• **Starting LP:** 8,000\n"
                "• **Starting Hand:** 5 Cards (Turn 1 player draws 0 on first turn)\n"
                "• **Deck Limits:** Main: 40-60 (Set 1 alpha relaxed to 34 min) | Extra: 0-15 | Side: 0-15\n"
                "• **Copies per Card:** Maximum 3 copies\n"
                "• **Duel Field:** Master Rule playmat (5 MMZ, 5 S/T, 2 EMZ, Field Spell, GY, Banished). Use `/board` to inspect!"
            ),
            inline=False
        )
        embed.add_field(
            name="🃏 Set 1: The Land of Kustomazi (TLOK)",
            value=(
                "• **Passcode Range:** `50,000,101 - 50,000,164` (`TLOK-001` - `TLOK-064`).\n"
                "• **Divine Mechanics:** Supreme Divine-Beast monsters (such as *Kasutamaiza, the Creator of Kustomazi*) require 3 Tributes, and their Normal Summon cannot be negated.\n"
                "• **Void & Creation Engine:** Spells and monsters synergize around continuous field control and special summoning servants from the Void.\n"
                "• **LeSpookie Halloween Chronicle:** Zombie Gemini monsters and Trick-or-Treat counter manipulation led by *Magnolia, Ghost of LeSpookie Street*.\n"
                "• **Pre-made Decks:** Load official tournament decks via `/load_character_deck`."
            ),
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Directory of all player and administrator slash commands.")
    async def help_command(self, interaction: discord.Interaction):
        """Displays organized directory of slash commands."""
        embed = discord.Embed(
            title="📖 Yu-Gi-Oh! Bot Command Directory",
            description="All commands are accessible via Discord slash commands (`/`):",
            color=0x3b82f6
        )

        embed.add_field(
            name="🃏 Card Search & Catalog",
            value=(
                "`/card <name>` - Search custom cards with artwork & stats\n"
                "`/cardpool` - Complete overview of Set 1: The Land of Kustomazi\n"
                "`/random_card` - Spotlight a random custom card\n"
                "`/recent_cards` - View newest custom cards added to the pool"
            ),
            inline=False
        )

        embed.add_field(
            name="📦 Player Deckbuilder",
            value=(
                "`/mydeck` - Inspect your current active custom deck\n"
                "`/deck_add <card>` - Add a card to your deck\n"
                "`/deck_remove <card>` - Remove a card from your deck\n"
                "`/load_character_deck <name>` - Load a pre-made story character deck"
            ),
            inline=False
        )

        embed.add_field(
            name="⚔️ Interactive Duels",
            value=(
                "`/duel @user` - Challenge a player to an in-chat interactive duel\n"
                "`/coinflip` - Flip a coin for turn order or effects\n"
                "`/dice [sides]` - Roll a die (default 6 sides)"
            ),
            inline=False
        )

        embed.add_field(
            name="🌌 Story, Lore & Utility",
            value=(
                "`/lore <query>` - Browse world sagas and character dossiers\n"
                "`/deck <name>` - Inspect pre-constructed character decks\n"
                "`/stats` - Platform & player stats\n"
                "`/ping` - Check bot & database latency\n"
                "`/info` - Simulator connection address & ports\n"
                "`/server_status` - Live health check for simulator"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Server & Admin Tools",
            value=(
                "`/duel_role` - Toggle your `@Duelist` ping role\n"
                "`/clear_messages [amount]` - Clean duel channel messages (Staff)\n"
                "`/admin sync_cards` - Rebuild simulator CDB & Lua scripts (Owner)\n"
                "`/admin reload <cog>` - Hot-reload bot extensions (Owner)"
            ),
            inline=False
        )

        embed.set_footer(text="The Land of Kustomazi • Set 1 Card & Duel Platform")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
