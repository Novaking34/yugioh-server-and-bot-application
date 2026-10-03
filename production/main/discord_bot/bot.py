#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Story, Duelingbook & Live Simulator Discord Bot
=============================================================================
Master runner and extension orchestrator for the Discord bot platform.
Loads modular cogs covering:
- `cogs.general`: Latency, server status, rules & info (/ping, /info)
- `cogs.cardpool`: Custom card search, Set 1 browser & telemetry (/card, /meta)
- `cogs.deckbuilding`: Player deck construction & Set 1 testing (/deck_add, /mydeck)
- `cogs.duel_engine`: Live interactive Discord duels with ELO stakes (/duel)
- `cogs.ranking`: Competitive ELO leaderboard & duelist licenses (/rank, /leaderboard)
- `cogs.story`: Narrative RPG campaign encounters & unlocks (/story, /story_stages)
- `cogs.lore`: World chronicles, sagas & stats (/lore, /stats)
- `cogs.server_tools`: Matchmaking notification roles, coin flips & dice
- `cogs.admin`: Hot-reloading, simulator diagnostics & state recovery
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
import asyncio
import uuid
import traceback

# Ensure discord_bot directory and project root are in Python path
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BOT_DIR)))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bot_config import BOT_CONFIG
from production.main.logger import get_logger

logger = get_logger("discord_bot")

COGS_LIST = [
    # Community & Player Cogs
    "cogs.general",
    "cogs.cardpool",
    "cogs.deckbuilding",
    "cogs.duel_engine",
    "cogs.ranking",
    "cogs.story",
    "cogs.lore",
    "cogs.server_tools",
    # Host & Owner Administration Cog
    "cogs.admin"
]


def attach_event_handlers(bot: commands.Bot):
    """Registers core lifecycle events and global error handlers to the bot."""

    @bot.event
    async def on_ready():
        logger.info(f"Bot successfully logged in as {bot.user.name} (ID: {bot.user.id})")
        logger.info("Synchronizing application slash commands with Discord...")

        try:
            guild_id = BOT_CONFIG.get("guild_id")
            if guild_id:
                guild_obj = discord.Object(id=guild_id)
                bot.tree.copy_global_to(guild=guild_obj)
                synced = await bot.tree.sync(guild=guild_obj)
                logger.info(f"Synchronized {len(synced)} slash commands to Guild ID {guild_id}.")
            else:
                synced = await bot.tree.sync()
                logger.info(f"Synchronized {len(synced)} global slash commands.")
            logger.info("Yu-Gi-Oh! Discord Bot is ONLINE and fully operational!")
        except Exception as e:
            logger.error(f"Failed to synchronize slash commands: {e}", exc_info=True)

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for application slash commands."""
        incident_id = str(uuid.uuid4())[:8]

        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ This command is on cooldown. Try again in {error.retry_after:.1f}s."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return

        if isinstance(error, app_commands.CheckFailure):
            # Already handled by cog or permission check
            return

        # Unhandled exceptions
        logger.error(
            f"[Incident #{incident_id}] Uncaught exception in slash command '{interaction.command.name if interaction.command else 'Unknown'}': {error}",
            exc_info=error
        )

        user_msg = (
            f"❌ An unexpected error occurred while executing this command.\n"
            f"**Incident ID:** `{incident_id}` (Logged to system diagnostics)."
        )

        try:
            if interaction.response.is_done():
                await interaction.followup.send(user_msg, ephemeral=True)
            else:
                await interaction.response.send_message(user_msg, ephemeral=True)
        except Exception as send_err:
            logger.warning(f"Could not send error message to user: {send_err}")


async def run_bot_instance(token: str, with_privileged_intents: bool = True):
    """Initializes and runs a bot instance with specified intents."""
    intents = discord.Intents.default()
    if with_privileged_intents:
        intents.message_content = True
        intents.members = True

    bot = commands.Bot(command_prefix=BOT_CONFIG["prefix"], intents=intents)
    attach_event_handlers(bot)

    # Load all modular cogs
    loaded_count = 0
    for cog_name in COGS_LIST:
        try:
            await bot.load_extension(cog_name)
            logger.info(f"Loaded modular extension: {cog_name}")
            loaded_count += 1
        except Exception as e:
            logger.error(f"Failed to load extension {cog_name}: {e}", exc_info=True)

    logger.info(f"Loaded {loaded_count}/{len(COGS_LIST)} modular extensions.")

    async with bot:
        await bot.start(token)


async def main():
    token = BOT_CONFIG.get("token")
    if not token or "YOUR_DISCORD_BOT_TOKEN" in token:
        logger.warning("No Discord Bot Token configured in environment.")
        print("[!] No Discord Bot Token configured.", flush=True)
        print("[*] To enable the bot, set your token in /home/professorseanex/yugioh-server/.env:", flush=True)
        print("    DISCORD_BOT_TOKEN=\"your_bot_token_here\"", flush=True)
        print("    Then launch via: ./manage.sh bot", flush=True)
        sys.exit(0)

    # Attempt to start with privileged intents first, fall back to standard intents if disabled
    try:
        await run_bot_instance(token, with_privileged_intents=True)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning("Privileged Gateway Intents not enabled. Falling back to Standard Intents...")
        await run_bot_instance(token, with_privileged_intents=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user.")
        print("\n[*] Bot shutdown requested by user.", flush=True)
