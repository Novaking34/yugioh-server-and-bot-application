#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Story Mode RPG & Lore Campaign
=============================================================================
Allows non-competitive and lore-focused duelists to experience the custom card
sagas of The Land of Kustomazi. Loads chapter and stage encounters directly from
the database (no hardcoding), supporting both pre-determined scripted encounters
and dynamic AI duels with real deck RNG and manual duel state controls.
=============================================================================
"""

import discord
from discord import app_commands, ui
from discord.ext import commands
import random
from typing import Optional, List, Dict, Any, Tuple

from services.story_service import StoryService
from services.deck import DeckService
from services.card import CardService
from services.duel_service import duel_manager
from utils import build_story_stage_embed
from production.main.logger import get_logger

logger = get_logger("discord_bot.cogs.story")


# =============================================================================
# 1. STORY DUEL STATE MACHINE (DATABASE-DRIVEN SCRIPTED & AI ENCOUNTERS)
# =============================================================================

class StoryDuelSession:
    """
    Live duel session between a human player and an in-universe Story NPC.
    Loads narrative cues, scripted timelines, or AI behavior directly from
    the database `story_stages` record.
    """

    def __init__(self, player: discord.User, stage: Dict[str, Any], player_deck: List[int], npc_deck: List[int]):
        self.player = player
        self.stage = stage
        self.stage_number = stage.get("stage_number", 1)
        self.npc_name = stage.get("opponent_name", "Story NPC")
        self.encounter_type = stage.get("encounter_type", "AI").upper()
        self.script_data = stage.get("script") or {}

        # Starting Life Points
        boss_starting_lp = stage.get("boss_hp") or 8000
        self.lp = {player.id: 8000, "npc": boss_starting_lp}

        # True Deck RNG Shuffling
        self.player_deck = player_deck.copy()
        self.npc_deck = npc_deck.copy()
        random.shuffle(self.player_deck)
        random.shuffle(self.npc_deck)

        # Opening Hands: Deal 5 cards each with RNG
        self.player_hand: List[int] = [self.player_deck.pop() for _ in range(min(5, len(self.player_deck)))]
        self.npc_hand: List[int] = [self.npc_deck.pop() for _ in range(min(5, len(self.npc_deck)))]

        # Field and GY tracking for both sides
        self.player_field: List[Dict[str, Any]] = []
        self.npc_field: List[Dict[str, Any]] = []
        self.player_gy: List[int] = []
        self.npc_gy: List[int] = []

        self.turn_count = 1
        self.duel_over = False
        self.winner = None
        self.threshold_triggered = False

    def draw_player_card(self) -> Optional[int]:
        """Draws 1 card from player's deck into their private hand."""
        if self.player_deck:
            c = self.player_deck.pop()
            self.player_hand.append(c)
            return c
        return None

    def mill_player_card(self) -> Optional[int]:
        """Sends the top card of player's deck directly to the Graveyard with RNG."""
        if self.player_deck:
            c = self.player_deck.pop()
            self.player_gy.append(c)
            return c
        return None

    def play_player_card(self, card_data: Dict[str, Any]) -> str:
        """Plays a card from player's hand onto their field (if monster) or GY (if spell)."""
        cid = card_data["id"]
        if cid in self.player_hand:
            self.player_hand.remove(cid)
            if card_data.get("card_type") == "Monster":
                self.player_field.append(card_data)
                return (
                    f"⚔️ **{self.player.display_name}** Normal Summoned **{card_data['name']}** "
                    f"[{card_data.get('attribute', 'DIVINE')}] (ATK {card_data.get('atk', 0)} / DEF {card_data.get('def', 0)})!"
                )
            else:
                self.player_gy.append(cid)
                return f"✨ **{self.player.display_name}** activated Spell: **{card_data['name']}**!"
        return "Card not in hand."

    def draw_npc_card(self) -> Optional[int]:
        """Draws 1 card from NPC's deck into the NPC hand using RNG."""
        if self.npc_deck:
            c = self.npc_deck.pop()
            self.npc_hand.append(c)
            return c
        return None

    async def execute_npc_turn(self, card_service: CardService) -> Tuple[str, int]:
        """
        Executes the NPC turn.
        If encounter_type == 'SCRIPTED' and stage script has a defined turn event:
            Executes pre-determined script event loaded from database.
        Otherwise (or in AI mode):
            Dynamic AI: draws a card from deck with RNG, inspects its real hand,
            plays monsters/spells, and computes dynamic attack damage.
        """
        # Step 1: Draw card with RNG
        drawn_cid = self.draw_npc_card()
        if drawn_cid:
            await card_service.track_card_draw(drawn_cid)

        # Step 2: Check for database-loaded scripted event
        if self.encounter_type == "SCRIPTED" and self.script_data:
            turn_key = str(self.turn_count)
            turns_dict = self.script_data.get("turns", {})
            if turn_key in turns_dict:
                turn_info = turns_dict[turn_key]
                dmg = turn_info.get("damage", 800)
                quote_str = f"\n💬 *{turn_info.get('quote')}*" if turn_info.get("quote") else ""
                msg = f"{turn_info.get('play', 'The opponent acts.')}{quote_str}"
                return msg, dmg
            elif "repeat" in self.script_data:
                rep = self.script_data["repeat"]
                dmg = rep.get("damage", 800)
                quote_str = f"\n💬 *{rep.get('quote')}*" if rep.get("quote") else ""
                msg = f"{rep.get('play', 'The opponent presses their advance.')}{quote_str}"
                return msg, dmg

        # Step 3: Dynamic AI Logic (Inspect actual drawn cards from NPC hand)
        monsters = []
        spells = []

        for cid in list(self.npc_hand):
            card = await card_service.get_card_by_query(str(cid))
            if card:
                if card.get("card_type") == "Monster":
                    monsters.append(card)
                else:
                    spells.append(card)

        action_lines = []
        combat_damage = 0

        # AI Action: Play a Spell/Trap if available
        if spells:
            chosen_spell = random.choice(spells)
            self.npc_hand.remove(chosen_spell["id"])
            self.npc_gy.append(chosen_spell["id"])
            await card_service.track_card_play(chosen_spell["id"])
            set_tag = f" [{chosen_spell['set_number']}]" if chosen_spell.get("set_number") else ""
            action_lines.append(f"✨ **{self.npc_name}** activated Spell: **{chosen_spell['name']}**{set_tag}!")

        # AI Action: Normal Summon best monster from hand to field
        if monsters and len(self.npc_field) < 3:
            # Pick monster with highest ATK
            chosen_monster = max(monsters, key=lambda m: (m.get("atk") or 0))
            self.npc_hand.remove(chosen_monster["id"])
            self.npc_field.append(chosen_monster)
            await card_service.track_card_play(chosen_monster["id"])
            set_tag = f" [{chosen_monster['set_number']}]" if chosen_monster.get("set_number") else ""
            action_lines.append(
                f"⚔️ **{self.npc_name}** Normal Summoned **{chosen_monster['name']}**{set_tag} "
                f"[{chosen_monster.get('attribute', 'DIVINE')}] (ATK {chosen_monster.get('atk', 0)})!"
            )

        # AI Action: Battle Phase attack with field monsters
        if self.npc_field:
            lead_monster = self.npc_field[0]
            lead_atk = lead_monster.get("atk") or 1200
            # Calculate battle damage (half ATK for direct story hit, minimum 600, max 2000)
            combat_damage = max(600, min(2000, lead_atk // 2))
            action_lines.append(
                f"💥 **{lead_monster['name']}** attacks directly, dealing **{combat_damage}** battle damage!"
            )
        else:
            # Default direct strike if hand was empty of monsters
            combat_damage = 800
            action_lines.append(f"💥 **{self.npc_name}** launches a direct spiritual assault dealing **{combat_damage}** damage!")

        full_msg = "\n".join(action_lines)
        return full_msg, combat_damage


# =============================================================================
# 2. STORY MANUAL LP MODAL
# =============================================================================

class StoryLPModal(ui.Modal, title="Manual LP Adjustment (Story Duel)"):
    """Allows players or moderators to manually apply arbitrary damage or healing."""

    def __init__(self, session: StoryDuelSession, target: str, view: "StoryDuelView"):
        super().__init__()
        self.session = session
        self.target = target
        self.story_view = view

        target_name = session.player.display_name if target == "player" else session.npc_name
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

        target_name = self.session.player.display_name if self.target == "player" else self.session.npc_name
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


# =============================================================================
# 3. STORY DUEL INTERACTIVE VIEW
# =============================================================================
# 3. STORY DUEL INTERACTIVE VIEW & CARD PICKER
# =============================================================================

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

        self.select_menu = ui.Select(placeholder="Choose card to play onto the field...", options=options)
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction: discord.Interaction):
        cid = int(self.select_menu.values[0])
        card_data = await self.story_view.card_service.get_card_by_query(str(cid))
        if not card_data:
            await interaction.response.send_message("❌ Card not found.", ephemeral=True)
            return

        play_msg = self.session.play_player_card(card_data)
        await self.story_view.card_service.track_card_play(cid)

        # Update main board embed
        embed = self.story_view.build_embed(action_text=play_msg)
        if hasattr(self.story_view, "message") and self.story_view.message:
            try:
                await self.story_view.message.edit(embed=embed, view=self.story_view)
            except Exception:
                pass
        await interaction.response.send_message(f"✅ {play_msg}", ephemeral=True)


class StoryDuelView(ui.View):
    """
    Main interactive board view for Story Mode encounters.
    Combines scripted/AI NPC turns with full manual duel controls.
    """

    def __init__(self, session: StoryDuelSession, story_service: StoryService, card_service: CardService):
        super().__init__(timeout=900)  # 15 minute timeout
        self.session = session
        self.story_service = story_service
        self.card_service = card_service
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
        embed = discord.Embed(
            title=f"{mode_badge} Stage {stage['stage_number']}: {stage['title']}",
            description=f"⚔️ **{self.session.player.display_name}** vs **{self.session.npc_name}**",
            color=color
        )

        p_lp = self.session.lp[self.session.player.id]
        n_lp = self.session.lp["npc"]

        p_bar = "🟩" * max(1, min(10, p_lp // 800))
        n_bar = "🟥" * max(1, min(10, n_lp // 800))

        p_field_str = f"\nField: {', '.join([m['name'] for m in self.session.player_field])}" if self.session.player_field else ""
        n_field_str = f"\nField: {', '.join([m['name'] for m in self.session.npc_field])}" if self.session.npc_field else ""

        embed.add_field(
            name=f"👤 {self.session.player.display_name}",
            value=f"**{p_lp} LP**\nHand: `{len(self.session.player_hand)}` | Deck: `{len(self.session.player_deck)}` | GY: `{len(self.session.player_gy)}`{p_field_str}\n{p_bar}",
            inline=True
        )
        embed.add_field(
            name=f"🤖 {self.session.npc_name}",
            value=f"**{n_lp} LP**\nHand: `{len(self.session.npc_hand)}` | Deck: `{len(self.session.npc_deck)}` | GY: `{len(self.session.npc_gy)}`{n_field_str}\n{n_bar}",
            inline=True
        )

        if action_text:
            embed.add_field(name="📢 Duel Chronicle", value=action_text, inline=False)

        if self.session.duel_over:
            if self.session.winner == self.session.player.id:
                embed.add_field(
                    name="🏆 VICTORY!",
                    value=f"*{stage['outro_dialogue']}*",
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

        # Check threshold dialogue loaded from database script
        if self.session.lp["npc"] <= 4000 and not self.session.threshold_triggered and self.session.lp["npc"] > 0:
            self.session.threshold_triggered = True
            threshold_text = self.session.script_data.get("threshold_4000")
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
        """Inspect private secret hand drawn with RNG from player's deck."""
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
            stat_str = f"ATK {c['atk']}/{c['def']}" if c['card_type'] == 'Monster' else f"{c['card_subtype'] or 'Normal'} {c['card_type']}"
            card_lines.append(f"**{i}. {c['name']}** [{stat_str}]\n*{c['effect_text'][:100]}...*")

        hand_embed = discord.Embed(
            title=f"🎴 Secret Hand — {interaction.user.display_name} ({len(cards)} Cards)",
            description="\n\n".join(card_lines) if card_lines else "*No card details.*",
            color=0x2ECC71
        )
        await interaction.response.send_message(embed=hand_embed, ephemeral=True)

    @ui.button(label="🃏 Draw Card", style=discord.ButtonStyle.secondary, row=0)
    async def draw_card_btn(self, interaction: discord.Interaction, button: ui.Button):
        """Draws 1 card from player's real deck with RNG."""
        if interaction.user.id != self.session.player.id:
            await interaction.response.send_message("❌ This is not your story duel.", ephemeral=True)
            return

        self.message = interaction.message
        drawn = self.session.draw_player_card()
        if drawn:
            await self.card_service.track_card_draw(drawn)
            card_info = await self.card_service.get_card_by_query(str(drawn))
            cname = card_info["name"] if card_info else f"Card #{drawn}"
            await interaction.response.send_message(f"🎴 You drew: **{cname}**! (Secret Hand)", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Your deck is empty!", ephemeral=True)

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
            "Select a card from your hand to summon or activate:",
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
            await interaction.response.send_message("⚠️ Your deck is empty!", ephemeral=True)
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


# =============================================================================
# 4. STORY JOURNEY INTERACTION VIEW
# =============================================================================

class StoryJourneyView(ui.View):
    """Hub view for browsing story stages and launching encounters."""

    def __init__(self, user: discord.User, stage: dict, progress: dict, story_service: StoryService, deck_service: DeckService, card_service: CardService):
        super().__init__(timeout=180)
        self.user = user
        self.stage = stage
        self.progress = progress
        self.story_service = story_service
        self.deck_service = deck_service
        self.card_service = card_service

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

        # Fetch player deck or fallback to Set 1 pool
        player_deck = await self.deck_service.get_player_card_ids(str(interaction.user.id))
        if len(player_deck) < 5:
            cards = await self.card_service.get_all_cards()
            player_deck = [c["id"] for c in cards] * 2

        # Fetch NPC deck
        npc_deck_id = self.stage.get("opponent_deck_id") or 1
        npc_deck_obj = await self.deck_service.get_character_deck_by_id(npc_deck_id)
        if npc_deck_obj and npc_deck_obj.get("cards"):
            npc_deck = []
            for c in npc_deck_obj["cards"]:
                npc_deck.extend([c["id"]] * c["quantity"])
        else:
            cards = await self.card_service.get_all_cards()
            npc_deck = [c["id"] for c in cards] * 2

        session = StoryDuelSession(interaction.user, self.stage, player_deck, npc_deck)
        duel_manager.register_session(interaction.user.id, 0, session)

        duel_view = StoryDuelView(session, self.story_service, self.card_service)
        mode_label = "Scripted Encounter" if session.encounter_type == "SCRIPTED" else "Dynamic AI Duel"
        embed = duel_view.build_embed(
            action_text=f"🌌 **{self.stage['title']}** begins! ({mode_label})\nConfront **{session.npc_name}**."
        )
        await interaction.response.send_message(embed=embed, view=duel_view)
        try:
            duel_view.message = await interaction.original_response()
        except Exception:
            pass


# =============================================================================
# 5. STORY COG COMMANDS
# =============================================================================

class StoryCog(commands.Cog, name="Story"):
    """Commands for experiencing the in-server custom card RPG campaign."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.story_service = StoryService()
        self.deck_service = DeckService()
        self.card_service = CardService()

    @app_commands.command(name="story", description="Embark on your journey in The Land of Kustomazi campaign")
    async def story_journey_command(self, interaction: discord.Interaction):
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
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="story_duel", description="Directly launch the story duel encounter for your current stage")
    async def story_duel_direct_command(self, interaction: discord.Interaction):
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

        player_deck = await self.deck_service.get_player_card_ids(str(interaction.user.id))
        if len(player_deck) < 5:
            cards = await self.card_service.get_all_cards()
            player_deck = [c["id"] for c in cards] * 2

        npc_deck_id = stage.get("opponent_deck_id") or 1
        npc_deck_obj = await self.deck_service.get_character_deck_by_id(npc_deck_id)
        if npc_deck_obj and npc_deck_obj.get("cards"):
            npc_deck = []
            for c in npc_deck_obj["cards"]:
                npc_deck.extend([c["id"]] * c["quantity"])
        else:
            cards = await self.card_service.get_all_cards()
            npc_deck = [c["id"] for c in cards] * 2

        session = StoryDuelSession(interaction.user, stage, player_deck, npc_deck)
        duel_manager.register_session(interaction.user.id, 0, session)

        duel_view = StoryDuelView(session, self.story_service, self.card_service)
        mode_label = "Scripted Encounter" if session.encounter_type == "SCRIPTED" else "Dynamic AI Duel"
        embed = duel_view.build_embed(
            action_text=f"🌌 **Stage {stage_num}: {stage['title']}** begins! ({mode_label})\nConfront **{session.npc_name}**."
        )
        await interaction.response.send_message(embed=embed, view=duel_view)
        try:
            duel_view.message = await interaction.original_response()
        except Exception:
            pass

    @app_commands.command(name="story_stages", description="View all stages in Chapter 1: The Genesis of Kustomazi")
    async def story_stages_command(self, interaction: discord.Interaction):
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
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="story_progress", description="Inspect your campaign achievements and unlocked lore titles")
    async def story_progress_command(self, interaction: discord.Interaction):
        """Displays player's story campaign summary and unlocked titles."""
        progress = await self.story_service.get_or_create_player_progress(str(interaction.user.id))

        embed = discord.Embed(
            title=f"📜 Duelist Chronicle — {interaction.user.display_name}",
            description="Your story progression and achievements across The Land of Kustomazi.",
            color=0x3B82F6
        )

        embed.add_field(
            name="📍 Current Objective",
            value=f"Chapter {progress['current_chapter_id']} • Stage {progress['current_stage_number']}",
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

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Extension loader entrypoint."""
    await bot.add_cog(StoryCog(bot))
