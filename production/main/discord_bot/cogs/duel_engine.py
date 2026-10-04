#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.cogs.duel_engine
Description:
    Interactive Live Yu-Gi-Oh! Duel Simulation Engine & Match Gateway.
    Provides complete Master Rule 2020 duel interaction:
    1. Turn-based state machine with 6 formal phases (DRAW -> STANDBY -> MAIN 1 -> BATTLE -> MAIN 2 -> END).
    2. Ranked (with ELO stakes) and Casual match modes.
    3. Private ephemeral hand inspection and secret card play.
    4. Normal Summoning (Face-up ATK) & Monster Setting (Face-down DEF) with Level/Tribute checks.
    5. Spell & Trap Card Setting to the 5 Spell & Trap Zones (STZ).
    6. Battle Position Switching (ATK <-> DEF, Flip Summon SET -> ATK).
    7. Targeted Monster Combat and Direct Attacks with Master Rule damage calculations.
    8. Life Point tracking, Deck Out detection, natural RNG, and rating telemetry integration.
    9. Concurrency isolation via DuelManager.

Architectural Classification:
    Layer 3 (L3) - Presentation & Discord Gateway Cog
    Subsystem: Duel Management & Interactive Matchmaking
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Layered Package Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Discord & UI Primitives
# -----------------------------------------------------------------------------
import random
from typing import Any, Dict, List, Optional, Tuple

import discord
from discord import app_commands, ui
from discord.ext import commands

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Services & Domain Subsystems
# -----------------------------------------------------------------------------
from bot_config import BOT_CONFIG
from services.duel import (
    DuelService,
    DuelManager,
    DuelSession,
    duel_service,
    duel_manager,
)
from services.duel.foundation import (
    DEFAULT_STARTING_LP,
    MATCH_TYPE_CASUAL,
    MATCH_TYPE_RANKED,
    PHASE_BATTLE,
    PHASE_DRAW,
    PHASE_END,
    PHASE_MAIN_1,
    PHASE_MAIN_2,
    PHASE_STANDBY,
)
from services.card import CardService
from services.deck import DeckService, is_extra_deck_card
from services.rating import RatingService

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Foundation Constants & Mechanics
# -----------------------------------------------------------------------------
from utils import (
    DuelBoard,
    render_duel_field_ascii,
    calculate_battle_damage,
    get_tribute_requirement,
    build_board_guide_embed,
)
from production.main.logger import get_logger

# -----------------------------------------------------------------------------
# Sub-Block 2.4: System Logger & Singletons
# -----------------------------------------------------------------------------
logger = get_logger("discord_bot.cogs.duel_engine")

_rating_service = RatingService()
_card_service = CardService()
_deck_service = DeckService()


# =============================================================================
# BLOCK 3: BODY BLOCK (UI Modals, Interactive Views & Commands)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: UI Modals & Interaction Components
# -----------------------------------------------------------------------------

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
            placeholder="e.g. Effect damage or direct strike",
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

        old_lp, new_lp, is_concluded = self.session.adjust_lp(
            self.target_player_id,
            delta=val,
            reason=self.reason.value or "Manual Adjustment"
        )

        target_user = self.session.p1 if self.target_player_id == self.session.p1.id else self.session.p2
        sign = "+" if val >= 0 else ""
        reason_txt = self.reason.value or "Manual Adjustment"
        msg = f"❤️ **{target_user.display_name}** LP: {old_lp} ➔ **{new_lp}** ({sign}{val}) [{reason_txt}]"

        if is_concluded:
            winner = self.session.winner or (self.session.p2 if self.target_player_id == self.session.p1.id else self.session.p1)
            await self.duel_view._handle_duel_conclusion(
                winner=winner,
                summary=f"{target_user.display_name}'s LP reached 0.",
                interaction=interaction
            )
            return

        await interaction.response.edit_message(
            embed=self.duel_view.build_embed(last_action=msg),
            view=self.duel_view
        )


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Selection Menus & Ephemeral Dialogs
# -----------------------------------------------------------------------------

class SummonSelect(ui.Select):
    """Dropdown menu for choosing a monster from hand to Normal Summon or Set."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", monster_cards: List[Dict[str, Any]]):
        self.session = session
        self.duel_view = duel_view
        self.cards_by_id: Dict[str, Dict[str, Any]] = {str(c["id"]): c for c in monster_cards}

        options = []
        for c in monster_cards[:12]:
            cid = str(c["id"])
            req = get_tribute_requirement(c.get("level"))
            trib_str = f"{req} Tribute(s)" if req > 0 else "0 Tributes"
            # Summon in ATK
            options.append(
                discord.SelectOption(
                    label=f"⚔️ Summon {c['name'][:75]}",
                    value=f"{cid}:ATK",
                    description=f"Lv.{c.get('level', 4)} ⭐ | ATK {c.get('atk', 0)}/DEF {c.get('def', 0)} ({trib_str})"[:100],
                    emoji="⚡"
                )
            )
            # Set in DEF
            options.append(
                discord.SelectOption(
                    label=f"🛡️ Set {c['name'][:80]}",
                    value=f"{cid}:SET",
                    description=f"Face-down Defense ({trib_str})"[:100],
                    emoji="🎴"
                )
            )

        super().__init__(placeholder="Select a monster to Normal Summon or Set...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        cid_str, pos = val.split(":")
        c = self.cards_by_id.get(cid_str)
        if not c:
            await interaction.response.send_message("❌ Card not found.", ephemeral=True)
            return

        uid = interaction.user.id
        if self.session.normal_summon_used.get(uid, False):
            await interaction.response.send_message(
                "❌ You have already performed your Normal Summon / Set this turn! (Master Rule allows 1 per turn).",
                ephemeral=True
            )
            return

        board = self.session.boards[uid]
        if not board.has_available_mmz():
            await interaction.response.send_message("❌ All 5 Main Monster Zones are occupied!", ephemeral=True)
            return

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

        # Place into open MMZ
        slot = board.summon_monster(c, position=pos)
        if slot is None:
            await interaction.response.send_message("❌ Could not place monster into MMZ.", ephemeral=True)
            return

        # Remove from hand
        cid_int = int(cid_str)
        if cid_int in self.session.hands[uid]:
            self.session.hands[uid].remove(cid_int)

        self.session.normal_summon_used[uid] = True
        trib_note = f" (Tributed: {', '.join(tributed_names)})" if tributed_names else ""
        if pos == "SET":
            action_msg = f"🛡️ **{interaction.user.display_name}** Set a monster face-down in MMZ [{slot + 1}]!{trib_note}"
            confirm_msg = f"✅ You Set **{c['name']}** face-down in MMZ [{slot + 1}]!"
        else:
            action_msg = f"⚡ **{interaction.user.display_name}** Normal Summoned **{c['name']}** (Level {c.get('level', 4)} ⭐ | ATK {c.get('atk', 0)}) into MMZ [{slot + 1}]!{trib_note}"
            confirm_msg = f"✅ You summoned **{c['name']}** in Attack Position into MMZ [{slot + 1}]!"

        await interaction.response.edit_message(content=confirm_msg, view=None)
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


class SpellTrapSelect(ui.Select):
    """Dropdown menu for choosing a Spell or Trap card from hand to Set in STZ."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", st_cards: List[Dict[str, Any]]):
        self.session = session
        self.duel_view = duel_view
        self.cards_by_id = {str(c["id"]): c for c in st_cards}

        options = []
        for c in st_cards[:25]:
            cid = str(c["id"])
            subtype = c.get("card_subtype") or "Normal"
            options.append(
                discord.SelectOption(
                    label=c["name"][:100],
                    value=cid,
                    description=f"{subtype} {c.get('card_type', 'Spell')} Card"[:100],
                    emoji="✨" if c.get("card_type") == "Spell" else "🛡️"
                )
            )
        super().__init__(placeholder="Select a Spell / Trap to Set in STZ...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cid_str = self.values[0]
        c = self.cards_by_id.get(cid_str)
        if not c:
            await interaction.response.send_message("❌ Card not found.", ephemeral=True)
            return

        uid = interaction.user.id
        board = self.session.boards[uid]
        if not board.has_available_stz():
            await interaction.response.send_message("❌ All 5 Spell & Trap Zones are occupied!", ephemeral=True)
            return

        slot = board.play_spell_or_trap(c, state="SET")
        if slot is None:
            await interaction.response.send_message("❌ Could not place card into STZ.", ephemeral=True)
            return

        cid_int = int(cid_str)
        if cid_int in self.session.hands[uid]:
            self.session.hands[uid].remove(cid_int)

        action_msg = f"✨ **{interaction.user.display_name}** Set 1 card face-down into Spell & Trap Zone [{slot + 1}]!"
        await interaction.response.edit_message(content=f"✅ You Set **{c['name']}** into STZ [{slot + 1}]!", view=None)

        if self.duel_view.message:
            await self.duel_view.message.edit(
                embed=self.duel_view.build_embed(last_action=action_msg),
                view=self.duel_view
            )


class SpellTrapView(ui.View):
    """Ephemeral view wrapper for Spell/Trap card setting dropdown."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", st_cards: List[Dict[str, Any]]):
        super().__init__(timeout=60)
        self.add_item(SpellTrapSelect(session, duel_view, st_cards))


class PositionChangeSelect(ui.Select):
    """Dropdown menu to switch a monster's battle position or Flip Summon."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", monsters_on_field: List[Tuple[int, Dict[str, Any]]]):
        self.session = session
        self.duel_view = duel_view
        self.monsters_by_slot = {str(slot): m for slot, m in monsters_on_field}

        options = []
        for slot, m in monsters_on_field:
            curr_pos = m.get("position", "ATK")
            if curr_pos == "ATK":
                target_pos = "DEF"
                label = f"🛡️ Switch {m['name'][:60]} to Defense"
                desc = f"Zone [{slot + 1}] — Change from ATK to DEF ({m.get('def', 0)} DEF)"
            elif curr_pos == "DEF":
                target_pos = "ATK"
                label = f"⚔️ Switch {m['name'][:60]} to Attack"
                desc = f"Zone [{slot + 1}] — Change from DEF to ATK ({m.get('atk', 0)} ATK)"
            else:  # SET
                target_pos = "ATK"
                label = f"✨ Flip Summon {m['name'][:60]}"
                desc = f"Zone [{slot + 1}] — Flip face-up into Attack Position"

            options.append(
                discord.SelectOption(
                    label=label[:100],
                    value=f"{slot}:{target_pos}",
                    description=desc[:100],
                    emoji="🔄"
                )
            )
        super().__init__(placeholder="Select a monster to change position...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        slot_str, new_pos = self.values[0].split(":")
        slot = int(slot_str)
        uid = interaction.user.id
        board = self.session.boards[uid]
        m = board.mmz[slot]
        if not m:
            await interaction.response.send_message("❌ Monster no longer on field.", ephemeral=True)
            return

        old_pos = m.get("position", "ATK")
        board.change_position(slot, new_pos)

        if old_pos == "SET" and new_pos == "ATK":
            action_msg = f"✨ **{interaction.user.display_name}** Flip Summoned **{m['name']}** (Face-Up Attack Position | {m.get('atk', 0)} ATK)!"
            confirm = f"✅ Flip Summoned **{m['name']}** to Attack Position!"
        else:
            pos_label = "Attack" if new_pos == "ATK" else "Defense"
            action_msg = f"🔄 **{interaction.user.display_name}** shifted **{m['name']}** to {pos_label} Position in MMZ [{slot + 1}]!"
            confirm = f"✅ Changed **{m['name']}** to {pos_label} Position!"

        await interaction.response.edit_message(content=confirm, view=None)
        if self.duel_view.message:
            await self.duel_view.message.edit(
                embed=self.duel_view.build_embed(last_action=action_msg),
                view=self.duel_view
            )


class PositionChangeView(ui.View):
    """Ephemeral view wrapper for position changing dropdown."""

    def __init__(self, session: DuelSession, duel_view: "DuelView", monsters_on_field: List[Tuple[int, Dict[str, Any]]]):
        super().__init__(timeout=60)
        self.add_item(PositionChangeSelect(session, duel_view, monsters_on_field))


class AttackTargetSelect(ui.Select):
    """Dropdown menu for choosing attack targets when both sides have monsters."""

    def __init__(
        self,
        session: DuelSession,
        duel_view: "DuelView",
        attacker_slot: int,
        attacker: Dict[str, Any],
        opp_monsters: List[Tuple[int, Dict[str, Any]]],
    ):
        self.session = session
        self.duel_view = duel_view
        self.attacker_slot = attacker_slot
        self.attacker = attacker
        self.opp_monsters_by_slot = {str(slot): m for slot, m in opp_monsters}

        options = []
        for slot, m in opp_monsters:
            pos = m.get("position", "ATK")
            if pos == "SET":
                m_label = f"🎴 Unknown Monster (MMZ [{slot + 1}])"
                desc = "Face-Down Defense Position (Flip upon attack)"
            elif pos == "DEF":
                m_label = f"🛡️ {m['name'][:60]} (MMZ [{slot + 1}])"
                desc = f"Face-Up DEF ({m.get('def', 0)} DEF)"
            else:
                m_label = f"⚔️ {m['name'][:60]} (MMZ [{slot + 1}])"
                desc = f"Face-Up ATK ({m.get('atk', 0)} ATK)"

            options.append(
                discord.SelectOption(
                    label=m_label[:100],
                    value=str(slot),
                    description=desc[:100],
                    emoji="🎯"
                )
            )

        super().__init__(placeholder="Choose an enemy monster to attack...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        target_slot = int(self.values[0])
        opp_uid = self.session.p2.id if interaction.user.id == self.session.p1.id else self.session.p1.id
        opp_user = self.session.p2 if interaction.user.id == self.session.p1.id else self.session.p1
        my_board = self.session.boards[interaction.user.id]
        opp_board = self.session.boards[opp_uid]

        target = opp_board.mmz[target_slot]
        if not target:
            await interaction.response.send_message("❌ Target monster is no longer on field.", ephemeral=True)
            return

        # Execute battle damage math
        battle_res = calculate_battle_damage(self.attacker, defender=target, is_direct=False)
        dmg = battle_res["damage"]

        # If defender was set, flip to DEF
        if target.get("position") == "SET":
            target["position"] = "DEF"

        if battle_res["defender_destroyed"]:
            opp_board.remove_monster(target_slot)
            opp_board.send_to_gy(target["id"])

        if battle_res["attacker_destroyed"]:
            my_board.remove_monster(self.attacker_slot)
            my_board.send_to_gy(self.attacker["id"])

        damaged_uid = None
        damaged_user = None
        if battle_res["damaged_side"] == "defender":
            damaged_uid = opp_uid
            damaged_user = opp_user
        elif battle_res["damaged_side"] == "attacker":
            damaged_uid = interaction.user.id
            damaged_user = interaction.user

        action_msg = battle_res["summary"]
        is_concluded = False
        if damaged_uid is not None and dmg > 0:
            old_lp, new_lp, is_concluded = self.session.adjust_lp(
                damaged_uid,
                delta=-dmg,
                reason="Battle Combat Damage"
            )
            action_msg += f"\n❤️ **{damaged_user.display_name}** LP: {old_lp} ➔ **{new_lp}** (-{dmg})"

        await interaction.response.edit_message(content=f"⚔️ Attack resolved against MMZ [{target_slot + 1}]!", view=None)

        if is_concluded:
            winner = interaction.user if damaged_uid == opp_uid else opp_user
            await self.duel_view._handle_duel_conclusion(
                winner=winner,
                summary=f"{winner.display_name} won through battle combat.",
                interaction=interaction
            )
            return

        if self.duel_view.message:
            await self.duel_view.message.edit(
                embed=self.duel_view.build_embed(last_action=action_msg),
                view=self.duel_view
            )


class AttackTargetView(ui.View):
    """Ephemeral view wrapper for choosing attack targets."""

    def __init__(
        self,
        session: DuelSession,
        duel_view: "DuelView",
        attacker_slot: int,
        attacker: Dict[str, Any],
        opp_monsters: List[Tuple[int, Dict[str, Any]]],
    ):
        super().__init__(timeout=60)
        self.add_item(AttackTargetSelect(session, duel_view, attacker_slot, attacker, opp_monsters))


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Interactive Board View & Match Controller
# -----------------------------------------------------------------------------

class DuelView(ui.View):
    """
    Main interactive board view containing action buttons for hand inspection,
    phase advancement, card draws, LP adjustments, Normal Summons, Attacks,
    position changes, and match transitions.
    """

    def __init__(self, session: DuelSession):
        super().__init__(timeout=1800)  # 30 minute match timeout
        self.session = session
        self.message: Optional[discord.Message] = None

    def disable_all(self):
        """Disables all action buttons upon duel completion."""
        for item in self.children:
            item.disabled = True

    async def _handle_duel_conclusion(
        self,
        winner: Any,
        summary: str,
        interaction: discord.Interaction
    ) -> None:
        """Centralized handler for concluding a duel, unregistering sessions, and updating telemetry."""
        self.session.duel_over = True
        self.session.winner = winner
        self.disable_all()

        res = await duel_service.conclude_duel(
            session=self.session,
            winner_id=str(winner.id) if winner else "DRAW",
            summary=summary
        )

        win_msg = f"\n🏆 **DUEL CONCLUDED! {winner.mention if hasattr(winner, 'mention') else winner} WINS!**"
        if res and self.session.match_type == "RANKED":
            p1_d = f"+{res['p1_elo_delta']}" if res.get('p1_elo_delta', 0) >= 0 else str(res.get('p1_elo_delta', 0))
            p2_d = f"+{res['p2_elo_delta']}" if res.get('p2_elo_delta', 0) >= 0 else str(res.get('p2_elo_delta', 0))
            win_msg += (
                f"\n📈 **ELO Changes:** {self.session.p1.display_name} (`{p1_d}`) | "
                f"{self.session.p2.display_name} (`{p2_d}`)"
            )

        embed = self.build_embed(last_action=f"{summary}{win_msg}")
        if interaction.response.is_done():
            if self.message:
                await self.message.edit(embed=embed, view=self)
            elif interaction.message:
                await interaction.message.edit(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    def build_embed(self, last_action: str = "Duel in Progress") -> discord.Embed:
        """Constructs the match scoreboard embed with phase badges and zone statuses."""
        p1 = self.session.p1
        p2 = self.session.p2

        mode_badge = "⚔️ [RANKED]" if self.session.match_type == "RANKED" else "🎮 [CASUAL]"
        phase_str = getattr(self.session, "current_phase", PHASE_MAIN_1)
        embed = discord.Embed(
            title=f"{mode_badge} Duel: {p1.display_name} VS {p2.display_name}",
            description=(
                f"**Turn {self.session.turn_count}** — Active Duelist: {self.session.turn_player.mention} | **Phase:** `{phase_str}`\n\n"
                f"**Latest Action:**\n{last_action}"
            ),
            color=0x9B59B6 if not self.session.duel_over else 0x10B981
        )

        p1_bar = "🟩" * max(1, self.session.lp[p1.id] // 1000)
        p2_bar = "🟩" * max(1, self.session.lp[p2.id] // 1000)
        p1_board = self.session.boards[p1.id]
        p2_board = self.session.boards[p2.id]

        embed.add_field(
            name=f"👤 {p1.display_name}",
            value=(
                f"**LP:** {self.session.lp[p1.id]} {p1_bar}\n"
                f"**Hand:** {len(self.session.hands[p1.id])} | **Deck:** {len(self.session.decks[p1.id])} | **GY:** {len(p1_board.gy)}\n"
                f"**MMZ:** {p1_board.format_mmz_display()}\n"
                f"**STZ:** {p1_board.format_stz_display()}"
            ),
            inline=True
        )
        embed.add_field(
            name=f"👤 {p2.display_name}",
            value=(
                f"**LP:** {self.session.lp[p2.id]} {p2_bar}\n"
                f"**Hand:** {len(self.session.hands[p2.id])} | **Deck:** {len(self.session.decks[p2.id])} | **GY:** {len(p2_board.gy)}\n"
                f"**MMZ:** {p2_board.format_mmz_display()}\n"
                f"**STZ:** {p2_board.format_stz_display()}"
            ),
            inline=True
        )

        if self.session.duel_over and self.session.match_result:
            res = self.session.match_result
            if self.session.match_type == "RANKED":
                p1_d = f"+{res['p1_elo_delta']}" if res['p1_elo_delta'] >= 0 else str(res['p1_elo_delta'])
                p2_d = f"+{res['p2_elo_delta']}" if res['p2_elo_delta'] >= 0 else str(res['p2_elo_delta'])
                embed.add_field(
                    name="🏅 Competitive Result",
                    value=(
                        f"• **{p1.display_name}**: `{res['p1_elo_before']}` ➔ **`{res['p1_elo_after']}`** ({p1_d})\n"
                        f"• **{p2.display_name}**: `{res['p2_elo_before']}` ➔ **`{res['p2_elo_after']}`** ({p2_d})"
                    ),
                    inline=False
                )

        embed.set_footer(text="Master Rule 2020 • Use buttons below to execute phase, card, and combat actions.")
        return embed

    # --- ROW 0: TURN & PHASE CONTROLS ---

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
            stat_str = f"ATK {c['atk']}/{c['def']}" if c['card_type'] == 'Monster' else f"{c.get('card_subtype') or 'Normal'} {c['card_type']}"
            card_lines.append(f"**{i}. {c['name']}** [{stat_str}]\n*{c['effect_text'][:100]}...*")

        hand_embed = discord.Embed(
            title=f"🎴 Your Secret Hand ({len(cards)} Cards)",
            description="\n\n".join(card_lines) if card_lines else "*No card details found.*",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=hand_embed, ephemeral=True)

    @ui.button(label="🃏 Draw Card", style=discord.ButtonStyle.secondary, row=0)
    async def draw_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Draws a card from the deck for the active turn player with RNG and deck out checks."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ It is not your turn to draw.", ephemeral=True)
            return

        drawn = self.session.draw_card(uid)
        if drawn is None:
            # Deck Out Loss
            winner = self.session.get_opponent(uid)
            await self._handle_duel_conclusion(
                winner=winner,
                summary=f"**{interaction.user.display_name}** attempted to draw from an empty deck (Deck Out)!",
                interaction=interaction
            )
            return

        await _card_service.track_card_draw(drawn)
        await interaction.response.edit_message(
            embed=self.build_embed(last_action=f"🃏 **{interaction.user.display_name}** drew 1 card."),
            view=self
        )

    @ui.button(label="⏩ Next Phase", style=discord.ButtonStyle.primary, row=0)
    async def next_phase_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Advances current phase sequentially (DRAW -> STANDBY -> MAIN 1 -> BATTLE -> MAIN 2 -> END -> next turn)."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can advance phases.", ephemeral=True)
            return

        prev_phase = self.session.current_phase
        new_phase = self.session.advance_phase()

        if self.session.duel_over:
            winner = self.session.winner
            await self._handle_duel_conclusion(
                winner=winner,
                summary=f"Turn player decked out entering {new_phase} phase.",
                interaction=interaction
            )
            return

        await interaction.response.edit_message(
            embed=self.build_embed(
                last_action=f"⏩ **Phase Advanced:** `{prev_phase}` ➔ **`{new_phase}`** (Active: {self.session.turn_player.mention})"
            ),
            view=self
        )

    @ui.button(label="⏳ End Turn", style=discord.ButtonStyle.success, row=0)
    async def end_turn_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Passes turn priority to the opposing duelist and triggers turn draw."""
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can end the turn.", ephemeral=True)
            return

        self.session.next_turn()
        if self.session.duel_over:
            winner = self.session.winner
            await self._handle_duel_conclusion(
                winner=winner,
                summary=f"{self.session.turn_player.display_name} decked out on turn start.",
                interaction=interaction
            )
            return

        await interaction.response.edit_message(
            embed=self.build_embed(
                last_action=f"🔄 **Turn {self.session.turn_count} Begins**: Priority passed to {self.session.turn_player.mention}! (Phase: `{self.session.current_phase}`)"
            ),
            view=self
        )

    # --- ROW 1: QUICK LP & RESOLUTION RNG ---

    @ui.button(label="❤️ -1000 LP", style=discord.ButtonStyle.danger, row=1)
    async def minus_1000_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Quick button to deal 1000 damage to the clicking player."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return

        old_lp, new_lp, is_concluded = self.session.adjust_lp(uid, delta=-1000, reason="Quick Damage")
        action_msg = f"💥 **{interaction.user.display_name}** took 1000 damage! (Remaining LP: {new_lp})"

        if is_concluded:
            winner = self.session.get_opponent(uid)
            await self._handle_duel_conclusion(
                winner=winner,
                summary=f"{interaction.user.display_name}'s LP dropped to 0.",
                interaction=interaction
            )
            return

        await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)

    @ui.button(label="❤️ Custom LP", style=discord.ButtonStyle.secondary, row=1)
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

    # --- ROW 2: FIELD PLAYS & COMBAT ---

    @ui.button(label="⚡ Summon/Set", style=discord.ButtonStyle.primary, row=2)
    async def summon_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Normal Summon (Face-up ATK) or Set (Face-down DEF) with Tribute and Limit checks."""
        self.message = interaction.message
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can summon or set monsters.", ephemeral=True)
            return

        if self.session.normal_summon_used.get(uid, False):
            await interaction.response.send_message("❌ You have already performed your Normal Summon / Set for this turn.", ephemeral=True)
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
            await interaction.response.send_message("❌ You have no Monster cards in hand to summon or set.", ephemeral=True)
            return

        view = SummonView(self.session, self, monster_cards)
        await interaction.response.send_message(
            "⚡ **Select a monster to Normal Summon (Face-up Attack) or Set (Face-down Defense):**",
            view=view,
            ephemeral=True
        )

    @ui.button(label="✨ Set S/T", style=discord.ButtonStyle.secondary, row=2)
    async def set_spell_trap_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Sets a Spell or Trap card face-down from hand into an open Spell & Trap Zone."""
        self.message = interaction.message
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can set Spells or Traps.", ephemeral=True)
            return

        board = self.session.boards[uid]
        if not board.has_available_stz():
            await interaction.response.send_message("❌ All 5 Spell & Trap Zones are currently occupied!", ephemeral=True)
            return

        hand_cids = self.session.hands[uid]
        st_cards = []
        for cid in hand_cids:
            c = await _card_service.get_card_by_query(str(cid))
            if c and c.get("card_type") in ("Spell", "Trap"):
                st_cards.append(c)

        if not st_cards:
            await interaction.response.send_message("📭 You have no Spell or Trap cards in hand to set.", ephemeral=True)
            return

        view = SpellTrapView(self.session, self, st_cards)
        await interaction.response.send_message(
            "✨ **Select a Spell or Trap card to Set into your Spell & Trap Zone:**",
            view=view,
            ephemeral=True
        )

    @ui.button(label="🔄 Position", style=discord.ButtonStyle.secondary, row=2)
    async def position_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Changes a monster's battle position (ATK <-> DEF, or Flip Summon SET -> ATK)."""
        self.message = interaction.message
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can change monster positions.", ephemeral=True)
            return

        board = self.session.boards[uid]
        field_monsters = [(i, m) for i, m in enumerate(board.mmz) if m is not None]
        if not field_monsters:
            await interaction.response.send_message("❌ You have no monsters on the field to change position.", ephemeral=True)
            return

        view = PositionChangeView(self.session, self, field_monsters)
        await interaction.response.send_message(
            "🔄 **Select a monster to shift battle position or Flip Summon:**",
            view=view,
            ephemeral=True
        )

    @ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, row=2)
    async def attack_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Declares an attack using battle damage calculations, positions, and direct strikes."""
        self.message = interaction.message
        uid = interaction.user.id
        if uid != self.session.turn_player.id:
            await interaction.response.send_message("⏳ Only the active turn player can declare attacks.", ephemeral=True)
            return

        my_board = self.session.boards[uid]
        my_atk_monsters = [(i, m) for i, m in enumerate(my_board.mmz) if m and m.get("position") == "ATK"]
        if not my_atk_monsters:
            await interaction.response.send_message(
                "❌ You have no monsters in Attack Position to declare an attack with! (Use `⚡ Summon/Set` first or change position).",
                ephemeral=True
            )
            return

        opp_uid = self.session.p2.id if uid == self.session.p1.id else self.session.p1.id
        opp_user = self.session.p2 if uid == self.session.p1.id else self.session.p1
        opp_board = self.session.boards[opp_uid]
        opp_monsters = [(i, m) for i, m in enumerate(opp_board.mmz) if m is not None]

        attacker_slot, attacker = my_atk_monsters[0] if len(my_atk_monsters) == 1 else max(my_atk_monsters, key=lambda t: t[1].get("atk", 0))

        if not opp_monsters:
            # DIRECT ATTACK
            battle_res = calculate_battle_damage(attacker, defender=None, is_direct=True)
            dmg = battle_res["damage"]
            old_lp, new_lp, is_concluded = self.session.adjust_lp(
                opp_uid,
                delta=-dmg,
                reason=f"Direct Attack from {attacker.get('name')}"
            )
            action_msg = f"{battle_res['summary']}\n❤️ **{opp_user.display_name}** LP: {old_lp} ➔ **{new_lp}** (-{dmg})"

            if is_concluded:
                await self._handle_duel_conclusion(
                    winner=interaction.user,
                    summary=f"{interaction.user.display_name} won by direct attack.",
                    interaction=interaction
                )
                return

            await interaction.response.edit_message(embed=self.build_embed(last_action=action_msg), view=self)
            return

        # Opponent controls monsters: open attack target selection view
        view = AttackTargetView(self.session, self, attacker_slot, attacker, opp_monsters)
        await interaction.response.send_message(
            f"⚔️ **Select an enemy monster for {attacker['name']} ({attacker.get('atk', 0)} ATK) to attack:**",
            view=view,
            ephemeral=True
        )

    @ui.button(label="🏳️ Surrender", style=discord.ButtonStyle.danger, row=2)
    async def surrender_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Concedes the match to the opponent."""
        uid = interaction.user.id
        if uid not in (self.session.p1.id, self.session.p2.id):
            return

        winner, summary = self.session.surrender(uid)
        await self._handle_duel_conclusion(winner=winner, summary=summary, interaction=interaction)

    # --- ROW 3: DISPLAY & FIELD VISUALIZATION ---

    @ui.button(label="🗺️ Duel Field", style=discord.ButtonStyle.secondary, row=3)
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
            title="🗺️ Live Duel Field Playmat (Master Rule 2020)",
            description=f"```text\n{ascii_mat}\n```",
            color=0x3498DB
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


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

        p1_deck, p1_extra = await _deck_service.get_player_duel_decks(str(self.challenger.id))
        p2_deck, p2_extra = await _deck_service.get_player_duel_decks(str(self.challenged.id))

        # Legal Yu-Gi-Oh! Deck fallback: 40+ cards strictly from Main Deck pool
        all_cards = await _card_service.get_all_cards()
        main_pool = [c["id"] for c in all_cards if not is_extra_deck_card(c)]
        if len(p1_deck) < 40:
            p1_deck = main_pool.copy()
        if len(p2_deck) < 40:
            p2_deck = main_pool.copy()

        p1_deck_name = await _deck_service.find_matching_saved_deck(str(self.challenger.id))
        p2_deck_name = await _deck_service.find_matching_saved_deck(str(self.challenged.id))

        session = duel_service.start_duel(
            p1=self.challenger,
            p2=self.challenged,
            p1_deck=p1_deck,
            p2_deck=p2_deck,
            match_type=match_type,
            p1_deck_name=p1_deck_name,
            p2_deck_name=p2_deck_name,
            p1_extra_deck=p1_extra,
            p2_extra_deck=p2_extra,
        )

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


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Duel Slash Commands Cog
# -----------------------------------------------------------------------------

class DuelEngineCog(commands.Cog, name="DuelEngine"):
    """Slash commands for initiating, managing, and inspecting live Yu-Gi-Oh! duels."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="duel", description="Challenge another player to a live Yu-Gi-Oh! duel on Discord")
    @app_commands.describe(
        opponent="The user you wish to duel",
        hidden="Whether to hide the response ephemerally (Default: False)"
    )
    async def duel_command(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
        hidden: Optional[bool] = False
    ):
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
            view=view,
            ephemeral=bool(hidden)
        )

    @app_commands.command(name="duel_manual", description="Manual PvP duel mode against another player (Ranked with ELO or Casual)")
    @app_commands.describe(
        opponent="The duelist you wish to challenge",
        hidden="Whether to hide the response ephemerally (Default: False)"
    )
    async def duel_manual_command(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
        hidden: Optional[bool] = False
    ):
        """Direct alias for manual PvP duels."""
        await self.duel_command(interaction, opponent, hidden=hidden)

    @app_commands.command(name="board", description="View the official Yu-Gi-Oh! Master Rule duel field layout and zone guide")
    @app_commands.describe(hidden="Whether to display the board guide ephemerally (Default: False)")
    async def board_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Displays rich educational embed illustrating the official Yu-Gi-Oh! board zones."""
        embed = build_board_guide_embed()
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))

    @app_commands.command(name="surrender", description="Concede and forfeit your current active Yu-Gi-Oh! duel")
    @app_commands.describe(hidden="Whether to send confirmation ephemerally (Default: False)")
    async def surrender_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Allows a duelist to forfeit an ongoing match."""
        session = duel_manager.get_session(interaction.user.id)
        if not session or session.duel_over:
            await interaction.response.send_message("❌ You are not currently in an active duel.", ephemeral=True)
            return

        winner, summary = session.surrender(interaction.user.id)
        res = await duel_service.conclude_duel(session, winner_id=str(winner.id) if winner else "DRAW", summary=summary)

        msg = f"🏳️ **{interaction.user.display_name}** surrendered! 🏆 **{winner.mention if hasattr(winner, 'mention') else winner} WINS!**"
        if res and session.match_type == "RANKED":
            p1_d = f"+{res['p1_elo_delta']}" if res.get('p1_elo_delta', 0) >= 0 else str(res.get('p1_elo_delta', 0))
            p2_d = f"+{res['p2_elo_delta']}" if res.get('p2_elo_delta', 0) >= 0 else str(res.get('p2_elo_delta', 0))
            msg += f"\n📈 **ELO Changes:** {session.p1.display_name} (`{p1_d}`) | {session.p2.display_name} (`{p2_d}`)"

        await interaction.response.send_message(msg, ephemeral=bool(hidden))

    @app_commands.command(name="duel_status", description="Inspect the active duel session and board state for a player")
    @app_commands.describe(
        user="The player whose duel state you wish to inspect (Default: yourself)",
        hidden="Whether to show status ephemerally (Default: False)"
    )
    async def duel_status_command(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
        hidden: Optional[bool] = False
    ):
        """Displays live score, phase, and zone overview of an active duel."""
        target = user or interaction.user
        session = duel_manager.get_session(target.id)
        if not session or session.duel_over:
            await interaction.response.send_message(
                f"ℹ️ **{target.display_name}** is not currently in an active duel.",
                ephemeral=bool(hidden)
            )
            return

        p1_board = session.boards[session.p1.id]
        p2_board = session.boards[session.p2.id]
        embed = discord.Embed(
            title=f"⚔️ Active Duel Status: {session.p1.display_name} VS {session.p2.display_name}",
            description=(
                f"**Turn {session.turn_count}** — Turn Player: {session.turn_player.mention} | **Phase:** `{session.current_phase}`\n"
                f"**Mode:** `{session.match_type}`"
            ),
            color=0x3498DB
        )
        embed.add_field(
            name=f"👤 {session.p1.display_name}",
            value=(
                f"**LP:** {session.lp[session.p1.id]}\n"
                f"**Hand:** {len(session.hands[session.p1.id])} | **Deck:** {len(session.decks[session.p1.id])} | **GY:** {len(p1_board.gy)}\n"
                f"**MMZ:** {p1_board.format_mmz_display()}\n"
                f"**STZ:** {p1_board.format_stz_display()}"
            ),
            inline=True
        )
        embed.add_field(
            name=f"👤 {session.p2.display_name}",
            value=(
                f"**LP:** {session.lp[session.p2.id]}\n"
                f"**Hand:** {len(session.hands[session.p2.id])} | **Deck:** {len(session.decks[session.p2.id])} | **GY:** {len(p2_board.gy)}\n"
                f"**MMZ:** {p2_board.format_mmz_display()}\n"
                f"**STZ:** {p2_board.format_stz_display()}"
            ),
            inline=True
        )
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Setup & Public Manifest)
# =============================================================================

async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(DuelEngineCog(bot))


__all__ = [
    "DuelEngineCog",
    "DuelSession",
    "DuelView",
    "ChallengeView",
    "LPModal",
    "SummonSelect",
    "SummonView",
    "SpellTrapSelect",
    "SpellTrapView",
    "PositionChangeSelect",
    "PositionChangeView",
    "AttackTargetSelect",
    "AttackTargetView",
    "setup",
]
