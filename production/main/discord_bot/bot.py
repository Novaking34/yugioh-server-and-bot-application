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

from config import BOT_CONFIG

# Configure Gateway Intents
# Message Content Intent is required to parse mentions and interactive text
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=BOT_CONFIG["prefix"], intents=intents)

COGS_LIST = [
    "cogs.cardpool",
    "cogs.deckbuilding",
    "cogs.duel_engine",
    "cogs.lore"
]


@bot.event
async def on_ready():
    """Triggered when the Discord client successfully authenticates and establishes connection."""
    print(f"[+] Bot logged in as {bot.user.name} (ID: {bot.user.id})")
    print(f"[*] Synchronizing application slash commands with Discord...")

    try:
        guild_id = BOT_CONFIG.get("guild_id")
        if guild_id:
            guild_obj = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild_obj)
            synced = await bot.tree.sync(guild=guild_obj)
            print(f"[+] Synchronized {len(synced)} slash commands to Guild ID {guild_id}.")
        else:
            synced = await bot.tree.sync()
            print(f"[+] Synchronized {len(synced)} global slash commands.")
    except Exception as e:
        print(f"[-] Failed to synchronize slash commands: {e}", file=sys.stderr)


async def load_extensions():
    """Dynamically loads all cog extensions."""
    for cog_name in COGS_LIST:
        try:
            await bot.load_extension(cog_name)
            print(f"[+] Loaded extension: {cog_name}")
        except Exception as e:
            print(f"[-] Failed to load extension {cog_name}: {e}", file=sys.stderr)


async def main():
    token = BOT_CONFIG.get("token")
    if not token or "YOUR_DISCORD_BOT_TOKEN" in token:
        print("[!] No Discord Bot Token configured.")
        print("[*] To enable the bot, set your token in /home/professorseanex/yugioh-server/.env:")
        print("    DISCORD_BOT_TOKEN=\"your_bot_token_here\"")
        print("    Then launch via: ./manage.sh bot")
        sys.exit(0)

    async with bot:
        await load_extensions()
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Bot shutdown requested by user.")
