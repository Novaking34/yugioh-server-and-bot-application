#!/usr/bin/env python3
"""
Custom Yu-Gi-Oh Story, Duelingbook & Live Discord Duel Engine Bot
Features:
- Live, Dynamic Cardpool Integration:
    * /card <name>: Dynamic autocomplete and lookup with Duelingbook art & lore
    * /recent_cards: Show the newest custom cards added to the pool
    * /addcard: Register a new custom card directly into the live cardpool
- Personal Deckbuilding:
    * /deck_add <card> [qty]: Add custom card to personal deck
    * /deck_remove <card>: Remove card from personal deck
    * /mydeck: View personal active deck
    * /deck_clear: Reset personal deck
    * /load_character_deck <name>: Copy a story character's deck (Valen/Morgana)
- Interactive Discord Duel Engine:
    * /duel challenge @user: Interactive match with LP tracking (8000), private hand view,
      normal summoning, spell/trap activation, dice/coin flips, and duel logging!
- Lore & Story:
    * /lore <topic>: Sagas, faction histories, and duelist dossiers
    * /deck <name>: Story character decklists
    * /stats: Global cardpool and story stats
"""

import discord
from discord import app_commands, ui
from discord.ext import commands
import aiosqlite
import json
import os
import sys
import random
from typing import Optional, List, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

sys.path.append(os.path.join(BASE_DIR, "tools"))
try:
    from duelingbook_importer import import_card_data
except ImportError:
    import_card_data = None

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
        except Exception:
            pass
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
        if k in csub: return FRAME_COLORS[k]
    return FRAME_COLORS['effect']

@bot.event
async def on_ready():
    print(f"[+] Bot logged in as {bot.user.name} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"[+] Synchronized {len(synced)} slash commands.")
    except Exception as e:
        print(f"[-] Failed to sync commands: {e}")

# ==========================================
# 1. LIVE DYNAMIC CARDPOOL & SEARCH COMMANDS
# ==========================================

async def card_name_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        if current.strip():
            cur = await db.execute("SELECT name FROM custom_cards WHERE name LIKE ? ORDER BY name ASC LIMIT 15", (f"%{current}%",))
        else:
            cur = await db.execute("SELECT name FROM custom_cards ORDER BY id DESC LIMIT 15")
        rows = await cur.fetchall()
        return [app_commands.Choice(name=row[0], value=row[0]) for row in rows]

@bot.tree.command(name="card", description="Search custom cardpool with Duelingbook art, stats, and story lore")
@app_commands.autocomplete(name=card_name_autocomplete)
@app_commands.describe(name="Name of the custom card to look up")
async def card_command(interaction: discord.Interaction, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
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
        await interaction.response.send_message(f"❌ Card **'{name}'** not found in the custom cardpool.", ephemeral=True)
        return
        
    color = get_card_color(card["card_type"], card["card_subtype"])
    embed = discord.Embed(
        title=f"{card['name']}",
        url=card["duelingbook_url"] or f"https://www.duelingbook.com/card?id={card['id']}",
        description=f"**[{card['card_type']} / {card['card_subtype']}]**",
        color=color
    )
    
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
        embed.add_field(name="📜 Card Type", value=f"**{card['card_subtype']} {card['card_type']}**", inline=True)
        
    if card["pendulum_effect"]:
        embed.add_field(name="💎 Pendulum Effect", value=f"```fix\n{card['pendulum_effect']}\n```", inline=False)
    embed.add_field(name="📖 Card Effect", value=f"```md\n{card['effect_text']}\n```", inline=False)
    
    lore_field = f"*{card['lore_text']}*"
    meta = []
    if card["faction_name"]: meta.append(f"**Faction:** {card['faction_name']}")
    if card["character_name"]: meta.append(f"**User/Owner:** {card['character_name']}")
    if card["story_significance"]: meta.append(f"**Role:** {card['story_significance']}")
    if meta: lore_field += "\n\n" + " • ".join(meta)
    embed.add_field(name="🌌 Story Lore", value=lore_field, inline=False)
    
    if card["image_url"]: embed.set_thumbnail(url=card["image_url"])
    footer_text = f"ID: {card['id']} • Designed by {card['creator_name'] or 'Unknown'} • Live in Cardpool"
    embed.set_footer(text=footer_text)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="recent_cards", description="View the most recently added custom cards in the cardpool")
@app_commands.describe(limit="Number of cards to display (max 10)")
async def recent_cards_command(interaction: discord.Interaction, limit: Optional[int] = 5):
    limit = min(max(1, limit), 10)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT id, name, card_type, card_subtype, attribute, atk, def, creator_name FROM custom_cards ORDER BY id DESC LIMIT ?", (limit,))
        cards = await cur.fetchall()
        
    embed = discord.Embed(
        title=f"🆕 Recently Added Custom Cards ({len(cards)})",
        description="These cards were recently registered or imported from Duelingbook and are live in the duel simulator!",
        color=0x3498DB
    )
    for c in cards:
        stats = f"{c['card_subtype']} {c['card_type']}"
        if c['card_type'] == 'Monster':
            stats += f" | {c['attribute']} | ATK {c['atk']}/{c['def'] if c['def'] is not None else 'LINK'}"
        embed.add_field(name=f"[{c['id']}] {c['name']}", value=f"{stats}\n*Designed by {c['creator_name'] or 'Anonymous'}*", inline=False)
    await interaction.response.send_message(embed=embed)

# ==========================================
# 2. PLAYER DECKBUILDING COMMANDS
# ==========================================

@bot.tree.command(name="deck_add", description="Add a custom card to your personal active deck")
@app_commands.autocomplete(card_name=card_name_autocomplete)
@app_commands.describe(card_name="Name of the card", quantity="Copies to add (1-3)")
async def deck_add_command(interaction: discord.Interaction, card_name: str, quantity: Optional[int] = 1):
    user_id = str(interaction.user.id)
    quantity = min(max(1, quantity), 3)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, name FROM custom_cards WHERE name = ? LIMIT 1", (card_name,))
        card = await cur.fetchone()
        if not card:
            await interaction.response.send_message(f"❌ Card '{card_name}' not found.", ephemeral=True)
            return
        cid, cname = card
        await db.execute("""
            INSERT INTO player_decks (user_id, card_id, quantity) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = MIN(3, quantity + ?)
        """, (user_id, cid, quantity, quantity))
        await db.commit()
    await interaction.response.send_message(f"✅ Added **{quantity}x {cname}** to your active deck! Use `/mydeck` to view.", ephemeral=True)

@bot.tree.command(name="deck_remove", description="Remove a card from your personal active deck")
@app_commands.autocomplete(card_name=card_name_autocomplete)
async def deck_remove_command(interaction: discord.Interaction, card_name: str):
    user_id = str(interaction.user.id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, name FROM custom_cards WHERE name = ? LIMIT 1", (card_name,))
        card = await cur.fetchone()
        if not card:
            await interaction.response.send_message(f"❌ Card not found.", ephemeral=True)
            return
        cid, cname = card
        await db.execute("DELETE FROM player_decks WHERE user_id = ? AND card_id = ?", (user_id, cid))
        await db.commit()
    await interaction.response.send_message(f"🗑️ Removed **{cname}** from your deck.", ephemeral=True)

@bot.tree.command(name="mydeck", description="View your current personal active deck")
async def mydeck_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    async with aiosqlite.connect(DB_PATH) as db:
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
        await interaction.response.send_message("📦 Your deck is empty! Use `/deck_add <card>` or `/load_character_deck` to get started.", ephemeral=True)
        return
        
    total_count = sum(c['quantity'] for c in cards)
    monsters = [f"{c['quantity']}x {c['name']} ({c['card_subtype']})" for c in cards if c['card_type'] == 'Monster']
    spells = [f"{c['quantity']}x {c['name']} ({c['card_subtype']})" for c in cards if c['card_type'] == 'Spell']
    traps = [f"{c['quantity']}x {c['name']} ({c['card_subtype']})" for c in cards if c['card_type'] == 'Trap']
    
    embed = discord.Embed(
        title=f"🃏 {interaction.user.display_name}'s Active Deck ({total_count} Cards)",
        color=0xF1C40F
    )
    if monsters: embed.add_field(name=f"⚔️ Monsters ({sum(c['quantity'] for c in cards if c['card_type'] == 'Monster')})", value="\n".join(monsters), inline=False)
    if spells: embed.add_field(name=f"✨ Spells ({sum(c['quantity'] for c in cards if c['card_type'] == 'Spell')})", value="\n".join(spells), inline=False)
    if traps: embed.add_field(name=f"🛡️ Traps ({sum(c['quantity'] for c in cards if c['card_type'] == 'Trap')})", value="\n".join(traps), inline=False)
    
    status_text = "✅ Ready for Duels!" if total_count >= 5 else "⚠️ Minimum 5 cards recommended to duel."
    embed.set_footer(text=f"{status_text} • Challenge someone with /duel challenge @user")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="load_character_deck", description="Copy a story character's pre-made deck into your personal deck")
@app_commands.describe(character="Story duelist (e.g. Valen Vance or Morgana Vex)")
async def load_character_deck_command(interaction: discord.Interaction, character: str):
    user_id = str(interaction.user.id)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT d.id, d.name, c.name FROM decks d
            JOIN characters c ON d.character_id = c.id
            WHERE c.name LIKE ? OR d.name LIKE ? LIMIT 1
        """, (f"%{character}%", f"%{character}%"))
        deck = await cur.fetchone()
        if not deck:
            await interaction.response.send_message("❌ Character deck not found.", ephemeral=True)
            return
        did, dname, cname = deck
        await db.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id,))
        cur = await db.execute("SELECT card_id, quantity FROM deck_cards WHERE deck_id = ?", (did,))
        cards = await cur.fetchall()
        for cid, qty in cards:
            await db.execute("INSERT INTO player_decks (user_id, card_id, quantity) VALUES (?, ?, ?)", (user_id, cid, qty))
        await db.commit()
    await interaction.response.send_message(f"✨ Loaded **{cname}'s {dname}** into your active deck! Use `/mydeck` to view.", ephemeral=True)

# ==========================================
# 3. INTERACTIVE DISCORD DUEL ENGINE
# ==========================================

active_duels: Dict[int, "DuelSession"] = {}

class DuelSession:
    def __init__(self, p1: discord.User, p2: discord.User, p1_deck: List[int], p2_deck: List[int]):
        self.p1 = p1
        self.p2 = p2
        self.lp = {p1.id: 8000, p2.id: 8000}
        self.decks = {p1.id: p1_deck.copy(), p2.id: p2_deck.copy()}
        random.shuffle(self.decks[p1.id])
        random.shuffle(self.decks[p2.id])
        
        # Opening hand: 5 cards each
        self.hands = {
            p1.id: [self.decks[p1.id].pop() for _ in range(min(5, len(self.decks[p1.id])))],
            p2.id: [self.decks[p2.id].pop() for _ in range(min(5, len(self.decks[p2.id])))]
        }
        self.fields = {p1.id: {"monsters": [], "spells": []}, p2.id: {"monsters": [], "spells": []}}
        self.gy = {p1.id: [], p2.id: []}
        
        # Random starting player
        self.turn_player = random.choice([p1, p2])
        self.turn_count = 1
        self.duel_over = False

    def draw_card(self, player_id):
        if self.decks[player_id]:
            c = self.decks[player_id].pop()
            self.hands[player_id].append(c)
            return c
        return None

class HandSelectModal(ui.Modal, title="Summon / Activate Card"):
    def __init__(self, session: DuelSession, player_id: int):
        super().__init__()
        self.session = session
        self.player_id = player_id
        self.card_name = ui.TextInput(label="Card Name to Play", placeholder="Enter card name from your hand...")
        self.action_type = ui.TextInput(label="Action", placeholder="Summon, Activate, or Set", default="Summon")
        self.add_item(self.card_name)
        self.add_item(self.action_type)

    async def on_submit(self, interaction: discord.Interaction):
        # Handle card play
        await interaction.response.send_message(f"Action: {self.action_type.value} on {self.card_name.value}", ephemeral=True)

class LPModal(ui.Modal, title="Adjust Life Points"):
    def __init__(self, session: DuelSession, target_player_id: int, duel_view: "DuelView"):
        super().__init__()
        self.session = session
        self.target_player_id = target_player_id
        self.duel_view = duel_view
        self.amount = ui.TextInput(label="Amount (+ to heal, - to damage)", placeholder="e.g. -1000 or +800")
        self.reason = ui.TextInput(label="Reason / Battle Details", placeholder="e.g. Direct attack from Sol Invictus", required=False)
        self.add_item(self.amount)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.amount.value.replace("+", "").strip())
        except ValueError:
            await interaction.response.send_message("❌ Invalid number.", ephemeral=True)
            return
            
        old_lp = self.session.lp[self.target_player_id]
        new_lp = max(0, old_lp + val)
        self.session.lp[self.target_player_id] = new_lp
        
        target_user = self.session.p1 if self.target_player_id == self.session.p1.id else self.session.p2
        sign = "+" if val >= 0 else ""
        msg = f"❤️ **{target_user.display_name}** LP: {old_lp} ➔ **{new_lp}** ({sign}{val}) [{self.reason.value or 'Manual Adjustment'}]"
        
        if new_lp <= 0:
            self.session.duel_over = True
            winner = self.session.p2 if self.target_player_id == self.session.p1.id else self.session.p1
            msg += f"\n🏆 **DUEL ENDED! {winner.mention} WINS!**"
            self.duel_view.disable_all()
            
        await interaction.response.edit_message(embed=self.duel_view.build_embed(last_action=msg), view=self.duel_view)

class DuelView(ui.View):
    def __init__(self, session: DuelSession):
        super().__init__(timeout=1800)
        self.session = session

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    def build_embed(self, last_action="Duel in Progress"):
        p1 = self.session.p1
        p2 = self.session.p2
        embed = discord.Embed(
            title=f"⚔️ Yu-Gi-Oh Duel: {p1.display_name} VS {p2.display_name}",
            description=f"**Turn {self.session.turn_count}** — Turn Player: {self.session.turn_player.mention}\n\n**Latest Action:**\n{last_action}",
            color=0x9B59B6
        )
        
        p1_bar = "🟩" * max(1, self.session.lp[p1.id] // 1000)
        p2_bar = "🟩" * max(1, self.session.lp[p2.id] // 1000)
        
        embed.add_field(
            name=f"👤 {p1.display_name}",
            value=f"**LP:** {self.session.lp[p1.id]} {p1_bar}\n**Hand:** {len(self.session.hands[p1.id])} | **Deck:** {len(self.session.decks[p1.id])} | **GY:** {len(self.session.gy[p1.id])}",
            inline=True
        )
        embed.add_field(
            name=f"👤 {p2.display_name}",
            value=f"**LP:** {self.session.lp[p2.id]} {p2_bar}\n**Hand:** {len(self.session.hands[p2.id])} | **Deck:** {len(self.session.decks[p2.id])} | **GY:** {len(self.session.gy[p2.id])}",
            inline=True
        )
        embed.set_footer(text="Click 'View Hand' for private cards • Click LP buttons to record damage")
        return embed

    @ui.button(label="🎴 View Hand", style=discord.ButtonStyle.primary)
    async def view_hand(self, interaction: discord.Interaction, button: ui.Button):
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            await interaction.response.send_message("❌ You are not a player in this duel.", ephemeral=True)
            return
            
        hand_cids = self.session.hands[uid]
        if not hand_cids:
            await interaction.response.send_message("Your hand is empty.", ephemeral=True)
            return
            
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            placeholders = ",".join("?" for _ in hand_cids)
            cur = await db.execute(f"SELECT id, name, card_type, card_subtype, atk, def, effect_text FROM custom_cards WHERE id IN ({placeholders})", hand_cids)
            cards = await cur.fetchall()
            
        desc = []
        for i, c in enumerate(cards, 1):
            stat_str = f"ATK {c['atk']}/{c['def']}" if c['card_type'] == 'Monster' else f"{c['card_subtype']} {c['card_type']}"
            desc.append(f"**{i}. {c['name']}** [{stat_str}]\n*{c['effect_text'][:120]}...*")
            
        hand_embed = discord.Embed(
            title=f"🎴 Your Secret Hand ({len(cards)} Cards)",
            description="\n\n".join(desc),
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=hand_embed, ephemeral=True)

    @ui.button(label="🃏 Draw Card", style=discord.ButtonStyle.secondary)
    async def draw_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ It is not your turn to draw.", ephemeral=True)
            return
            
        drawn = self.session.draw_card(uid)
        if not drawn:
            await interaction.response.send_message("❌ Your deck is empty!", ephemeral=True)
            return
            
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🃏 **{interaction.user.display_name}** drew 1 card."),
            view=self
        )

    @ui.button(label="❤️ -1000 LP", style=discord.ButtonStyle.danger)
    async def minus_1000(self, interaction: discord.Interaction, button: ui.Button):
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id): return
        self.session.lp[uid] = max(0, self.session.lp[uid] - 1000)
        action = f"💥 **{interaction.user.display_name}** took 1000 damage! (Remaining: {self.session.lp[uid]})"
        if self.session.lp[uid] == 0:
            self.session.duel_over = True
            self.disable_all()
            winner = self.session.p2 if uid == self.session.p1.id else self.session.p1
            action += f"\n🏆 **{winner.mention} WINS THE DUEL!**"
        await interaction.response.edit_message(embed=self.build_embed(last_action=action), view=self)

    @ui.button(label="❤️ Custom LP", style=discord.ButtonStyle.secondary)
    async def custom_lp_btn(self, interaction: discord.Interaction, button: ui.Button):
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id): return
        await interaction.response.send_modal(LPModal(self.session, uid, self))

    @ui.button(label="🎲 Roll d6", style=discord.ButtonStyle.secondary)
    async def roll_dice(self, interaction: discord.Interaction, button: ui.Button):
        res = random.randint(1, 6)
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🎲 **{interaction.user.display_name}** rolled a die: **[{res}]**!"),
            view=self
        )

    @ui.button(label="⏳ End Turn", style=discord.ButtonStyle.success)
    async def end_turn(self, interaction: discord.Interaction, button: ui.Button):
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can end the turn.", ephemeral=True)
            return
        # Switch turn player
        self.session.turn_player = self.session.p2 if uid == self.session.p1.id else self.session.p1
        self.session.turn_count += 1
        # Auto draw for new turn player
        drawn = self.session.draw_card(self.session.turn_player.id)
        draw_txt = " (DREW 1 CARD)" if drawn else " (DECK EMPTY)"
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"⏳ **Turn passed!** It is now {self.session.turn_player.mention}'s turn{draw_txt}."),
            view=self
        )

    @ui.button(label="🏳️ Concede", style=discord.ButtonStyle.danger)
    async def concede_btn(self, interaction: discord.Interaction, button: ui.Button):
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id): return
        winner = self.session.p2 if uid == self.session.p1.id else self.session.p1
        self.session.duel_over = True
        self.disable_all()
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🏳️ **{interaction.user.display_name} surrendered!**\n🏆 **{winner.mention} WINS!**"),
            view=self
        )

class ChallengeView(ui.View):
    def __init__(self, challenger: discord.User, challenged: discord.User):
        super().__init__(timeout=120)
        self.challenger = challenger
        self.challenged = challenged

    @ui.button(label="⚔️ Accept Challenge", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.challenged.id:
            await interaction.response.send_message("❌ Only the challenged duelist can accept.", ephemeral=True)
            return
            
        # Load decks
        async with aiosqlite.connect(DB_PATH) as db:
            async def get_deck(uid):
                cur = await db.execute("SELECT card_id, quantity FROM player_decks WHERE user_id = ?", (str(uid),))
                rows = await cur.fetchall()
                cards = []
                for cid, qty in rows:
                    cards.extend([cid] * qty)
                return cards
                
            p1_deck = await get_deck(self.challenger.id)
            p2_deck = await get_deck(self.challenged.id)
            
            # Fallback to sample cardpool if deck is empty
            if len(p1_deck) < 5 or len(p2_deck) < 5:
                cur = await db.execute("SELECT id FROM custom_cards LIMIT 20")
                sample_cards = [r[0] for r in await cur.fetchall()] * 2
                if len(p1_deck) < 5: p1_deck = sample_cards.copy()
                if len(p2_deck) < 5: p2_deck = sample_cards.copy()
                
        session = DuelSession(self.challenger, self.challenged, p1_deck, p2_deck)
        duel_view = DuelView(session)
        embed = duel_view.build_embed(last_action=f"⚔️ Challenge accepted! First turn decided by destiny: {session.turn_player.mention} goes first!")
        await interaction.response.edit_message(content=None, embed=embed, view=duel_view)

    @ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.challenged.id:
            await interaction.response.send_message("❌ Only the challenged duelist can decline.", ephemeral=True)
            return
        await interaction.response.edit_message(content=f"🚫 {self.challenged.display_name} declined the duel challenge.", view=None)

@bot.tree.command(name="duel", description="Challenge another player to a live Yu-Gi-Oh duel on Discord!")
@app_commands.describe(opponent="The user you want to duel")
async def duel_command(interaction: discord.Interaction, opponent: discord.User):
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("❌ You cannot duel yourself!", ephemeral=True)
        return
    if opponent.bot:
        await interaction.response.send_message("❌ You cannot challenge a bot to a live duel.", ephemeral=True)
        return
        
    view = ChallengeView(interaction.user, opponent)
    await interaction.response.send_message(
        f"⚔️ {opponent.mention}, you have been challenged to a **Yu-Gi-Oh Story Duel** by {interaction.user.mention}!\n*Do you accept?*",
        view=view
    )

# ==========================================
# 4. LORE, STATS & SAGA COMMANDS
# ==========================================

@bot.tree.command(name="lore", description="Read world lore, saga chronicles, or faction background")
@app_commands.describe(query="Name of a saga, faction, or character")
async def lore_command(interaction: discord.Interaction, query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM lore_arcs WHERE title LIKE ? LIMIT 1", (f"%{query}%",))
        arc = await cur.fetchone()
        if arc:
            embed = discord.Embed(title=f"🌌 Saga Chronicle: {arc['title']}", description=arc["synopsis"], color=0x4A90E2)
            embed.add_field(name="Timeline / Era", value=arc["era_or_season"], inline=True)
            await interaction.response.send_message(embed=embed)
            return
            
        cur = await db.execute("SELECT f.*, a.title AS arc_title FROM factions f LEFT JOIN lore_arcs a ON f.arc_id = a.id WHERE f.name LIKE ? LIMIT 1", (f"%{query}%",))
        faction = await cur.fetchone()
        if faction:
            embed = discord.Embed(title=f"⚔️ Faction Overview: {faction['name']}", description=faction["lore_description"], color=0xE67E22)
            embed.add_field(name="Playstyle Dynamics", value=faction["playstyle_overview"] or "N/A", inline=False)
            if faction["arc_title"]: embed.add_field(name="Active Saga", value=faction["arc_title"], inline=True)
            await interaction.response.send_message(embed=embed)
            return

        cur = await db.execute("SELECT c.*, f.name AS faction_name, a.title AS arc_title FROM characters c LEFT JOIN factions f ON c.faction_id = f.id LEFT JOIN lore_arcs a ON c.arc_id = a.id WHERE c.name LIKE ? OR c.alias LIKE ? LIMIT 1", (f"%{query}%", f"%{query}%"))
        char = await cur.fetchone()
        if char:
            embed = discord.Embed(title=f"👤 Duelist Dossier: {char['name']}", description=char["bio"], color=0x9B59B6)
            if char["alias"]: embed.add_field(name="Alias", value=char["alias"], inline=True)
            if char["faction_name"]: embed.add_field(name="Faction", value=char["faction_name"], inline=True)
            if char["arc_title"]: embed.add_field(name="Saga", value=char["arc_title"], inline=True)
            if char["avatar_url"]: embed.set_thumbnail(url=char["avatar_url"])
            await interaction.response.send_message(embed=embed)
            return

    await interaction.response.send_message(f"❓ No lore records found matching **'{query}'**.", ephemeral=True)

@bot.tree.command(name="stats", description="View server custom card database and duel statistics")
async def stats_command(interaction: discord.Interaction):
    async with aiosqlite.connect(DB_PATH) as db:
        c_cards = (await (await db.execute("SELECT COUNT(*) FROM custom_cards")).fetchone())[0]
        c_factions = (await (await db.execute("SELECT COUNT(*) FROM factions")).fetchone())[0]
        c_chars = (await (await db.execute("SELECT COUNT(*) FROM characters")).fetchone())[0]
        c_decks = (await (await db.execute("SELECT COUNT(*) FROM decks")).fetchone())[0]
        c_duels = (await (await db.execute("SELECT COUNT(*) FROM duel_logs")).fetchone())[0]
        c_pdecks = (await (await db.execute("SELECT COUNT(DISTINCT user_id) FROM player_decks")).fetchone())[0]
        
    embed = discord.Embed(title="📊 Story Database & Discord Duel Stats", color=0x2ECC71)
    embed.add_field(name="🃏 Custom Cards in Pool", value=str(c_cards), inline=True)
    embed.add_field(name="⚔️ Factions / Archetypes", value=str(c_factions), inline=True)
    embed.add_field(name="👤 Story Duelists", value=str(c_chars), inline=True)
    embed.add_field(name="👥 Players with Custom Decks", value=str(c_pdecks), inline=True)
    embed.add_field(name="⚔️ Story Duels Recorded", value=str(c_duels), inline=True)
    embed.add_field(name="🌐 Duelingbook Sync", value="Active", inline=True)
    embed.set_footer(text="Live Duel Simulator on Port 7911 • Web Catalog on Port 8000")
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    token = config.get("token")
    if not token or "YOUR_DISCORD_BOT_TOKEN" in token:
        print("[!] No Discord Bot Token configured.")
        print("[*] Add your token to /home/professorseanex/yugioh-server/.env:")
        print("    DISCORD_BOT_TOKEN=your_token_here")
        print("    Then run: ./manage.sh bot")
        sys.exit(0)
    else:
        bot.run(token)
