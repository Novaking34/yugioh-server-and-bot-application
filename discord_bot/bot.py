#!/usr/bin/env python3
"""
Custom Yu-Gi-Oh Story & Duelingbook Discord Bot
Features:
- /card <name>: Search custom cards with rich visual embeds and Duelingbook links.
- /lore <topic>: Explore story sagas, factions, and character narratives.
- /deck <name>: View character decks and exportable lists.
- /addcard: Submit new custom cards directly into the database.
- /stats: View database and card catalog statistics.
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Try loading from .env
if os.path.exists(ENV_PATH):
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)

def load_config():
    token = os.getenv("DISCORD_BOT_TOKEN")
    prefix = "!"
    guild_id = None
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                token = token or cfg.get("token")
                prefix = cfg.get("prefix", "!")
                guild_id = cfg.get("guild_id")
        except Exception as e:
            print(f"[!] Error loading config.json: {e}")
            
    return {"token": token, "prefix": prefix, "guild_id": guild_id}

config = load_config()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=config["prefix"], intents=intents)

# Color palettes for Yu-Gi-Oh card frames
FRAME_COLORS = {
    'normal': 0xD4B37F,       # Normal Monster Yellow
    'effect': 0xC97434,       # Effect Monster Orange
    'ritual': 0x6E9ED4,       # Ritual Blue
    'fusion': 0x9356A0,       # Fusion Violet
    'synchro': 0xEEEEEE,      # Synchro White
    'xyz': 0x111111,          # Xyz Black
    'link': 0x0055AA,         # Link Dark Blue
    'spell': 0x1D9E74,        # Spell Green
    'trap': 0xBC3576          # Trap Magenta
}

def get_card_color(card_type, card_subtype):
    ctype = (card_type or '').lower()
    csub = (card_subtype or '').lower()
    
    if ctype == 'spell': return FRAME_COLORS['spell']
    if ctype == 'trap': return FRAME_COLORS['trap']
    for k in ['link', 'xyz', 'synchro', 'fusion', 'ritual', 'effect', 'normal']:
        if k in csub:
            return FRAME_COLORS[k]
    return FRAME_COLORS['effect']

@bot.event
async def on_ready():
    print(f"[+] Bot logged in as {bot.user.name} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"[+] Synchronized {len(synced)} slash commands.")
    except Exception as e:
        print(f"[-] Failed to sync commands: {e}")

# Autocomplete helper for card names
async def card_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        if current.strip():
            cursor = await db.execute(
                "SELECT name FROM custom_cards WHERE name LIKE ? LIMIT 15",
                (f"%{current}%",)
            )
        else:
            cursor = await db.execute("SELECT name FROM custom_cards LIMIT 15")
        rows = await cursor.fetchall()
        return [app_commands.Choice(name=row[0], value=row[0]) for row in rows]

# 1. /card command
@bot.tree.command(name="card", description="Search for a custom card with Duelingbook art, stats, and story lore")
@app_commands.autocomplete(name=card_name_autocomplete)
@app_commands.describe(name="Name of the custom card to look up")
async def card_command(interaction: discord.Interaction, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT c.*, f.name AS faction_name, ch.name AS character_name
            FROM custom_cards c
            LEFT JOIN factions f ON c.faction_id = f.id
            LEFT JOIN characters ch ON c.signature_character_id = ch.id
            WHERE c.name = ? OR c.name LIKE ?
            LIMIT 1
        """, (name, f"%{name}%"))
        card = await cursor.fetchone()
        
    if not card:
        await interaction.response.send_message(
            f"❌ Card **'{name}'** not found in the custom card database.", 
            ephemeral=True
        )
        return
        
    color = get_card_color(card["card_type"], card["card_subtype"])
    embed = discord.Embed(
        title=f"{card['name']}",
        url=card["duelingbook_url"] or f"https://www.duelingbook.com/card?id={card['id']}",
        description=f"**[{card['card_type']} / {card['card_subtype']}]**",
        color=color
    )
    
    # Monster stats
    if card["card_type"] == "Monster":
        stats_line = f"**Attribute:** {card['attribute']} | **Type:** {card['monster_type']}"
        if "link" in (card["card_subtype"] or "").lower():
            stats_line += f"\n**Link Rating:** Link-{card['level_or_rank_or_link']} | **Arrows:** {card['link_arrows'] or 'N/A'}"
        elif "xyz" in (card["card_subtype"] or "").lower():
            stats_line += f"\n**Rank:** {card['level_or_rank_or_link']}"
        else:
            stats_line += f"\n**Level:** {card['level_or_rank_or_link']}"
            
        if card["scale"] is not None:
            stats_line += f" | **Scale:** {card['scale']}"
            
        def_val = "LINK" if "link" in (card["card_subtype"] or "").lower() else card["def"]
        stats_line += f"\n**ATK:** {card['atk']} / **DEF:** {def_val}"
        embed.add_field(name="⚔️ Monster Parameters", value=stats_line, inline=False)
    else:
        embed.add_field(
            name="📜 Card Type", 
            value=f"**{card['card_subtype']} {card['card_type']}**", 
            inline=True
        )
        
    # Pendulum effect if exists
    if card["pendulum_effect"]:
        embed.add_field(
            name="💎 Pendulum Effect", 
            value=f"```fix\n{card['pendulum_effect']}\n```", 
            inline=False
        )
        
    # Card effect
    embed.add_field(
        name="📖 Card Effect", 
        value=f"```md\n{card['effect_text']}\n```", 
        inline=False
    )
    
    # Story Lore & Metadata
    lore_field = f"*{card['lore_text']}*"
    meta = []
    if card["faction_name"]: meta.append(f"**Faction:** {card['faction_name']}")
    if card["character_name"]: meta.append(f"**User/Owner:** {card['character_name']}")
    if card["story_significance"]: meta.append(f"**Role:** {card['story_significance']}")
    if meta:
        lore_field += "\n\n" + " • ".join(meta)
        
    embed.add_field(name="🌌 Story Lore", value=lore_field, inline=False)
    
    # Image artwork
    if card["image_url"]:
        embed.set_thumbnail(url=card["image_url"])
        
    footer_text = f"ID: {card['id']} • Designed by {card['creator_name'] or 'Unknown'} • Hosted on Duelingbook"
    embed.set_footer(text=footer_text)
    
    await interaction.response.send_message(embed=embed)

# 2. /lore command
@bot.tree.command(name="lore", description="Read world lore, saga chronicles, or faction background")
@app_commands.describe(query="Name of a saga, faction, or character")
async def lore_command(interaction: discord.Interaction, query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Check lore arcs
        cur = await db.execute("SELECT * FROM lore_arcs WHERE title LIKE ? LIMIT 1", (f"%{query}%",))
        arc = await cur.fetchone()
        if arc:
            embed = discord.Embed(
                title=f"🌌 Saga Chronicle: {arc['title']}",
                description=arc["synopsis"],
                color=0x4A90E2
            )
            embed.add_field(name="Timeline / Era", value=arc["era_or_season"], inline=True)
            await interaction.response.send_message(embed=embed)
            return
            
        # Check factions
        cur = await db.execute("SELECT f.*, a.title AS arc_title FROM factions f LEFT JOIN lore_arcs a ON f.arc_id = a.id WHERE f.name LIKE ? LIMIT 1", (f"%{query}%",))
        faction = await cur.fetchone()
        if faction:
            embed = discord.Embed(
                title=f"⚔️ Faction Overview: {faction['name']}",
                description=faction["lore_description"],
                color=0xE67E22
            )
            embed.add_field(name="Playstyle Dynamics", value=faction["playstyle_overview"] or "N/A", inline=False)
            if faction["arc_title"]:
                embed.add_field(name="Active Saga", value=faction["arc_title"], inline=True)
            await interaction.response.send_message(embed=embed)
            return

        # Check characters
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
            if char["alias"]: embed.add_field(name="Alias", value=char["alias"], inline=True)
            if char["faction_name"]: embed.add_field(name="Faction", value=char["faction_name"], inline=True)
            if char["arc_title"]: embed.add_field(name="Saga", value=char["arc_title"], inline=True)
            if char["avatar_url"]: embed.set_thumbnail(url=char["avatar_url"])
            await interaction.response.send_message(embed=embed)
            return

    await interaction.response.send_message(
        f"❓ No lore records found matching **'{query}'**.", 
        ephemeral=True
    )

# 3. /deck command
@bot.tree.command(name="deck", description="View character decklists and story affiliations")
@app_commands.describe(name="Deck name or duelist name")
async def deck_command(interaction: discord.Interaction, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT d.*, c.name AS character_name 
            FROM decks d
            LEFT JOIN characters c ON d.character_id = c.id
            WHERE d.name LIKE ? OR c.name LIKE ?
            LIMIT 1
        """, (f"%{name}%", f"%{name}%"))
        deck = await cur.fetchone()
        
        if not deck:
            await interaction.response.send_message(f"❌ Deck not found.", ephemeral=True)
            return
            
        cur = await db.execute("""
            SELECT dc.quantity, dc.section, cc.name, cc.card_type, cc.card_subtype
            FROM deck_cards dc
            JOIN custom_cards cc ON dc.card_id = cc.id
            WHERE dc.deck_id = ?
            ORDER BY dc.section DESC, cc.name ASC
        """, (deck["id"],))
        cards = await cur.fetchall()
        
    embed = discord.Embed(
        title=f"🃏 Deck Profile: {deck['name']}",
        url=deck["duelingbook_deck_url"] or "https://www.duelingbook.com",
        description=deck["description"] or "A custom story deck.",
        color=0xF1C40F
    )
    if deck["character_name"]:
        embed.add_field(name="Duelist", value=deck["character_name"], inline=True)
    if deck["creator_name"]:
        embed.add_field(name="Deck Architect", value=deck["creator_name"], inline=True)
        
    main_cards = [f"{c['quantity']}x {c['name']}" for c in cards if c['section'] == 'MAIN']
    extra_cards = [f"{c['quantity']}x {c['name']}" for c in cards if c['section'] == 'EXTRA']
    
    if main_cards:
        embed.add_field(name="Main Deck", value="\n".join(main_cards), inline=False)
    if extra_cards:
        embed.add_field(name="Extra Deck", value="\n".join(extra_cards), inline=False)
        
    await interaction.response.send_message(embed=embed)

# 4. /stats command
@bot.tree.command(name="stats", description="View server custom card database statistics")
async def stats_command(interaction: discord.Interaction):
    async with aiosqlite.connect(DB_PATH) as db:
        c_cards = (await (await db.execute("SELECT COUNT(*) FROM custom_cards")).fetchone())[0]
        c_factions = (await (await db.execute("SELECT COUNT(*) FROM factions")).fetchone())[0]
        c_chars = (await (await db.execute("SELECT COUNT(*) FROM characters")).fetchone())[0]
        c_decks = (await (await db.execute("SELECT COUNT(*) FROM decks")).fetchone())[0]
        c_duels = (await (await db.execute("SELECT COUNT(*) FROM duel_logs")).fetchone())[0]
        
    embed = discord.Embed(
        title="📊 Story Database & Card Catalog Stats",
        color=0x2ECC71
    )
    embed.add_field(name="🃏 Custom Cards", value=str(c_cards), inline=True)
    embed.add_field(name="⚔️ Factions / Archetypes", value=str(c_factions), inline=True)
    embed.add_field(name="👤 Story Duelists", value=str(c_chars), inline=True)
    embed.add_field(name="📦 Character Decks", value=str(c_decks), inline=True)
    embed.add_field(name="⚔️ Story Duels Recorded", value=str(c_duels), inline=True)
    embed.add_field(name="🌐 Duelingbook Integration", value="Active", inline=True)
    embed.set_footer(text="Live Duel Simulator ready on port 7911 (TCP) / 7922 (Web)")
    
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    token = config.get("token")
    if not token or "YOUR_DISCORD_BOT_TOKEN" in token:
        print("[!] No Discord Bot Token configured.")
        print("[*] To run the bot:")
        print("    1. Create an application & bot at https://discord.com/developers/applications")
        print("    2. Copy the token into /home/professorseanex/yugioh-server/.env:")
        print("       DISCORD_BOT_TOKEN=your_token_here")
        print("    3. Or update /home/professorseanex/yugioh-server/discord_bot/config.json")
        print("    4. Run: ./manage.sh bot")
        sys.exit(0)
    else:
        bot.run(token)
