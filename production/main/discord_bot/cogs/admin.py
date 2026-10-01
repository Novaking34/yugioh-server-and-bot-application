#!/usr/bin/env python3
"""
=============================================================================
Administrator & Bot Owner Cog (Private / Host Only)
=============================================================================
Dedicated management commands for platform owners and server administrators:
- /admin sync_cards: Compile CDB & regenerate Lua scripts live from Discord
- /admin reload <cog>: Hot-reload bot extensions without downtime
- /admin simulator <status|restart>: Inspect or restart ocgcore container
- /admin db_stats: Comprehensive database inspection
- /admin export_deck @user: Export player deck to .ydk
- /admin broadcast <message>: Official platform announcement
Restricted to bot owners and users with administrator permissions.
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
import subprocess
import aiosqlite
from typing import Optional, Literal

# Resolve paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, DECKS_DIR, TOOLS_DIR
)


class AdminCog(commands.GroupCog, group_name="admin"):
    """Administrative and owner commands for the Yu-Gi-Oh! platform."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = STORY_DB_PATH

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Enforces that only administrators or bot application owners can run admin commands."""
        # Check if user is bot owner
        app_info = await self.bot.application_info()
        if interaction.user.id == app_info.owner.id:
            return True

        # Check guild administrator permission
        if interaction.guild and interaction.user.guild_permissions.administrator:
            return True

        await interaction.response.send_message(
            "⛔ **Access Denied**: This command is restricted to Bot Owners and Server Administrators.",
            ephemeral=True
        )
        return False

    @app_commands.command(name="sync_cards", description="Compile custom_cards.cdb and regenerate all Lua scripts live.")
    async def sync_cards(self, interaction: discord.Interaction):
        """Rebuilds CDB and generates Lua scripts."""
        await interaction.response.defer(ephemeral=True)

        try:
            sys.path.insert(0, TOOLS_DIR)
            from cdb_builder import build_cdb
            from lua_generator import generate_all_scripts

            cards_count = build_cdb(story_db_path=self.db_path, cdb_output_path=CDB_OUTPUT_PATH)
            scripts_count = generate_all_scripts(story_db=self.db_path, scripts_dir=SCRIPTS_DIR)

            embed = discord.Embed(
                title="✅ Card Pool Synchronized",
                description="Successfully compiled database and regenerated simulator scripts.",
                color=0x238636
            )
            embed.add_field(name="Cards Compiled to CDB", value=f"**{cards_count}** cards", inline=True)
            embed.add_field(name="Lua Effect Scripts", value=f"**{scripts_count}** scripts", inline=True)
            embed.add_field(name="CDB Path", value=f"`production/shared/expansions/custom_cards.cdb`", inline=False)
            embed.set_footer(text="Players can now update via the Client App!")

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"[-] Error during synchronization: {e}", ephemeral=True)

    @app_commands.command(name="reload", description="Hot-reload a bot extension cog without restarting.")
    @app_commands.describe(cog_name="Name of cog extension to reload (e.g. cogs.cardpool)")
    async def reload_cog(self, interaction: discord.Interaction, cog_name: str):
        """Reloads a specific cog."""
        await interaction.response.defer(ephemeral=True)

        try:
            await self.bot.reload_extension(cog_name)
            await interaction.followup.send(f"[+] Successfully reloaded **{cog_name}**.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"[-] Failed to reload {cog_name}: {e}", ephemeral=True)

    @app_commands.command(name="db_stats", description="Inspect database table counts and storage size.")
    async def db_stats(self, interaction: discord.Interaction):
        """Detailed database statistics."""
        await interaction.response.defer(ephemeral=True)

        if not os.path.exists(self.db_path):
            await interaction.followup.send("[-] Database file not found.", ephemeral=True)
            return

        db_size_kb = os.path.getsize(self.db_path) / 1024

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM custom_cards") as c:
                cards = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM factions") as c:
                factions = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM characters") as c:
                chars = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM decks") as c:
                decks = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(DISTINCT user_id) FROM player_decks") as c:
                players = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM duel_logs") as c:
                duels = (await c.fetchone())[0]

        embed = discord.Embed(
            title="📊 Database Diagnostics",
            color=0x3b82f6
        )
        embed.add_field(name="Storage Size", value=f"`{db_size_kb:.1f} KB`", inline=True)
        embed.add_field(name="Custom Cards", value=f"**{cards}**", inline=True)
        embed.add_field(name="Factions", value=f"**{factions}**", inline=True)
        embed.add_field(name="Story Characters", value=f"**{chars}**", inline=True)
        embed.add_field(name="Pre-Made Decks", value=f"**{decks}**", inline=True)
        embed.add_field(name="Active Duelists", value=f"**{players}**", inline=True)
        embed.add_field(name="Logged Duels", value=f"**{duels}**", inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="simulator", description="Inspect, view logs, monitor stats, or manage the Docker duel simulator container.")
    @app_commands.describe(action="Simulator action: status, logs, stats, restart, start, stop")
    async def simulator_control(self, interaction: discord.Interaction, action: Literal["status", "logs", "stats", "restart", "start", "stop"]):
        """Inspects, monitors, or controls the simulator container."""
        await interaction.response.defer(ephemeral=True)

        if action == "status":
            res = subprocess.run(
                ["docker", "ps", "-a", "--filter", "name=ygo-simulator-server", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            out = res.stdout.strip() or "Container not found."
            await interaction.followup.send(f"**🐳 Simulator Container Status**\n```text\n{out}\n```", ephemeral=True)
        elif action == "logs":
            res = subprocess.run(
                ["docker", "logs", "--tail", "25", "ygo-simulator-server"],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            out = (res.stdout + res.stderr).strip() or "No logs available."
            # Guard against exceeding Discord 2000 character limit
            if len(out) > 1900:
                out = "..." + out[-1890:]
            await interaction.followup.send(f"**📜 Simulator Recent Logs (last 25 lines)**\n```text\n{out}\n```", ephemeral=True)
        elif action == "stats":
            res = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}", "ygo-simulator-server"],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            out = res.stdout.strip() or "Unable to retrieve container metrics."
            await interaction.followup.send(f"**⚡ Simulator Resource Metrics**\n```text\n{out}\n```", ephemeral=True)
        elif action == "restart":
            res = subprocess.run(["docker", "compose", "restart"], capture_output=True, text=True, cwd=BASE_DIR)
            if res.returncode == 0:
                await interaction.followup.send("✅ Simulator container restarted successfully.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error restarting container:\n```{res.stderr}```", ephemeral=True)
        elif action == "start":
            res = subprocess.run(["docker", "compose", "up", "-d"], capture_output=True, text=True, cwd=BASE_DIR)
            if res.returncode == 0:
                await interaction.followup.send("✅ Simulator container started.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error starting container:\n```{res.stderr}```", ephemeral=True)
        elif action == "stop":
            res = subprocess.run(["docker", "compose", "stop"], capture_output=True, text=True, cwd=BASE_DIR)
            if res.returncode == 0:
                await interaction.followup.send("🛑 Simulator container stopped.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error stopping container:\n```{res.stderr}```", ephemeral=True)

    @app_commands.command(name="broadcast", description="Send an official platform announcement to the current channel.")
    @app_commands.describe(title="Announcement title", message="Announcement body text")
    async def broadcast(self, interaction: discord.Interaction, title: str, message: str):
        """Sends a rich announcement embed."""
        embed = discord.Embed(
            title=f"📢 {title}",
            description=message,
            color=0x8b5cf6
        )
        embed.set_footer(text=f"Official Announcement from {interaction.user.display_name}")
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("[+] Announcement broadcasted.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
