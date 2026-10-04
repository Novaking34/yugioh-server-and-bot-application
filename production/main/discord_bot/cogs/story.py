#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.cogs.story
Description:
    Discord Bot Cog: Story Mode RPG & Lore Campaign Gateway.
    Allows non-competitive and lore-focused duelists to experience the custom card
    sagas of The Land of Kustomazi. Loads chapter and stage encounters directly
    from the database, supporting both scripted encounter timelines and dynamic
    AI duels with true deck RNG and manual Master Rule 5 field state controls.

Architectural Classification:
    Layer 3 (L3) - Presentation & Discord Gateway Cog
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import random
from typing import Any, Dict, List, Optional, Tuple

import discord
from discord import app_commands, ui
from discord.ext import commands

from bot_config import BOT_CONFIG
from production.main.logger import get_logger
from services.card import CardService
from services.deck import DeckService, is_extra_deck_card
from services.duel import duel_manager
from services.story import StoryDuelSession, StoryService, story_service
from utils import build_story_stage_embed

logger = get_logger("discord_bot.cogs.story")

# =============================================================================
# BLOCK 3: BODY BLOCK (UI Modals, Views, and Story Gateway Cog)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Story LP Adjustment Modal
# -----------------------------------------------------------------------------
class StoryLPModal(ui.Modal, title="Manual LP Adjustment (Story Duel)"):
    """Allows players or moderators to manually apply arbitrary damage or healing."""

    def __init__(self, session: StoryDuelSession, target: str, view: "StoryDuelView"):
        super().__init__()
        self.session = session
        self.target = target
        self.story_view = view

        target_name = (
            getattr(session.player, "display_name", str(session.player))
            if target == "player"
            else session.npc_name
        )
        self.amount = ui.TextInput(
            label=f"Adjust {target_name}'s LP (+ or -)",
            placeholder="e.g. -1500 or +800",
            max_length=6
        )
        self.reason = ui.TextInput(
            label="Reason / Effect Details",
            placeholder="e.g. Monster battle damage or Spell effect",
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

        key = self.session.player.id if self.target == "player" else "npc"
        old_lp = self.session.lp[key]
        new_lp = max(0, old_lp + val)
        self.session.lp[key] = new_lp

        target_name = (
            getattr(self.session.player, "display_name", str(self.session.player))
            if self.target == "player"
            else self.session.npc_name
        )
        sign = "+" if val >= 0 else ""
        reason_txt = self.reason.value or "Manual Adjustment"
        msg = f"❤️ **{target_name}** LP: {old_lp} ➔ **{new_lp}** ({sign}{val}) [{reason_txt}]"

        # Check win/loss
        if self.session.lp["npc"] <= 0:
            self.session.duel_over = True
            self.session.winner = self.session.player.id
            duel_manager.unregister_session(self.session)
            res = await self.story_view.story_service.complete_stage(
                str(self.session.player.id), self.session.stage_number
            )
            msg += f"\n\n🏆 **VICTORY ACHIEVED!**\n*{self.session.stage['outro_dialogue']}*"
            if res.get("reward_title"):
                msg += f"\n🏅 Unlocked Title: **{res['reward_title']}**"
            if res.get("reward_card_name"):
                msg += f"\n🃏 Unlocked Card: **{res['reward_card_name']}**"
            self.story_view.disable_all()

        elif self.session.lp[self.session.player.id] <= 0:
            self.session.duel_over = True
            self.session.winner = "npc"
            duel_manager.unregister_session(self.session)
            msg += f"\n\n💀 Your Life Points dropped to 0. {self.session.npc_name} claims victory."
            self.story_view.disable_all()

        embed = self.story_view.build_embed(action_text=msg)
        await interaction.response.edit_message(
            embed=embed,
            view=self.story_view if not self.session.duel_over else None
        )


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Card Selection & Extra Deck Views
# -----------------------------------------------------------------------------
class StoryPlayCardPickerView(ui.View):
    """Ephemeral selection view for playing or summoning a card from hand."""

    def __init__(self, session: StoryDuelSession, cards: List[Dict[str, Any]], story_view: "StoryDuelView"):
        super().__init__(timeout=60)
        self.session = session
        self.story_view = story_view

        options = []
        seen = set()
        for c in cards[:25]:
            cid = c["id"]
            if cid in seen:
                continue
            seen.add(cid)
            stat = f"ATK {c.get('atk', 0)}" if c.get("card_type") == "Monster" else (c.get("card_subtype") or "Spell")
            options.append(
                discord.SelectOption(
                    label=c["name"][:100],
                    value=str(cid),
                    description=f"{c.get('card_type', 'Card')} • {stat}"[:100],
                    emoji="⚔️" if c.get("card_type") == "Monster" else "✨"
                )
            )

        self.select_menu = ui.Select(placeholder="Choose card from Hand to play onto the field...", options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        cid = int(self.select_menu.values[0])
        card_data = await self.story_view.card_service.get_card_by_query(str(cid))
        if not card_data:
            await interaction.response.send_message("❌ Card not found.", ephemeral=True)
            return

        play_msg = self.session.play_player_card(card_data)
        if hasattr(self.story_view.card_service, "track_card_play"):
            try:
                await self.story_view.card_service.track_card_play(cid)
            except Exception:
                pass

        # Update main board embed
        embed = self.story_view.build_embed(action_text=play_msg)
        if hasattr(self.story_view, "message") and self.story_view.message:
            try:
                await self.story_view.message.edit(embed=embed, view=self.story_view)
            except Exception:
                pass
        await interaction.response.send_message(f"✅ {play_msg}", ephemeral=True)


class StoryExtraDeckPickerView(ui.View):
    """Ephemeral selection view for Special Summoning a monster from the Extra Deck."""

    def __init__(self, session: StoryDuelSession, cards: List[Dict[str, Any]], story_view: "StoryDuelView"):
        super().__init__(timeout=60)
        self.session = session
        self.story_view = story_view

        options = []
        seen = set()
        for c in cards[:25]:
            cid = c["id"]
            if cid in seen:
                continue
            seen.add(cid)
            subtype = c.get("card_subtype") or "Extra"
            stat = f"ATK {c.get('atk', 0)} / DEF {c.get('def', 0)}"
            options.append(
                discord.SelectOption(
                    label=c["name"][:100],
                    value=str(cid),
                    description=f"{subtype} • {stat}"[:100],
                    emoji="🌀"
                )
            )

        self.select_menu = ui.Select(placeholder="Choose Extra Deck monster to Special Summon...", options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        cid = int(self.select_menu.values[0])
        card_data = await self.story_view.card_service.get_card_by_query(str(cid))
        if not card_data:
            await interaction.response.send_message("❌ Card not found.", ephemeral=True)
            return

        play_msg = self.session.special_summon_extra_monster(card_data)
        if hasattr(self.story_view.card_service, "track_card_play"):
            try:
                await self.story_view.card_service.track_card_play(cid)
            except Exception:
                pass

        # Update main board embed
        embed = self.story_view.build_embed(action_text=play_msg)
        if hasattr(self.story_view, "message") and self.story_view.message:
            try:
                await self.story_view.message.edit(embed=embed, view=self.story_view)
            except Exception:
                pass
        await interaction.response.send_message(f"✅ {play_msg}", ephemeral=True)


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Interactive Board View
# -----------------------------------------------------------------------------
class StoryDuelView(ui.View):
    """
    Main interactive board view for Story Mode encounters.
    Combines scripted/AI NPC turns with full manual duel controls.
    """

    def __init__(self, session: StoryDuelSession, story_srv: StoryService, card_srv: CardService):
        super().__init__(timeout=900)  # 15 minute timeout
        self.session = session
        self.story_service = story_srv
        self.card_service = card_srv
        self.message: Optional[discord.Message] = None

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    def build_embed(self, action_text: str = "") -> discord.Embed:
        stage = self.session.stage
        color = 0x8B5CF6 if not self.session.duel_over else (
            0x10B981 if self.session.winner == self.session.player.id else 0xEF4444
        )

        mode_badge = "📜 [SCRIPTED STORY]" if self.session.encounter_type == "SCRIPTED" else "🤖 [AI DUEL]"
        p_name = getattr(self.session.player, "display_name", str(self.session.player))
        embed = discord.Embed(
            title=f"{mode_badge} Stage {stage.get('stage_number', 1)}: {stage.get('title', 'Encounter')}",
            description=f"⚔️ **{p_name}** vs **{self.session.npc_name}**",
            color=color
        )

        p_lp = self.session.lp[self.session.player.id]
        n_lp = self.session.lp["npc"]

        p_bar = "🟩" * max(1, min(10, p_lp // 800))
        n_bar = "🟥" * max(1, min(10, n_lp // 800))

        p_field_str = f"\nField: {', '.join([m['name'] for m in self.session.player_field])}" if self.session.player_field else ""
        n_field_str = f"\nField: {', '.join([m['name'] for m in self.session.npc_field])}" if self.session.npc_field else ""

        embed.add_field(
            name=f"👤 {p_name}",
            value=(
                f"**{p_lp} LP**\n"
                f"Hand: `{len(self.session.player_hand)}` | Deck: `{len(self.session.player_deck)}` | "
                f"Extra: `{len(self.session.player_extra_deck)}` | GY: `{len(self.session.player_gy)}`"
                f"{p_field_str}\n{p_bar}"
            ),
            inline=True
        )
        embed.add_field(
            name=f"🤖 {self.session.npc_name}",
            value=(
                f"**{n_lp} LP**\n"
                f"Hand: `{len(self.session.npc_hand)}` | Deck: `{len(self.session.npc_deck)}` | "
                f"Extra: `{len(self.session.npc_extra_deck)}` | GY: `{len(self.session.npc_gy)}`"
                f"{n_field_str}\n{n_bar}"
            ),
            inline=True
        )

        if action_text:
            embed.add_field(name="📢 Duel Chronicle", value=action_text, inline=False)

        if self.session.duel_over:
            if self.session.winner == self.session.player.id:
                embed.add_field(
                    name="🏆 VICTORY!",
                    value=f"*{stage.get('outro_dialogue', 'Congratulations on your victory!')}*",
                    inline=False
                )
            else:
                embed.add_field(
                    name="💀 DEFEAT",
                    value=f"The power of {self.session.npc_name} overwhelmed you. Refine your deck and try again with `/story`!",
                    inline=False
                )

        embed.set_footer(text=f"Turn {self.session.turn_count} • Loaded from Story Database • Zero ELO Risk")
        return embed

    @ui.button(label="⚔️ Attack / Next Turn", style=discord.ButtonStyle.primary, row=0)
    async def attack_button(self, interaction: discord.Interaction, button: ui.Button):
        """Executes player attack and triggers the NPC's scripted or AI turn response."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        if self.session.duel_over:
            await interaction.response.send_message("❌ This duel has concluded.", ephemeral=True)
            return

        # Determine player damage based on summoned field monsters or standard direct strike
        if self.session.player_field:
            lead = self.session.player_field[-1]
            player_dmg = max(500, lead.get("atk") or 1000)
            attack_line = f"⚔️ **{interaction.user.display_name}** commands **{lead['name']}** (ATK {player_dmg}) to strike **{self.session.npc_name}** for **{player_dmg}** damage!"
        else:
            player_dmg = 1000
            attack_line = f"⚔️ **{interaction.user.display_name}** launched a direct attack on **{self.session.npc_name}** for **{player_dmg}** damage!"

        self.session.lp["npc"] = max(0, self.session.lp["npc"] - player_dmg)
        chronicle = [attack_line]

        # Check threshold dialogue loaded from database script (half LP dialogue)
        half_hp = getattr(self.session, "npc_max_hp", 8000) // 2
        if self.session.lp["npc"] <= half_hp and not self.session.threshold_triggered and self.session.lp["npc"] > 0:
            self.session.threshold_triggered = True
            threshold_text = (
                self.session.script_data.get(f"threshold_{half_hp}")
                or self.session.script_data.get("threshold_half")
                or self.session.script_data.get("threshold_4000")
            )
            if threshold_text:
                chronicle.append(threshold_text)

        # NPC turn execution (scripted or dynamic AI)
        if self.session.lp["npc"] > 0:
            npc_play_text, npc_dmg = await self.session.execute_npc_turn(self.card_service)
            self.session.lp[self.session.player.id] = max(0, self.session.lp[self.session.player.id] - npc_dmg)

            chronicle.append(f"\n🤖 **{self.session.npc_name}'s Turn:**")
            chronicle.append(npc_play_text)
            chronicle.append(f"💔 You took **{npc_dmg}** damage! (Remaining LP: {self.session.lp[self.session.player.id]})")

        # Win/Loss check
        if self.session.lp["npc"] <= 0:
            self.session.duel_over = True
            self.session.winner = self.session.player.id
            duel_manager.unregister_session(self.session)

            res = await self.story_service.complete_stage(
                str(self.session.player.id), self.session.stage_number
            )
            reward_txt = ""
            if res.get("reward_title"):
                reward_txt += f"\n🏅 Unlocked Title: **{res['reward_title']}**"
            if res.get("reward_card_name"):
                reward_txt += f"\n🃏 Unlocked Card: **{res['reward_card_name']}**"

            chronicle.append(f"\n🎉 **Victory Achieved!**{reward_txt}")
            self.disable_all()

        elif self.session.lp[self.session.player.id] <= 0:
            self.session.duel_over = True
            self.session.winner = "npc"
            duel_manager.unregister_session(self.session)
            chronicle.append("\n💀 Your Life Points dropped to 0.")
            self.disable_all()

        self.session.turn_count += 1
        embed = self.build_embed(action_text="\n".join([c for c in chronicle if c]))
        await interaction.response.edit_message(
            embed=embed,
            view=self if not self.session.duel_over else None
        )

    @ui.button(label="❤️ Custom LP", style=discord.ButtonStyle.secondary, row=0)
    async def custom_lp_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Allows manual LP adjustment for either player or NPC, supporting custom card effects."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return
        self.message = interaction.message
        await interaction.response.send_modal(StoryLPModal(self.session, "npc", self))

    @ui.button(label="🎴 View Hand", style=discord.ButtonStyle.secondary, row=0)
    async def view_hand_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Inspect private secret hand drawn with RNG from player's Main Deck."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        hand_cids = self.session.player_hand
        if not hand_cids:
            await interaction.response.send_message("📭 Your hand is currently empty.", ephemeral=True)
            return

        cards = []
        for cid in hand_cids:
            c = await self.card_service.get_card_by_query(str(cid))
            if c:
                cards.append(c)

        card_lines = []
        for i, c in enumerate(cards, 1):
            stat_str = f"ATK {c['atk']}/{c['def']}" if c['card_type'] == 'Monster' else f"{c.get('card_subtype') or 'Normal'} {c['card_type']}"
            card_lines.append(f"**{i}. {c['name']}** [{stat_str}]\n*{c['effect_text'][:100]}...*")

        hand_embed = discord.Embed(
            title=f"🎴 Secret Hand — {interaction.user.display_name} ({len(cards)} Cards)",
            description="\n\n".join(card_lines) if card_lines else "*No card details.*",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=hand_embed, ephemeral=True)

    @ui.button(label="🃏 Draw Card", style=discord.ButtonStyle.secondary, row=0)
    async def draw_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Draws 1 card from player's real Main Deck with RNG."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        drawn = self.session.draw_player_card()
        if drawn:
            if hasattr(self.card_service, "track_card_draw"):
                try:
                    await self.card_service.track_card_draw(drawn)
                except Exception:
                    pass
            card_info = await self.card_service.get_card_by_query(str(drawn))
            cname = card_info["name"] if card_info else f"Card #{drawn}"
            await interaction.response.send_message(f"🎴 You drew: **{cname}**! (Secret Hand)", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Your Main Deck is empty!", ephemeral=True)

    @ui.button(label="🏳️ Surrender", style=discord.ButtonStyle.danger, row=0)
    async def surrender_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Surrenders the encounter."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ Only the duelist can surrender.", ephemeral=True)
            return

        self.message = interaction.message
        self.session.duel_over = True
        self.session.winner = "npc"
        duel_manager.unregister_session(self.session)
        self.disable_all()

        embed = self.build_embed(action_text="🏳️ You surrendered the encounter.")
        await interaction.response.edit_message(embed=embed, view=None)

    @ui.button(label="✨ Play Card", style=discord.ButtonStyle.success, row=1)
    async def play_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Allows playing or summoning a card from the secret hand onto the field/GY."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        hand_cids = self.session.player_hand
        if not hand_cids:
            await interaction.response.send_message("📭 Your hand is currently empty.", ephemeral=True)
            return

        cards = []
        for cid in hand_cids:
            c = await self.card_service.get_card_by_query(str(cid))
            if c:
                cards.append(c)

        if not cards:
            await interaction.response.send_message("❌ No cards in hand available.", ephemeral=True)
            return

        picker_view = StoryPlayCardPickerView(self.session, cards, self)
        await interaction.response.send_message(
            "Select a card from your Hand to summon or activate:",
            view=picker_view,
            ephemeral=True
        )

    @ui.button(label="🌀 Extra Deck", style=discord.ButtonStyle.primary, row=1)
    async def extra_deck_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Inspects Extra Deck and allows Special Summoning Fusion, Synchro, or Link monsters."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        extra_cids = self.session.player_extra_deck
        if not extra_cids:
            await interaction.response.send_message("📭 Your Extra Deck is empty.", ephemeral=True)
            return

        cards = []
        for cid in extra_cids:
            c = await self.card_service.get_card_by_query(str(cid))
            if c:
                cards.append(c)

        if not cards:
            await interaction.response.send_message("❌ No Extra Deck monsters available.", ephemeral=True)
            return

        picker_view = StoryExtraDeckPickerView(self.session, cards, self)
        await interaction.response.send_message(
            "Select an Extra Deck monster (Fusion, Synchro, Link) to Special Summon:",
            view=picker_view,
            ephemeral=True
        )

    @ui.button(label="🌀 Mill 1 Card", style=discord.ButtonStyle.secondary, row=1)
    async def mill_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Sends top card of deck directly to Graveyard with RNG."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        drawn = self.session.mill_player_card()
        if not drawn:
            await interaction.response.send_message("⚠️ Your Main Deck is empty!", ephemeral=True)
            return

        card_info = await self.card_service.get_card_by_query(str(drawn))
        cname = card_info["name"] if card_info else f"Card #{drawn}"
        embed = self.build_embed(
            action_text=f"🌀 **{interaction.user.display_name}** milled top card to Graveyard: **{cname}**!"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="🪙 Coin Toss", style=discord.ButtonStyle.secondary, row=1)
    async def coin_toss_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Simulates Yu-Gi-Oh! coin flip (Heads or Tails)."""
        self.message = interaction.message
        flip = random.choice(["🪙 HEADS", "🪙 TAILS"])
        embed = self.build_embed(action_text=f"🪙 **{interaction.user.display_name}** tossed a coin: **{flip}**!")
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="🎲 Roll d6", style=discord.ButtonStyle.secondary, row=1)
    async def roll_dice_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Simulates natural Yu-Gi-Oh! die roll for card effects."""
        self.message = interaction.message
        res = random.randint(1, 6)
        embed = self.build_embed(action_text=f"🎲 **{interaction.user.display_name}** rolled a die: **[{res}]**!")
        await interaction.response.edit_message(embed=embed, view=self)


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Story Journey Hub View
# -----------------------------------------------------------------------------
class StoryJourneyView(ui.View):
    """Hub view for browsing story stages and launching encounters."""

    def __init__(
        self,
        user: discord.User,
        stage: dict,
        progress: dict,
        story_srv: StoryService,
        deck_srv: DeckService,
        card_srv: CardService
    ):
        super().__init__(timeout=180)
        self.user = user
        self.stage = stage
        self.progress = progress
        self.story_service = story_srv
        self.deck_service = deck_srv
        self.card_service = card_srv

    @ui.button(label="⚔️ Begin Story Duel", style=discord.ButtonStyle.success)
    async def begin_duel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This journey view belongs to another duelist.", ephemeral=True)
            return

        if duel_manager.is_user_dueling(interaction.user.id):
            await interaction.response.send_message(
                "❌ You already have an active duel session running! Conclude it or ask a moderator to reset it with `/admin reset_duel`.",
                ephemeral=True
            )
            return

        # Fetch player deck partitioned into (Main, Extra)
        player_main, player_extra = await self.deck_service.get_player_duel_decks(str(interaction.user.id))

        # Legal Yu-Gi-Oh! Deck fallback: 40+ cards strictly from Main Deck pool
        all_cards = await self.card_service.get_all_cards()
        main_pool = [c["id"] for c in all_cards if not is_extra_deck_card(c)]
        extra_pool = [c["id"] for c in all_cards if is_extra_deck_card(c)]

        if len(player_main) < 40:
            player_main = main_pool.copy()
        if not player_extra:
            player_extra = extra_pool.copy()

        # Fetch NPC deck partitioned into (Main, Extra)
        npc_deck_id = self.stage.get("opponent_deck_id") or 1
        npc_deck_obj = await self.deck_service.get_character_deck_by_id(npc_deck_id)
        npc_main: List[int] = []
        npc_extra: List[int] = []

        if npc_deck_obj and npc_deck_obj.get("cards"):
            for c in npc_deck_obj["cards"]:
                section = (c.get("section") or "").upper()
                if section == "EXTRA" or is_extra_deck_card(c):
                    npc_extra.extend([c["id"]] * c["quantity"])
                else:
                    npc_main.extend([c["id"]] * c["quantity"])

        if len(npc_main) < 40:
            npc_main = main_pool.copy()
        if not npc_extra:
            npc_extra = extra_pool.copy()

        session = StoryDuelSession(
            player=interaction.user,
            stage=self.stage,
            player_deck=player_main,
            npc_deck=npc_main,
            player_extra_deck=player_extra,
            npc_extra_deck=npc_extra,
        )
        duel_manager.register_session(interaction.user.id, 0, session)

        duel_view = StoryDuelView(session, self.story_service, self.card_service)
        mode_label = "Scripted Encounter" if session.encounter_type == "SCRIPTED" else "Dynamic AI Duel"
        embed = duel_view.build_embed(
            action_text=f"🌌 **{self.stage.get('title', 'Encounter')}** begins! ({mode_label})\nConfront **{session.npc_name}**."
        )
        await interaction.response.send_message(embed=embed, view=duel_view)
        try:
            duel_view.message = await interaction.original_response()
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Story Presentation Cog Gateway
# -----------------------------------------------------------------------------
class StoryCog(commands.Cog, name="Story"):
    """Commands for experiencing the in-server custom card RPG campaign."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.story_service = StoryService()
        self.deck_service = DeckService()
        self.card_service = CardService()

    @app_commands.command(name="story", description="Embark on your journey in The Land of Kustomazi campaign")
    @app_commands.describe(hidden="Whether the campaign screen should be private to you")
    async def story_journey_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Displays current story chapter, active stage, and dialog encounter."""
        progress = await self.story_service.get_or_create_player_progress(str(interaction.user.id))
        stage_num = progress["current_stage_number"]
        chapter_id = progress["current_chapter_id"]

        stage = await self.story_service.get_stage(chapter_id, stage_num)
        if not stage:
            await interaction.response.send_message("❌ Active story stage not found in database.", ephemeral=True)
            return

        embed = build_story_stage_embed(stage, progress)
        view = StoryJourneyView(
            interaction.user, stage, progress, self.story_service, self.deck_service, self.card_service
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=bool(hidden))

    @app_commands.command(name="story_duel", description="Directly launch the story duel encounter for your current stage")
    @app_commands.describe(hidden="Whether the encounter launch should be private")
    async def story_duel_direct_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Direct launch shortcut for the active story stage encounter."""
        if duel_manager.is_user_dueling(interaction.user.id):
            await interaction.response.send_message(
                "❌ You already have an active duel session running. Surrender or finish your match first.",
                ephemeral=True
            )
            return

        progress = await self.story_service.get_or_create_player_progress(str(interaction.user.id))
        stage_num = progress["current_stage_number"]
        chapter_id = progress["current_chapter_id"]

        stage = await self.story_service.get_stage(chapter_id, stage_num)
        if not stage:
            await interaction.response.send_message("❌ Active story stage not found in database.", ephemeral=True)
            return

        # Fetch player deck partitioned into (Main, Extra)
        player_main, player_extra = await self.deck_service.get_player_duel_decks(str(interaction.user.id))

        all_cards = await self.card_service.get_all_cards()
        main_pool = [c["id"] for c in all_cards if not is_extra_deck_card(c)]
        extra_pool = [c["id"] for c in all_cards if is_extra_deck_card(c)]

        if len(player_main) < 40:
            player_main = main_pool.copy()
        if not player_extra:
            player_extra = extra_pool.copy()

        npc_deck_id = stage.get("opponent_deck_id") or 1
        npc_deck_obj = await self.deck_service.get_character_deck_by_id(npc_deck_id)
        npc_main: List[int] = []
        npc_extra: List[int] = []

        if npc_deck_obj and npc_deck_obj.get("cards"):
            for c in npc_deck_obj["cards"]:
                section = (c.get("section") or "").upper()
                if section == "EXTRA" or is_extra_deck_card(c):
                    npc_extra.extend([c["id"]] * c["quantity"])
                else:
                    npc_main.extend([c["id"]] * c["quantity"])

        if len(npc_main) < 40:
            npc_main = main_pool.copy()
        if not npc_extra:
            npc_extra = extra_pool.copy()

        session = StoryDuelSession(
            player=interaction.user,
            stage=stage,
            player_deck=player_main,
            npc_deck=npc_main,
            player_extra_deck=player_extra,
            npc_extra_deck=npc_extra,
        )
        duel_manager.register_session(interaction.user.id, 0, session)

        duel_view = StoryDuelView(session, self.story_service, self.card_service)
        mode_label = "Scripted Encounter" if session.encounter_type == "SCRIPTED" else "Dynamic AI Duel"
        embed = duel_view.build_embed(
            action_text=f"🌌 **Stage {stage_num}: {stage.get('title', 'Encounter')}** begins! ({mode_label})\nConfront **{session.npc_name}**."
        )
        await interaction.response.send_message(embed=embed, view=duel_view, ephemeral=bool(hidden))
        try:
            duel_view.message = await interaction.original_response()
        except Exception:
            pass

    @app_commands.command(name="story_stages", description="View all stages in Chapter 1: The Genesis of Kustomazi")
    @app_commands.describe(hidden="Whether the stages list should be private")
    async def story_stages_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Displays the campaign stage map with completion status."""
        progress = await self.story_service.get_or_create_player_progress(str(interaction.user.id))
        stages = await self.story_service.get_all_stages(chapter_id=1)

        embed = discord.Embed(
            title="🗺️ Campaign Chronicle — Chapter 1: The Genesis of Kustomazi",
            description="Progress through each stage to master the customs of this realm and claim exclusive cards & titles.",
            color=0x8B5CF6
        )

        highest = progress.get("highest_stage_completed", 0)
        current = progress.get("current_stage_number", 1)

        for s in stages:
            s_num = s["stage_number"]
            if highest >= s_num:
                status_icon = "✅ Completed"
            elif current == s_num:
                status_icon = "📍 Current Objective"
            else:
                status_icon = "🔒 Locked"

            reward = f"🎁 Title: `{s.get('reward_title')}`"
            if s.get("reward_card_name"):
                reward += f" | Card: `{s['reward_card_name']}`"

            enc_mode = " [Scripted]" if s.get("encounter_type") == "SCRIPTED" else " [AI Duel]"
            embed.add_field(
                name=f"Stage {s_num}: {s['title']}{enc_mode} [{status_icon}]",
                value=f"Challenger: **{s['opponent_name']}**\n{reward}",
                inline=False
            )

        embed.set_footer(text="Use /story or /story_duel to challenge your current objective!")
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))

    @app_commands.command(name="story_progress", description="Inspect your campaign achievements and unlocked lore titles")
    @app_commands.describe(hidden="Whether your duelist chronicle should be private")
    async def story_progress_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Displays player's story campaign summary and unlocked titles."""
        progress = await self.story_service.get_or_create_player_progress(str(interaction.user.id))

        embed = discord.Embed(
            title=f"📜 Duelist Chronicle — {interaction.user.display_name}",
            description="Your story progression and achievements across The Land of Kustomazi.",
            color=0x3B82F6
        )

        embed.add_field(
            name="📍 Current Objective",
            value=f"Chapter {progress.get('current_chapter_id', 1)} • Stage {progress.get('current_stage_number', 1)}",
            inline=True
        )
        embed.add_field(
            name="🏆 Total Story Victories",
            value=f"**{progress.get('total_story_wins', 0)}** Wins",
            inline=True
        )
        embed.add_field(
            name="⭐ Highest Stage Cleared",
            value=f"Stage **{progress.get('highest_stage_completed', 0)}**",
            inline=True
        )

        titles = progress.get("titles_list", [])
        titles_formatted = "\n".join([f"• 🏅 **{t}**" for t in titles]) if titles else "*None yet.*"
        embed.add_field(name="🎖️ Earned Story Titles", value=titles_formatted, inline=False)

        if interaction.user.display_avatar:
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Extension Loader Entrypoint)
# =============================================================================

async def setup(bot: commands.Bot):
    """Extension loader entrypoint."""
    await bot.add_cog(StoryCog(bot))

__all__ = [
    "StoryLPModal",
    "StoryPlayCardPickerView",
    "StoryExtraDeckPickerView",
    "StoryDuelView",
    "StoryJourneyView",
    "StoryCog",
    "setup",
]
