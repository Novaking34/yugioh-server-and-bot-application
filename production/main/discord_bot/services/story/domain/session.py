#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.story.domain.session
Description:
    Live Yu-Gi-Oh! Story Duel State Machine & Encounter Simulation Engine.
    Manages Player vs Story NPC matches, enforces strict Master Rule 5 deck
    partitioning (Main Deck vs Extra Deck), drives scripted encounter timelines,
    and runs dynamic NPC combat AI.

Architectural Classification:
    Layer 1 (L1) - Domain Component
    Subsystem: Story & Lore Campaign RPG
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import random
from typing import Any, Dict, List, Optional, Tuple, Union

from production.main.logger import get_logger
from services.deck.foundation.classifier import is_extra_deck_card, partition_card_ids
from ..foundation.constants import (
    DEFAULT_AI_STRIKE_DAMAGE,
    DEFAULT_STARTING_BOSS_HP,
    DEFAULT_STARTING_HAND_SIZE,
    DEFAULT_STARTING_PLAYER_HP,
    ENCOUNTER_TYPE_AI,
    ENCOUNTER_TYPE_SCRIPTED,
    MAX_COMBAT_DAMAGE,
    MIN_COMBAT_DAMAGE,
)

logger = get_logger("discord_bot.services.story.session")

# =============================================================================
# BLOCK 3: BODY BLOCK (Story Duel Session State Machine)
# =============================================================================

class StoryDuelSession:
    """
    Live duel session between a human player and an in-universe Story NPC.
    Loads narrative cues, scripted timelines, or AI behavior directly from
    the database `story_stages` record.

    Enforces Master Rule 5 Deck Partitioning:
    - Main Deck: Normal/Effect/Ritual monsters, Spells, Traps. Hand deals ONLY from here.
    - Extra Deck: Fusion (Mohousha, The Great Kasutamaiza), Synchro, Link. NEVER in hand.
    """

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Constructor & MR5 Deck Initialization
    # -------------------------------------------------------------------------
    def __init__(
        self,
        player: Any,
        stage: Dict[str, Any],
        player_deck: List[int],
        npc_deck: List[int],
        player_extra_deck: Optional[List[int]] = None,
        npc_extra_deck: Optional[List[int]] = None,
    ) -> None:
        self.player = player
        self.stage = stage
        self.stage_number = stage.get("stage_number", 1)
        self.npc_name = stage.get("opponent_name", "Story NPC")
        self.encounter_type = (stage.get("encounter_type") or ENCOUNTER_TYPE_AI).upper()
        self.script_data = stage.get("script") or {}

        # Starting Life Points: Tiered scaling (4000 LP skirmish vs 6000 LP midboss vs 8000 LP apex)
        boss_starting_lp = stage.get("boss_hp") or DEFAULT_STARTING_BOSS_HP
        script = stage.get("script") or {}
        player_starting_lp = stage.get("player_hp") or script.get("player_hp") or (boss_starting_lp if boss_starting_lp <= 4000 else DEFAULT_STARTING_PLAYER_HP)
        self.npc_max_hp = int(boss_starting_lp)
        self.player_max_hp = int(player_starting_lp)
        self.lp = {player.id: self.player_max_hp, "npc": self.npc_max_hp}

        # MR5 Deck Partitioning: Guarantee Extra Deck monsters are NEVER in Main Deck or dealt to hand
        p_main, p_extra = partition_card_ids(player_deck)
        n_main, n_extra = partition_card_ids(npc_deck)
        if player_extra_deck:
            p_extra.extend(player_extra_deck)
        if npc_extra_deck:
            n_extra.extend(npc_extra_deck)

        self.player_deck: List[int] = list(p_main)
        self.player_extra_deck: List[int] = list(p_extra)
        self.npc_deck: List[int] = list(n_main)
        self.npc_extra_deck: List[int] = list(n_extra)

        # Shuffle Main Decks
        random.shuffle(self.player_deck)
        random.shuffle(self.npc_deck)

        # Opening Hands: Deal 5 cards each strictly from the Main Deck
        self.player_hand: List[int] = [
            self.player_deck.pop()
            for _ in range(min(DEFAULT_STARTING_HAND_SIZE, len(self.player_deck)))
        ]
        self.npc_hand: List[int] = [
            self.npc_deck.pop()
            for _ in range(min(DEFAULT_STARTING_HAND_SIZE, len(self.npc_deck)))
        ]

        # Field, GY, Banished tracking for both sides
        self.player_field: List[Dict[str, Any]] = []
        self.npc_field: List[Dict[str, Any]] = []
        self.player_gy: List[int] = []
        self.npc_gy: List[int] = []
        self.player_banished: List[int] = []
        self.npc_banished: List[int] = []

        self.turn_count = 1
        self.duel_over = False
        self.winner: Optional[Any] = None
        self.threshold_triggered = False

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Card Draw & Mill Actions
    # -------------------------------------------------------------------------
    def draw_player_card(self) -> Optional[int]:
        """Draws 1 card from player's Main Deck into their private hand."""
        if self.player_deck:
            c = self.player_deck.pop()
            self.player_hand.append(c)
            return c
        return None

    def mill_player_card(self) -> Optional[int]:
        """Sends the top card of player's Main Deck directly to the Graveyard with RNG."""
        if self.player_deck:
            c = self.player_deck.pop()
            self.player_gy.append(c)
            return c
        return None

    def draw_npc_card(self) -> Optional[int]:
        """Draws 1 card from NPC's Main Deck into the NPC hand using RNG."""
        if self.npc_deck:
            c = self.npc_deck.pop()
            self.npc_hand.append(c)
            return c
        return None

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Player Card Play & Summon Actions
    # -------------------------------------------------------------------------
    def play_player_card(self, card_data: Dict[str, Any]) -> str:
        """Plays a card from player's hand onto their field (if monster) or GY (if spell)."""
        cid = card_data.get("id")
        if not cid:
            return "Invalid card."

        # Extra Deck monsters cannot be played from Main Deck hand
        if is_extra_deck_card(card_data):
            return f"❌ **{card_data.get('name', 'Monster')}** is an Extra Deck monster and must be Special Summoned from the Extra Deck!"

        if cid in self.player_hand:
            self.player_hand.remove(cid)
            card_type = card_data.get("card_type")
            if card_type == "Monster":
                self.player_field.append(card_data)
                return (
                    f"⚔️ **{getattr(self.player, 'display_name', str(self.player))}** Normal Summoned **{card_data['name']}** "
                    f"[{card_data.get('attribute', 'DIVINE')}] (ATK {card_data.get('atk', 0)} / DEF {card_data.get('def', 0)})!"
                )
            else:
                self.player_gy.append(cid)
                return f"✨ **{getattr(self.player, 'display_name', str(self.player))}** activated Spell: **{card_data['name']}**!"
        return "Card not in hand."

    def special_summon_extra_monster(self, card_data: Dict[str, Any]) -> str:
        """Special Summons an Extra Deck monster (Fusion, Synchro, Link) onto the field."""
        cid = card_data.get("id")
        if not cid:
            return "Invalid card."

        if cid in self.player_extra_deck:
            self.player_extra_deck.remove(cid)
            self.player_field.append(card_data)
            subtype = card_data.get("card_subtype", "Fusion")
            return (
                f"🌀 **{getattr(self.player, 'display_name', str(self.player))}** Special Summoned from Extra Deck: "
                f"**{card_data['name']}** ({subtype}) [ATK {card_data.get('atk', 0)} / DEF {card_data.get('def', 0)}]!"
            )
        return "Card not found in Extra Deck."

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: NPC Turn Execution (Scripted vs Dynamic AI)
    # -------------------------------------------------------------------------
    async def execute_npc_turn(self, card_service: Any) -> Tuple[str, int]:
        """
        Executes the NPC turn.
        If encounter_type == 'SCRIPTED' and stage script has a defined turn event:
            Executes pre-determined script event loaded from database.
        Otherwise (or in AI mode):
            Dynamic AI: draws a card from deck with RNG, inspects its real hand,
            plays monsters/spells, and computes dynamic attack damage.
        """
        # Step 1: Draw card with RNG strictly from Main Deck
        drawn_cid = self.draw_npc_card()
        if drawn_cid and hasattr(card_service, "track_card_draw"):
            try:
                await card_service.track_card_draw(drawn_cid)
            except Exception:
                pass

        # Step 2: Check for database-loaded scripted event
        if self.encounter_type == ENCOUNTER_TYPE_SCRIPTED and self.script_data:
            turn_key = str(self.turn_count)
            turns_dict = self.script_data.get("turns", {})
            if turn_key in turns_dict:
                turn_info = turns_dict[turn_key]
                dmg = turn_info.get("damage", DEFAULT_AI_STRIKE_DAMAGE)
                quote_str = f"\n💬 *{turn_info.get('quote')}*" if turn_info.get("quote") else ""
                msg = f"{turn_info.get('play', 'The opponent acts.')}{quote_str}"
                return msg, dmg
            elif "repeat" in self.script_data:
                rep = self.script_data["repeat"]
                dmg = rep.get("damage", DEFAULT_AI_STRIKE_DAMAGE)
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
            if hasattr(card_service, "track_card_play"):
                try:
                    await card_service.track_card_play(chosen_spell["id"])
                except Exception:
                    pass
            set_tag = f" [{chosen_spell['set_number']}]" if chosen_spell.get("set_number") else ""
            action_lines.append(f"✨ **{self.npc_name}** activated Spell: **{chosen_spell['name']}**{set_tag}!")

        # AI Action: Normal Summon best monster from hand to field
        if monsters and len(self.npc_field) < 3:
            # Pick monster with highest ATK
            chosen_monster = max(monsters, key=lambda m: (m.get("atk") or 0))
            self.npc_hand.remove(chosen_monster["id"])
            self.npc_field.append(chosen_monster)
            if hasattr(card_service, "track_card_play"):
                try:
                    await card_service.track_card_play(chosen_monster["id"])
                except Exception:
                    pass
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
            combat_damage = max(MIN_COMBAT_DAMAGE, min(MAX_COMBAT_DAMAGE, lead_atk // 2))
            action_lines.append(
                f"💥 **{lead_monster['name']}** attacks directly, dealing **{combat_damage}** battle damage!"
            )
        else:
            # Default direct strike if hand was empty of monsters
            combat_damage = DEFAULT_AI_STRIKE_DAMAGE
            action_lines.append(f"💥 **{self.npc_name}** launches a direct spiritual assault dealing **{combat_damage}** damage!")

        full_msg = "\n".join(action_lines)
        return full_msg, combat_damage


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "StoryDuelSession",
]
