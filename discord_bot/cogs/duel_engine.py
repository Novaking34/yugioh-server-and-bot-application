#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Interactive Duel Simulation Engine
=============================================================================
Provides a fully interactive, in-chat Yu-Gi-Oh! duel engine featuring:
1. Turn-based state machine (8000 Life Points, Turn counter, Priority tracking).
2. Private ephemeral hand inspection (players only see their own secret cards).
3. Live Life Point calculation, damage logging, and win/loss declarations.
4. Dice rolling, card draw triggers, and mutual turn management.
5. Integration with player active decks from the Story Database.
=============================================================================
"""

import discord
from discord import app_commands, ui
from discord.ext import commands
import aiosqlite
import random
from typing import Dict, List, Optional

from config import BOT_CONFIG


# =============================================================================
# 1. DUEL SESSION STATE MACHINE
# =============================================================================

class DuelSession:
    """
    Encapsulates the live state of an active match between two Discord duelists.
    """

    def __init__(self, p1: discord.User, p2: discord.User, p1_deck: List[int], p2_deck: List[int]):
        self.p1 = p1
        self.p2 = p2
        self.lp = {p1.id: 8000, p2.id: 8000}
        
        # Clone and shuffle player decks
        self.decks = {p1.id: p1_deck.copy(), p2.id: p2_deck.copy()}
        random.shuffle(self.decks[p1.id])
        random.shuffle(self.decks[p2.id])

        # Opening Hand: Deal 5 cards each
        self.hands = {
            p1.id: [self.decks[p1.id].pop() for _ in range(min(5, len(self.decks[p1.id])))],
            p2.id: [self.decks[p2.id].pop() for _ in range(min(5, len(self.decks[p2.id])))]
        }
        self.fields = {p1.id: {"monsters": [], "spells": []}, p2.id: {"monsters": [], "spells": []}}
        self.gy = {p1.id: [], p2.id: []}

        # Random starting turn player
        self.turn_player = random.choice([p1, p2])
        self.turn_count = 1
        self.duel_over = False

    def draw_card(self, player_id: int) -> Optional[int]:
        """Draws 1 card from deck into hand. Returns card passcode or None if deck empty."""
        if self.decks[player_id]:
            c = self.decks[player_id].pop()
            self.hands[player_id].append(c)
            return c
        return None


# =============================================================================
# 2. UI MODALS & INTERACTION COMPONENTS
# =============================================================================

class LPModal(ui.Modal, title="Adjust Life Points"):
    """Modal dialog allowing players to input arbitrary damage or healing."""

    def __init__(self, session: DuelSession, target_player_id: int, duel_view: "DuelView"):
        super().__init__()
        self.session = session
        self.target_player_id = target_player_id
        self.duel_view = duel_view

        self.amount = ui.TextInput(
            label="Amount (+ to heal, - to damage)",
            placeholder="e.g. -1000 or +800",
            max_length=6
        )
        self.reason = ui.TextInput(
            label="Reason / Battle Details",
            placeholder="e.g. Direct attack from Sol Invictus",
            required=False,
            max_length=100
        )
        self.add_item(self.amount)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.amount.value.replace("+", "").strip())
        except ValueError:
            await interaction.response.send_message("❌ Invalid integer value.", ephemeral=True)
            return

        old_lp = self.session.lp[self.target_player_id]
        new_lp = max(0, old_lp + val)
        self.session.lp[self.target_player_id] = new_lp

        target_user = self.session.p1 if self.target_player_id == self.session.p1.id else self.session.p2
        sign = "+" if val >= 0 else ""
        reason_txt = self.reason.value or 'Manual Adjustment'
        msg = f"❤️ **{target_user.display_name}** LP: {old_lp} ➔ **{new_lp}** ({sign}{val}) [{reason_txt}]"

        if new_lp <= 0:
            self.session.duel_over = True
            winner = self.session.p2 if self.target_player_id == self.session.p1.id else self.session.p1
            msg += f"\n🏆 **DUEL CONCLUDED! {winner.mention} EMERGES VICTORIOUS!**"
            self.duel_view.disable_all()

        await interaction.response.edit_message(
            embed=self.duel_view.build_embed(last_action=msg),
            view=self.duel_view
        )


class DuelView(ui.View):
    """
    Main interactive board view containing action buttons for hand inspection,
    card draws, LP adjustments, and turn transitions.
    """

    def __init__(self, session: DuelSession):
        super().__init__(timeout=1800)  # 30 minute match timeout
        self.session = session
        self.db_path = BOT_CONFIG["db_path"]

    def disable_all(self):
        """Disables all action buttons upon duel completion."""
        for item in self.children:
            item.disabled = True

    def build_embed(self, last_action: str = "Duel in Progress") -> discord.Embed:
        """Constructs the high-level match scoreboard embed."""
        p1 = self.session.p1
        p2 = self.session.p2

        embed = discord.Embed(
            title=f"⚔️ Yu-Gi-Oh! Duel: {p1.display_name} VS {p2.display_name}",
            description=f"**Turn {self.session.turn_count}** — Active Duelist: {self.session.turn_player.mention}\n\n**Latest Action:**\n{last_action}",
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
        embed.set_footer(text="Click 'View Hand' for private secret cards • LP buttons log combat damage")
        return embed

    @ui.button(label="🎴 View Hand", style=discord.ButtonStyle.primary)
    async def view_hand_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Displays secret hand privately to the clicking player using an ephemeral embed."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            await interaction.response.send_message("❌ You are a spectator in this duel.", ephemeral=True)
            return

        hand_cids = self.session.hands[uid]
        if not hand_cids:
            await interaction.response.send_message("📭 Your hand is currently empty.", ephemeral=True)
            return

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            placeholders = ",".join("?" for _ in hand_cids)
            cur = await db.execute(
                f"SELECT id, name, card_type, card_subtype, atk, def, effect_text FROM custom_cards WHERE id IN ({placeholders})",
                hand_cids
            )
            cards = await cur.fetchall()

        card_lines = []
        for i, c in enumerate(cards, 1):
            stat_str = f"ATK {c['atk']}/{c['def']}" if c['card_type'] == 'Monster' else f"{c['card_subtype'] or 'Normal'} {c['card_type']}"
            card_lines.append(f"**{i}. {c['name']}** [{stat_str}]\n*{c['effect_text'][:110]}...*")

        hand_embed = discord.Embed(
            title=f"🎴 Your Secret Hand ({len(cards)} Cards)",
            description="\n\n".join(card_lines),
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=hand_embed, ephemeral=True)

    @ui.button(label="🃏 Draw Card", style=discord.ButtonStyle.secondary)
    async def draw_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Draws a card from the deck for the active turn player."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ It is not your turn to draw.", ephemeral=True)
            return

        drawn = self.session.draw_card(uid)
        if not drawn:
            await interaction.response.send_message("❌ Deck out! No cards remaining in your deck.", ephemeral=True)
            return

        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🃏 **{interaction.user.display_name}** drew 1 card."),
            view=self
        )

    @ui.button(label="❤️ -1000 LP", style=discord.ButtonStyle.danger)
    async def minus_1000_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Quick button to deal 1000 damage to the clicking player."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return

        self.session.lp[uid] = max(0, self.session.lp[uid] - 1000)
        action_msg = f"💥 **{interaction.user.display_name}** took 1000 damage! (Remaining LP: {self.session.lp[uid]})"

        if self.session.lp[uid] == 0:
            self.session.duel_over = True
            self.disable_all()
            winner = self.session.p2 if uid == self.session.p1.id else self.session.p1
            action_msg += f"\n🏆 **{winner.mention} WINS THE MATCH!**"

        await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)

    @ui.button(label="❤️ Custom LP", style=discord.ButtonStyle.secondary)
    async def custom_lp_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Opens modal for custom LP damage or recovery."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return
        await interaction.response.send_modal(LPModal(self.session, uid, self))

    @ui.button(label="🎲 Roll d6", style=discord.ButtonStyle.secondary)
    async def roll_dice_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Rolls a six-sided die for effect resolution."""
        result = random.randint(1, 6)
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🎲 **{interaction.user.display_name}** rolled a die: **[{result}]**!"),
            view=self
        )

    @ui.button(label="⏳ End Turn", style=discord.ButtonStyle.success)
    async def end_turn_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Passes turn priority to the opposing duelist and triggers turn draw."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can end the turn.", ephemeral=True)
            return

        # Swap turn player
        self.session.turn_player = self.session.p2 if uid == self.session.p1.id else self.session.p1
        self.session.turn_count += 1

        # Automatic normal draw for new turn
        drawn = self.session.draw_card(self.session.turn_player.id)
        draw_note = " (DREW 1 CARD)" if drawn else " (DECK OUT)"

        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"⏳ **Turn passed!** It is now {self.session.turn_player.mention}'s turn{draw_note}."),
            view=self
        )

    @ui.button(label="🏳️ Concede", style=discord.ButtonStyle.danger)
    async def concede_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Concedes the duel immediately."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return

        winner = self.session.p2 if uid == self.session.p1.id else self.session.p1
        self.session.duel_over = True
        self.disable_all()
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🏳️ **{interaction.user.display_name} has surrendered!**\n🏆 **{winner.mention} WINS!**"),
            view=self
        )


class ChallengeView(ui.View):
    """Initial invitation prompt prompting challenged duelist to Accept or Decline."""

    def __init__(self, challenger: discord.User, challenged: discord.User):
        super().__init__(timeout=120)
        self.challenger = challenger
        self.challenged = challenged
        self.db_path = BOT_CONFIG["db_path"]

    @ui.button(label="⚔️ Accept Challenge", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.challenged.id:
            await interaction.response.send_message("❌ Only the challenged duelist can accept.", ephemeral=True)
            return

        # Fetch decks from database
        async with aiosqlite.connect(self.db_path) as db:
            async def get_player_deck(uid: int) -> List[int]:
                cur = await db.execute("SELECT card_id, quantity FROM player_decks WHERE user_id = ?", (str(uid),))
                rows = await cur.fetchall()
                cards = []
                for cid, qty in rows:
                    cards.extend([cid] * qty)
                return cards

            p1_deck = await get_player_deck(self.challenger.id)
            p2_deck = await get_player_deck(self.challenged.id)

            # Fallback to general pool if deck is smaller than 5 cards
            if len(p1_deck) < 5 or len(p2_deck) < 5:
                cur = await db.execute("SELECT id FROM custom_cards LIMIT 20")
                sample_pool = [r[0] for r in await cur.fetchall()] * 2
                if len(p1_deck) < 5:
                    p1_deck = sample_pool.copy()
                if len(p2_deck) < 5:
                    p2_deck = sample_pool.copy()

        session = DuelSession(self.challenger, self.challenged, p1_deck, p2_deck)
        duel_view = DuelView(session)
        embed = duel_view.build_embed(
            last_action=f"⚔️ Challenge accepted! Destiny decides: {session.turn_player.mention} goes first!"
        )
        await interaction.response.edit_message(content=None, embed=embed, view=duel_view)

    @ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.challenged.id:
            await interaction.response.send_message("❌ Only the challenged duelist can decline.", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"🚫 {self.challenged.display_name} declined the duel challenge.",
            view=None
        )


# =============================================================================
# 3. DUEL COG COMMANDS
# =============================================================================

class DuelEngineCog(commands.Cog, name="DuelEngine"):
    """Commands for initiating live Discord duels."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="duel", description="Challenge another player to a live Yu-Gi-Oh! duel on Discord")
    @app_commands.describe(opponent="The user you wish to duel")
    async def duel_command(self, interaction: discord.Interaction, opponent: discord.User):
        """Initiates a match invitation with action buttons."""
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ You cannot duel yourself!", ephemeral=True)
            return
        if opponent.bot:
            await interaction.response.send_message("❌ You cannot challenge a bot to a live duel.", ephemeral=True)
            return

        view = ChallengeView(interaction.user, opponent)
        await interaction.response.send_message(
            f"⚔️ {opponent.mention}, you have been challenged to a **Yu-Gi-Oh! Story Duel** by {interaction.user.mention}!\n*Do you accept the call to duel?*",
            view=view
        )


async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(DuelEngineCog(bot))
