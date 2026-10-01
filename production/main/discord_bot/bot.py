#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Story, Duelingbook & Live Simulator Discord Bot
=============================================================================
Master runner and extension orchestrator for the Discord story bot.
Loads modular cogs covering:
- `cogs.cardpool`: Custom card search (/card) & autocomplete
- `cogs.deckbuilding`: Player deck creation (/deck_add, /mydeck)
- `cogs.duel_engine`: Live interactive Discord duels (/duel)
- `cogs.lore`: World chronicles, sagas & stats (/lore, /stats)

Usage:
    ./manage.sh bot
Or:
    ./venv/bin/python discord_bot/bot.py
=============================================================================
"""

import discord
from discord.ext import commands
import os
import sys
import asyncio

# Ensure discord_bot directory is in Python path for local cog imports
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from bot_config import BOT_CONFIG

# Configure Gateway Intents
# Message Content Intent is required to parse mentions and interactive text
intents = discord.Intents.default()
intents.message_content = True

COGS_LIST = [
    # Community & Player Cogs
    "cogs.general",
    "cogs.cardpool",
    "cogs.deckbuilding",
    "cogs.duel_engine",
    "cogs.lore",
    "cogs.server_tools",
    # Host & Owner Administration Cog
    "cogs.admin"
]


def attach_event_handlers(bot: commands.Bot):
    """Registers core lifecycle events to the bot instance."""

    @bot.event
    async def on_ready():
        print(f"[+] Bot logged in as {bot.user.name} (ID: {bot.user.id})", flush=True)
        print(f"[*] Synchronizing application slash commands with Discord...", flush=True)

        try:
            guild_id = BOT_CONFIG.get("guild_id")
            if guild_id:
                guild_obj = discord.Object(id=guild_id)
                bot.tree.copy_global_to(guild=guild_obj)
                synced = await bot.tree.sync(guild=guild_obj)
                print(f"[+] Synchronized {len(synced)} slash commands to Guild ID {guild_id}.", flush=True)
            else:
                synced = await bot.tree.sync()
                print(f"[+] Synchronized {len(synced)} global slash commands.", flush=True)
            print(f"[✓] Yu-Gi-Oh! Discord Bot is ONLINE and ready for duels & deckbuilding!", flush=True)
        except Exception as e:
            print(f"[-] Failed to synchronize slash commands: {e}", file=sys.stderr, flush=True)


async def run_bot_instance(token: str, with_privileged_intents: bool = True):
    """Initializes and runs a bot instance with specified intents."""
    intents = discord.Intents.default()
    if with_privileged_intents:
        intents.message_content = True
        intents.members = True

    bot = commands.Bot(command_prefix=BOT_CONFIG["prefix"], intents=intents)
    attach_event_handlers(bot)

    # Load all modular cogs
    for cog_name in COGS_LIST:
        try:
            await bot.load_extension(cog_name)
            print(f"[+] Loaded extension: {cog_name}", flush=True)
        except Exception as e:
            print(f"[-] Failed to load extension {cog_name}: {e}", file=sys.stderr, flush=True)

    async with bot:
        await bot.start(token)


async def main():
    token = BOT_CONFIG.get("token")
    if not token or "YOUR_DISCORD_BOT_TOKEN" in token:
        print("[!] No Discord Bot Token configured.", flush=True)
        print("[*] To enable the bot, set your token in /home/professorseanex/yugioh-server/.env:", flush=True)
        print("    DISCORD_BOT_TOKEN=\"your_bot_token_here\"", flush=True)
        print("    Then launch via: ./manage.sh bot", flush=True)
        sys.exit(0)

    # Attempt to start with privileged intents first, fall back to standard intents if disabled
    try:
        await run_bot_instance(token, with_privileged_intents=True)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n" + "=" * 70, flush=True)
        print("[!] Notice: Privileged Gateway Intents not enabled in Discord Developer Portal.", flush=True)
        print("[*] Reconnecting with Standard Intents...", flush=True)
        print("[*] All Slash Commands (/card, /duel, /mydeck, /admin, etc.) are FULLY functional!", flush=True)
        print("[*] To enable legacy text prefix commands (!card), enable 'Message Content Intent'", flush=True)
        print("    in https://discord.com/developers/applications/ -> [Bot] -> [Privileged Gateway Intents].", flush=True)
        print("=" * 70 + "\n", flush=True)
        await run_bot_instance(token, with_privileged_intents=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Bot shutdown requested by user.", flush=True)
