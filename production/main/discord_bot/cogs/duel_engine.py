#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Interactive Duel Simulation Engine
=============================================================================
Provides a fully interactive, in-chat Yu-Gi-Oh! duel engine featuring:
1. Turn-based state machine (8000 Life Points, Turn counter, Priority tracking).
2. Ranked (with ELO stakes) and Casual match modes.
3. Private ephemeral hand inspection (players only see their own secret cards).
4. Live Life Point calculation, damage logging, and win/loss declarations.
5. Telemetry integration recording card draws, deck performance, and ELO deltas.
6. Robust concurrency tracking via DuelManager for safe recovery & hot reloading.
=============================================================================
"""

import discord
from discord import app_commands, ui
from discord.ext import commands
import random
from typing import Any, Dict, List, Optional

from bot_config import BOT_CONFIG
from services.duel_service import duel_manager
from services.rating_service import RatingService
from services.card import CardService
from services.deck import DeckService
from production.main.logger import get_logger
from utils import (
    DuelBoard,
    render_duel_field_ascii,
    calculate_battle_damage,
    get_tribute_requirement
)

logger = get_logger("discord_bot.cogs.duel_engine")

_rating_service = RatingService()
_card_service = CardService()
_deck_service = DeckService()


# =============================================================================
# 1. DUEL SESSION STATE MACHINE
# =============================================================================

class DuelSession:
    """
    Encapsulates the live state of an active match between two Discord duelists.
    """

    def __init__(
        self,
        p1: discord.User,
        p2: discord.User,
        p1_deck: List[int],
        p2_deck: List[int],
        match_type: str = "RANKED",
        p1_deck_name: Optional[str] = None,
        p2_deck_name: Optional[str] = None,
    ):
        self.p1 = p1
        self.p2 = p2
        self.match_type = match_type.upper()
        self.deck_names = {p1.id: p1_deck_name, p2.id: p2_deck_name}
        self.lp = {p1.id: 8000, p2.id: 8000}

        # Keep original decks for post-match card telemetry
        self.original_decks = {p1.id: p1_deck.copy(), p2.id: p2_deck.copy()}
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
        self.boards = {
            p1.id: DuelBoard(p1.display_name),
            p2.id: DuelBoard(p2.display_name)
        }

        # Random starting turn player
        self.turn_player = random.choice([p1, p2])
        self.turn_count = 1
        self.duel_over = False
        self.winner: Optional[discord.User] = None
        self.match_result: Optional[dict] = None

    def draw_card(self, player_id: int) -> Optional[int]:
        """Draws 1 card from deck into hand. Returns card passcode or None if deck empty."""
        if self.decks[player_id]:
            c = self.decks[player_id].pop()
            self.hands[player_id].append(c)
            return c
        return None

    def mill_card(self, player_id: int) -> Optional[int]:
        """Sends top card from player's deck to Graveyard with RNG."""
        if self.decks[player_id]:
            c = self.decks[player_id].pop()
            self.gy[player_id].append(c)
            if player_id in self.boards:
                self.boards[player_id].send_to_gy(c)
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
            placeholder="e.g. Attack from The Great Kasutamaiza",
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
        reason_txt = self.reason.value or "Manual Adjustment"
        msg = f"❤️ **{target_user.display_name}** LP: {old_lp} ➔ **{new_lp}** ({sign}{val}) [{reason_txt}]"

        if new_lp <= 0:
            self.session.duel_over = True
            winner = self.session.p2 if self.target_player_id == self.session.p1.id else self.session.p1
            self.session.winner = winner
            msg += f"\n🏆 **DUEL CONCLUDED! {winner.mention} EMERGES VICTORIOUS!**"
            self.duel_view.disable_all()
            duel_manager.unregister_session(self.session)

            # Record match result and update ELO/card telemetry
            res = await _rating_service.record_duel_match(
                str(self.session.p1.id),
                str(self.session.p2.id),
                winner_id=str(winner.id),
                match_type=self.session.match_type,
                turns=self.session.turn_count,
                summary=f"{winner.display_name} reduced {target_user.display_name}'s LP to 0.",
                p1_deck=self.session.original_decks[self.session.p1.id],
                p2_deck=self.session.original_decks[self.session.p2.id],
                p1_name=self.session.p1.display_name,
                p2_name=self.session.p2.display_name,
                p1_deck_name=self.session.deck_names.get(self.session.p1.id),
                p2_deck_name=self.session.deck_names.get(self.session.p2.id),
            )
            self.session.match_result = res
            if self.session.match_type == "RANKED":
                p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
                p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
                msg += f"\n📈 **ELO Changes:** {self.session.p1.display_name} (`{p1_d}`) | {self.session.p2.display_name} (`{p2_d}`)"

        await interaction.response.edit_message(
            embed=self.duel_view.build_embed(last_action=msg),
            view=self.duel_view
        )


class SummonSelect(ui.Select):
    """Dropdown menu for choosing a monster from hand to summon with tribute checks."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", monster_cards: List[Dict[str, Any]]):
        self.session = session
        self.duel_view = duel_view
        self.cards_by_id = {str(c["id"]): c for c in monster_cards}
        options = []
        for c in monster_cards[:25]:
            req = get_tribute_requirement(c.get("level"))
            trib_text = f"{req} Tribute(s)" if req > 0 else "0 Tributes"
            options.append(
                discord.SelectOption(
                    label=c["name"][:100],
                    value=str(c["id"]),
                    description=f"Lv.{c.get('level', 4)} ⭐ | ATK {c.get('atk', 0)}/DEF {c.get('def', 0)} ({trib_text})"[:100],
                    emoji="⚡"
                )
            )
        super().__init__(placeholder="Select a monster to Normal Summon...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cid_str = self.values[0]
        c = self.cards_by_id.get(cid_str)
        if not c:
            await interaction.response.send_message("❌ Card not found.", ephemeral=True)
            return

        uid = interaction.user.id
        board = self.session.boards[uid]
        req_trib = get_tribute_requirement(c.get("level"))
        active_monsters = board.active_monsters

        if len(active_monsters) < req_trib:
            await interaction.response.send_message(
                f"❌ **{c['name']}** (Level {c.get('level', 4)} ⭐) requires **{req_trib} Tribute(s)**, but you only have **{len(active_monsters)}** monster(s) on field!",
                ephemeral=True
            )
            return

        # Tribute monsters if required
        tributed_names = []
        if req_trib > 0:
            for _ in range(req_trib):
                for i, m in enumerate(board.mmz):
                    if m is not None:
                        tributed_names.append(m["name"])
                        board.mmz[i] = None
                        board.send_to_gy(m["id"])
                        break

        # Place summoned monster into open MMZ slot
        slot = board.place_monster(c, position="ATK")
        if slot is None:
            await interaction.response.send_message("❌ All 5 Main Monster Zones are occupied!", ephemeral=True)
            return

        # Remove card from player hand
        cid_int = int(cid_str)
        if cid_int in self.session.hands[uid]:
            self.session.hands[uid].remove(cid_int)

        trib_note = f" (Tributed: {', '.join(tributed_names)})" if tributed_names else ""
        action_msg = f"⚡ **{interaction.user.display_name}** Normal Summoned **{c['name']}** (Level {c.get('level', 4)} ⭐ | ATK {c.get('atk', 0)}) into MMZ [{slot + 1}]!{trib_note}"

        await interaction.response.edit_message(content=f"✅ You summoned **{c['name']}** to MMZ [{slot + 1}]!", view=None)

        if self.duel_view.message:
            await self.duel_view.message.edit(
                embed=self.duel_view.build_embed(last_action=action_msg),
                view=self.duel_view
            )


class SummonView(ui.View):
    """Ephemeral view wrapper for monster summoning dropdown."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", monster_cards: List[Dict[str, Any]]):
        super().__init__(timeout=60)
        self.add_item(SummonSelect(session, duel_view, monster_cards))


class DuelView(ui.View):
    """
    Main interactive board view containing action buttons for hand inspection,
    card draws, LP adjustments, Normal Summons, Attacks, and turn transitions.
    """

    def __init__(self, session: DuelSession):
        super().__init__(timeout=1800)  # 30 minute match timeout
        self.session = session
        self.message: Optional[discord.Message] = None

    def disable_all(self):
        """Disables all action buttons upon duel completion."""
        for item in self.children:
            item.disabled = True

    def build_embed(self, last_action: str = "Duel in Progress") -> discord.Embed:
        """Constructs the match scoreboard embed."""
        p1 = self.session.p1
        p2 = self.session.p2

        mode_badge = "⚔️ [RANKED]" if self.session.match_type == "RANKED" else "🎮 [CASUAL]"
        embed = discord.Embed(
            title=f"{mode_badge} Duel: {p1.display_name} VS {p2.display_name}",
            description=f"**Turn {self.session.turn_count}** — Active Duelist: {self.session.turn_player.mention}\n\n**Latest Action:**\n{last_action}",
            color=0x9B59B6 if not self.session.duel_over else 0x10B981
        )

        p1_bar = "🟩" * max(1, self.session.lp[p1.id] // 1000)
        p2_bar = "🟩" * max(1, self.session.lp[p2.id] // 1000)
        p1_mmz = self.session.boards[p1.id].format_mmz_display()
        p2_mmz = self.session.boards[p2.id].format_mmz_display()

        embed.add_field(
            name=f"👤 {p1.display_name}",
            value=f"**LP:** {self.session.lp[p1.id]} {p1_bar}\n**Hand:** {len(self.session.hands[p1.id])} | **Deck:** {len(self.session.decks[p1.id])} | **GY:** {len(self.session.boards[p1.id].gy)}\n**MMZ:** {p1_mmz}",
            inline=True
        )
        embed.add_field(
            name=f"👤 {p2.display_name}",
            value=f"**LP:** {self.session.lp[p2.id]} {p2_bar}\n**Hand:** {len(self.session.hands[p2.id])} | **Deck:** {len(self.session.decks[p2.id])} | **GY:** {len(self.session.boards[p2.id].gy)}\n**MMZ:** {p2_mmz}",
            inline=True
        )

        if self.session.duel_over and self.session.match_result:
            res = self.session.match_result
            if self.session.match_type == "RANKED":
                p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
                p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
                embed.add_field(
                    name="🏅 Competitive Result",
                    value=f"• **{p1.display_name}**: `{res['p1_elo_before']}` ➔ **`{res['p1_elo_after']}`** ({p1_d})\n"
                          f"• **{p2.display_name}**: `{res['p2_elo_before']}` ➔ **`{res['p2_elo_after']}`** ({p2_d})",
                    inline=False
                )

        embed.set_footer(text="Hand: secret cards • Summon: play monster • Attack: battle • Field: live ASCII mat")
        return embed

    @ui.button(label="🎴 View Hand", style=discord.ButtonStyle.primary, row=0)
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

        cards = []
        for cid in hand_cids:
            c = await _card_service.get_card_by_query(str(cid))
            if c:
                cards.append(c)

        card_lines = []
        for i, c in enumerate(cards, 1):
            stat_str = f"ATK {c['atk']}/{c['def']}" if c['card_type'] == 'Monster' else f"{c['card_subtype'] or 'Normal'} {c['card_type']}"
            card_lines.append(f"**{i}. {c['name']}** [{stat_str}]\n*{c['effect_text'][:100]}...*")

        hand_embed = discord.Embed(
            title=f"🎴 Your Secret Hand ({len(cards)} Cards)",
            description="\n\n".join(card_lines) if card_lines else "*No card details found.*",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=hand_embed, ephemeral=True)

    @ui.button(label="🃏 Draw Card", style=discord.ButtonStyle.secondary, row=0)
    async def draw_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Draws a card from the deck for the active turn player with RNG."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ It is not your turn to draw.", ephemeral=True)
            return

        drawn = self.session.draw_card(uid)
        if not drawn:
            await interaction.response.send_message("❌ Deck out! No cards remaining in your deck.", ephemeral=True)
            return

        # Track draw telemetry
        await _card_service.track_card_draw(drawn)

        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🃏 **{interaction.user.display_name}** drew 1 card."),
            view=self
        )

    @ui.button(label="⏳ End Turn", style=discord.ButtonStyle.success, row=0)
    async def end_turn_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Passes turn priority to the opposing duelist and triggers turn draw."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can end the turn.", ephemeral=True)
            return

        self.session.turn_player = self.session.p2 if uid == self.session.p1.id else self.session.p1
        self.session.turn_count += 1

        next_uid = self.session.turn_player.id
        drawn = self.session.draw_card(next_uid)
        draw_txt = ""
        if drawn:
            await _card_service.track_card_draw(drawn)
            draw_txt = f" (Drawn 1 card automatically)"

        await interaction.response.edit_message(
            embed=self.build_embed(
                last_action=f"🔄 **Turn {self.session.turn_count} Begins**: Priority passed to {self.session.turn_player.mention}!{draw_txt}"
            ),
            view=self
        )

    @ui.button(label="❤️ -1000 LP", style=discord.ButtonStyle.danger, row=0)
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
            self.session.winner = winner
            action_msg += f"\n🏆 **{winner.mention} WINS THE MATCH!**"
            duel_manager.unregister_session(self.session)

            res = await _rating_service.record_duel_match(
                str(self.session.p1.id),
                str(self.session.p2.id),
                winner_id=str(winner.id),
                match_type=self.session.match_type,
                turns=self.session.turn_count,
                summary=f"{winner.display_name} defeated {interaction.user.display_name}.",
                p1_deck=self.session.original_decks[self.session.p1.id],
                p2_deck=self.session.original_decks[self.session.p2.id],
                p1_name=self.session.p1.display_name,
                p2_name=self.session.p2.display_name,
                p1_deck_name=self.session.deck_names.get(self.session.p1.id),
                p2_deck_name=self.session.deck_names.get(self.session.p2.id),
            )
            self.session.match_result = res
            if self.session.match_type == "RANKED":
                p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
                p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
                action_msg += f"\n📈 **ELO Changes:** {self.session.p1.display_name} (`{p1_d}`) | {self.session.p2.display_name} (`{p2_d}`)"

        await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)

    @ui.button(label="❤️ Custom LP", style=discord.ButtonStyle.secondary, row=0)
    async def custom_lp_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Opens modal for custom LP damage or recovery."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return
        await interaction.response.send_modal(LPModal(self.session, uid, self))

    @ui.button(label="🪙 Coin Toss", style=discord.ButtonStyle.secondary, row=1)
    async def coin_toss_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Simulates Yu-Gi-Oh! coin flip (Heads or Tails)."""
        flip = random.choice(["🪙 HEADS", "🪙 TAILS"])
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🪙 **{interaction.user.display_name}** tossed a coin: **{flip}**!"),
            view=self
        )

    @ui.button(label="🎲 Roll d6", style=discord.ButtonStyle.secondary, row=1)
    async def roll_dice_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Rolls a six-sided die for effect resolution."""
        result = random.randint(1, 6)
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🎲 **{interaction.user.display_name}** rolled a die: **[{result}]**!"),
            view=self
        )

    @ui.button(label="🌀 Mill 1 Card", style=discord.ButtonStyle.secondary, row=1)
    async def mill_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Sends top card of deck to Graveyard with RNG."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return

        drawn = self.session.mill_card(uid)
        if not drawn:
            await interaction.response.send_message("❌ Your deck is empty!", ephemeral=True)
            return

        c = await _card_service.get_card_by_query(str(drawn))
        cname = c["name"] if c else f"Card #{drawn}"
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🌀 **{interaction.user.display_name}** milled top card to GY: **{cname}**!"),
            view=self
        )

    @ui.button(label="🗺️ Duel Field", style=discord.ButtonStyle.secondary, row=1)
    async def field_view_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Displays full ASCII playmat of the live board layout and zones."""
        p1 = self.session.p1
        p2 = self.session.p2
        ascii_mat = render_duel_field_ascii(
            player_board=self.session.boards[p1.id],
            opp_board=self.session.boards[p2.id],
            p_name=p1.display_name,
            opp_name=p2.display_name,
            p_lp=self.session.lp[p1.id],
            opp_lp=self.session.lp[p2.id],
            p_hand=len(self.session.hands[p1.id]),
            opp_hand=len(self.session.hands[p2.id]),
            p_deck=len(self.session.decks[p1.id]),
            opp_deck=len(self.session.decks[p2.id])
        )
        embed = discord.Embed(
            title="🗺️ Live Duel Field Playmat (Master Rule)",
            description=f"```text\n{ascii_mat}\n```",
            color=0x3498DB
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="⚡ Summon", style=discord.ButtonStyle.primary, row=2)
    async def summon_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Allows active turn player to Normal Summon a monster from hand with Level/Tribute checks."""
        self.message = interaction.message
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can summon monsters.", ephemeral=True)
            return

        hand_cids = self.session.hands[uid]
        if not hand_cids:
            await interaction.response.send_message("📭 Your hand is empty!", ephemeral=True)
            return

        monster_cards = []
        for cid in hand_cids:
            c = await _card_service.get_card_by_query(str(cid))
            if c and c.get("card_type") == "Monster":
                monster_cards.append(c)

        if not monster_cards:
            await interaction.response.send_message("❌ You have no Monster cards in hand to summon.", ephemeral=True)
            return

        view = SummonView(self.session, self, monster_cards)
        await interaction.response.send_message(
            "⚡ **Select a monster to Normal Summon to your Main Monster Zone:**",
            view=view,
            ephemeral=True
        )

    @ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, row=2)
    async def attack_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Declares an attack using battle damage calculations and position rules."""
        self.message = interaction.message
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can declare attacks.", ephemeral=True)
            return

        my_board = self.session.boards[uid]
        my_atk_monsters = [m for m in my_board.mmz if m and m.get("position") == "ATK"]
        if not my_atk_monsters:
            await interaction.response.send_message(
                "❌ You have no monsters in Attack Position to declare an attack with! (Use `⚡ Summon` first).",
                ephemeral=True
            )
            return

        opp_user = self.session.p2 if uid == self.session.p1.id else self.session.p1
        opp_uid = opp_user.id
        opp_board = self.session.boards[opp_uid]
        opp_monsters = [m for m in opp_board.mmz if m is not None]

        attacker = max(my_atk_monsters, key=lambda m: m.get("atk", 0))

        if not opp_monsters:
            # DIRECT ATTACK
            battle_res = calculate_battle_damage(attacker, defender=None, is_direct=True)
            dmg = battle_res["damage"]
            old_lp = self.session.lp[opp_uid]
            new_lp = max(0, old_lp - dmg)
            self.session.lp[opp_uid] = new_lp
            action_msg = f"{battle_res['summary']}\n❤️ **{opp_user.display_name}** LP: {old_lp} ➔ **{new_lp}** (-{dmg})"

            if new_lp <= 0:
                self.session.duel_over = True
                self.disable_all()
                self.session.winner = interaction.user
                action_msg += f"\n🏆 **{interaction.user.mention} WINS THE MATCH!**"
                duel_manager.unregister_session(self.session)

                res = await _rating_service.record_duel_match(
                    str(self.session.p1.id),
                    str(self.session.p2.id),
                    winner_id=str(interaction.user.id),
                    match_type=self.session.match_type,
                    turns=self.session.turn_count,
                    summary=f"{interaction.user.display_name} won by direct attack.",
                    p1_deck=self.session.original_decks[self.session.p1.id],
                    p2_deck=self.session.original_decks[self.session.p2.id],
                    p1_name=self.session.p1.display_name,
                    p2_name=self.session.p2.display_name,
                    p1_deck_name=self.session.deck_names.get(self.session.p1.id),
                    p2_deck_name=self.session.deck_names.get(self.session.p2.id),
                )
                self.session.match_result = res
                if self.session.match_type == "RANKED":
                    p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
                    p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
                    action_msg += f"\n📈 **ELO Changes:** {self.session.p1.display_name} (`{p1_d}`) | {self.session.p2.display_name} (`{p2_d}`)"

            await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)
            return

        # Opponent has monsters: target first defender
        target = opp_monsters[0]
        battle_res = calculate_battle_damage(attacker, defender=target, is_direct=False)
        dmg = battle_res["damage"]

        if battle_res["defender_destroyed"]:
            for i, m in enumerate(opp_board.mmz):
                if m is target:
                    opp_board.mmz[i] = None
                    opp_board.send_to_gy(target["id"])
                    break

        if battle_res["attacker_destroyed"]:
            for i, m in enumerate(my_board.mmz):
                if m is attacker:
                    my_board.mmz[i] = None
                    my_board.send_to_gy(attacker["id"])
                    break

        damaged_uid = None
        damaged_user = None
        if battle_res["damaged_side"] == "defender":
            damaged_uid = opp_uid
            damaged_user = opp_user
        elif battle_res["damaged_side"] == "attacker":
            damaged_uid = uid
            damaged_user = interaction.user

        action_msg = battle_res["summary"]
        if damaged_uid is not None and dmg > 0:
            old_lp = self.session.lp[damaged_uid]
            new_lp = max(0, old_lp - dmg)
            self.session.lp[damaged_uid] = new_lp
            action_msg += f"\n❤️ **{damaged_user.display_name}** LP: {old_lp} ➔ **{new_lp}** (-{dmg})"

            if new_lp <= 0:
                self.session.duel_over = True
                self.disable_all()
                winner = interaction.user if damaged_uid == opp_uid else opp_user
                self.session.winner = winner
                action_msg += f"\n🏆 **{winner.mention} WINS THE MATCH!**"
                duel_manager.unregister_session(self.session)

                res = await _rating_service.record_duel_match(
                    str(self.session.p1.id),
                    str(self.session.p2.id),
                    winner_id=str(winner.id),
                    match_type=self.session.match_type,
                    turns=self.session.turn_count,
                    summary=f"{winner.display_name} won through battle combat.",
                    p1_deck=self.session.original_decks[self.session.p1.id],
                    p2_deck=self.session.original_decks[self.session.p2.id],
                    p1_name=self.session.p1.display_name,
                    p2_name=self.session.p2.display_name,
                    p1_deck_name=self.session.deck_names.get(self.session.p1.id),
                    p2_deck_name=self.session.deck_names.get(self.session.p2.id),
                )
                self.session.match_result = res
                if self.session.match_type == "RANKED":
                    p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
                    p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
                    action_msg += f"\n📈 **ELO Changes:** {self.session.p1.display_name} (`{p1_d}`) | {self.session.p2.display_name} (`{p2_d}`)"

        await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)

    @ui.button(label="🏳️ Surrender", style=discord.ButtonStyle.danger, row=1)
    async def surrender_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Concedes the match to the opponent."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return

        self.session.duel_over = True
        self.disable_all()
        winner = self.session.p2 if uid == self.session.p1.id else self.session.p1
        surrendering_user = interaction.user
        self.session.winner = winner
        duel_manager.unregister_session(self.session)

        action_msg = f"🏳️ **{surrendering_user.display_name}** surrendered! 🏆 **{winner.mention} WINS!**"

        res = await _rating_service.record_duel_match(
            str(self.session.p1.id),
            str(self.session.p2.id),
            winner_id=str(winner.id),
            match_type=self.session.match_type,
            turns=self.session.turn_count,
            summary=f"{surrendering_user.display_name} surrendered to {winner.display_name}.",
            p1_deck=self.session.original_decks[self.session.p1.id],
            p2_deck=self.session.original_decks[self.session.p2.id],
            p1_name=self.session.p1.display_name,
            p2_name=self.session.p2.display_name,
            p1_deck_name=self.session.deck_names.get(self.session.p1.id),
            p2_deck_name=self.session.deck_names.get(self.session.p2.id),
        )
        self.session.match_result = res
        if self.session.match_type == "RANKED":
            p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
            p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
            action_msg += f"\n📈 **ELO Changes:** {self.session.p1.display_name} (`{p1_d}`) | {self.session.p2.display_name} (`{p2_d}`)"

        await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)


# =============================================================================
# 3. CHALLENGE INVITATION VIEW
# =============================================================================

class ChallengeView(ui.View):
    """Invitation prompt giving the challenged user Ranked, Casual, or Decline choices."""

    def __init__(self, challenger: discord.User, challenged: discord.User):
        super().__init__(timeout=120)
        self.challenger = challenger
        self.challenged = challenged

    async def _start_duel(self, interaction: discord.Interaction, match_type: str):
        if interaction.user.id != self.challenged.id:
            await interaction.response.send_message("❌ Only the challenged duelist can respond.", ephemeral=True)
            return

        p1_deck = await _deck_service.get_player_card_ids(str(self.challenger.id))
        p2_deck = await _deck_service.get_player_card_ids(str(self.challenged.id))

        # Fallback to Set 1 pool if player deck is under 5 cards
        if len(p1_deck) < 5 or len(p2_deck) < 5:
            all_cards = await _card_service.get_all_cards()
            fallback = [c["id"] for c in all_cards] * 2
            if len(p1_deck) < 5:
                p1_deck = fallback.copy()
            if len(p2_deck) < 5:
                p2_deck = fallback.copy()

        p1_deck_name = await _deck_service.find_matching_saved_deck(str(self.challenger.id))
        p2_deck_name = await _deck_service.find_matching_saved_deck(str(self.challenged.id))

        session = DuelSession(
            self.challenger,
            self.challenged,
            p1_deck,
            p2_deck,
            match_type=match_type,
            p1_deck_name=p1_deck_name,
            p2_deck_name=p2_deck_name
        )
        duel_manager.register_session(self.challenger.id, self.challenged.id, session)

        duel_view = DuelView(session)
        mode_label = "⚔️ RANKED MATCH" if match_type == "RANKED" else "🎮 CASUAL MATCH"
        embed = duel_view.build_embed(
            last_action=f"{mode_label} begins! Destiny decides: {session.turn_player.mention} goes first!"
        )
        await interaction.response.edit_message(content=None, embed=embed, view=duel_view)

    @ui.button(label="⚔️ Accept (Ranked)", style=discord.ButtonStyle.success)
    async def accept_ranked(self, interaction: discord.Interaction, button: ui.Button):
        await self._start_duel(interaction, "RANKED")

    @ui.button(label="🎮 Accept (Casual)", style=discord.ButtonStyle.primary)
    async def accept_casual(self, interaction: discord.Interaction, button: ui.Button):
        await self._start_duel(interaction, "CASUAL")

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
# 4. DUEL COG COMMANDS
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
            await interaction.response.send_message("❌ You cannot challenge a bot to a live duel. Use `/story` for NPC duels!", ephemeral=True)
            return

        if duel_manager.is_user_dueling(interaction.user.id):
            await interaction.response.send_message(
                "❌ You already have an active duel running. Finish or surrender your current duel first.",
                ephemeral=True
            )
            return

        if duel_manager.is_user_dueling(opponent.id):
            await interaction.response.send_message(
                f"❌ {opponent.display_name} is currently engaged in another duel.",
                ephemeral=True
            )
            return

        view = ChallengeView(interaction.user, opponent)
        await interaction.response.send_message(
            f"⚔️ {opponent.mention}, you have been challenged to a **Yu-Gi-Oh! Custom Card Duel** by {interaction.user.mention}!\n*Choose Ranked for ELO stakes or Casual to practice:*",
            view=view
        )

    @app_commands.command(name="duel_manual", description="Manual PvP duel mode against another player (Ranked with ELO or Casual)")
    @app_commands.describe(opponent="The duelist you wish to challenge")
    async def duel_manual_command(self, interaction: discord.Interaction, opponent: discord.User):
        """Direct alias for manual PvP duels."""
        await self.duel_command(interaction, opponent)


async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(DuelEngineCog(bot))

