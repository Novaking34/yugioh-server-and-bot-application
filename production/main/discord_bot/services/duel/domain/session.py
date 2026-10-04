# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.domain.session
Description:
    Live Yu-Gi-Oh! Duel Session State Machine & Board Binding.
    Encapsulates life points, deck states, hands, graveyards, field boards,
    turn cycles, phases, and victory conditions for both PvP and Story mode matches.

Architectural Classification:
    Layer 1 (L1) - Domain Component
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import random
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.domain.duel_board import DuelBoard
from production.main.logger import get_logger
from services.deck.foundation.classifier import partition_card_ids
from ..foundation.constants import (
    DEFAULT_OPENING_HAND_SIZE,
    DEFAULT_STARTING_LP,
    MATCH_TYPE_RANKED,
    PHASE_BATTLE,
    PHASE_DRAW,
    PHASE_END,
    PHASE_MAIN_1,
    PHASE_MAIN_2,
    PHASE_STANDBY,
)

logger = get_logger("discord_bot.services.duel.session")


# =============================================================================
# BLOCK 3: BODY BLOCK (Core Duel Session State Machine)
# =============================================================================

class DuelSession:
    """
    Encapsulates the live state machine of an active match between two duelists
    (Player vs Player or Player vs NPC/Story AI).
    """

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Constructor & Match Initialization
    # -------------------------------------------------------------------------
    def __init__(
        self,
        p1: Any,
        p2: Any,
        p1_deck: List[int],
        p2_deck: List[int],
        match_type: str = MATCH_TYPE_RANKED,
        p1_deck_name: Optional[str] = None,
        p2_deck_name: Optional[str] = None,
        starting_lp: int = DEFAULT_STARTING_LP,
        opening_hand_size: int = DEFAULT_OPENING_HAND_SIZE,
        p1_extra_deck: Optional[List[int]] = None,
        p2_extra_deck: Optional[List[int]] = None,
    ) -> None:
        self.p1 = p1
        self.p2 = p2
        self.match_type = match_type.upper()
        self.deck_names: Dict[int, Optional[str]] = {p1.id: p1_deck_name, p2.id: p2_deck_name}
        self.lp: Dict[int, int] = {p1.id: starting_lp, p2.id: starting_lp}

        # Strict MR5 Deck Partitioning: Extra Deck monsters can NEVER be in Main Deck or in Hand
        p1_main, p1_extra = partition_card_ids(p1_deck)
        p2_main, p2_extra = partition_card_ids(p2_deck)
        if p1_extra_deck:
            p1_extra.extend(p1_extra_deck)
        if p2_extra_deck:
            p2_extra.extend(p2_extra_deck)

        # Keep original decks for post-match card telemetry and audit
        self.original_decks: Dict[int, List[int]] = {p1.id: list(p1_main), p2.id: list(p2_main)}
        self.decks: Dict[int, List[int]] = {p1.id: list(p1_main), p2.id: list(p2_main)}
        self.extra_decks: Dict[int, List[int]] = {p1.id: list(p1_extra), p2.id: list(p2_extra)}
        random.shuffle(self.decks[p1.id])
        random.shuffle(self.decks[p2.id])

        # Opening Hands: Deal 5 cards each strictly from the Main Deck
        self.hands: Dict[int, List[int]] = {
            p1.id: [self.decks[p1.id].pop() for _ in range(min(opening_hand_size, len(self.decks[p1.id])))],
            p2.id: [self.decks[p2.id].pop() for _ in range(min(opening_hand_size, len(self.decks[p2.id])))]
        }

        # Legacy slot tracking for backwards compatibility with cogs
        self.fields: Dict[int, Dict[str, list]] = {
            p1.id: {"monsters": [], "spells": []},
            p2.id: {"monsters": [], "spells": []}
        }
        self.gy: Dict[int, List[int]] = {p1.id: [], p2.id: []}
        self.banished: Dict[int, List[int]] = {p1.id: [], p2.id: []}

        # Board state binding (symmetrical Master Rule field mats)
        p1_name = getattr(p1, "display_name", str(p1))
        p2_name = getattr(p2, "display_name", str(p2))
        self.boards: Dict[int, DuelBoard] = {
            p1.id: DuelBoard(p1_name),
            p2.id: DuelBoard(p2_name)
        }
        self.boards[p1.id].extra_deck = self.extra_decks[p1.id]
        self.boards[p2.id].extra_deck = self.extra_decks[p2.id]

        # Random starting turn player
        self.turn_player: Any = random.choice([p1, p2])
        self.turn_count: int = 1
        self.current_phase: str = PHASE_DRAW
        self.normal_summon_used: Dict[int, bool] = {p1.id: False, p2.id: False}
        self.duel_over: bool = False
        self.winner: Optional[Any] = None
        self.match_result: Optional[Dict[str, Any]] = None

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Card Draw & Mill Actions
    # -------------------------------------------------------------------------
    def draw_card(self, player_id: int) -> Optional[int]:
        """
        Draws 1 card from deck into hand.
        Returns card passcode or None if deck is empty (Deck Out).
        """
        if self.decks[player_id]:
            c = self.decks[player_id].pop()
            self.hands[player_id].append(c)
            return c
        return None

    def mill_card(self, player_id: int) -> Optional[int]:
        """
        Sends the top card from player's deck directly to Graveyard.
        Updates both local GY list and DuelBoard state.
        """
        if self.decks[player_id]:
            c = self.decks[player_id].pop()
            self.gy[player_id].append(c)
            if player_id in self.boards:
                self.boards[player_id].send_to_gy(c)
            return c
        return None

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Turn Cycles & Phase Progression
    # -------------------------------------------------------------------------
    def advance_phase(self) -> str:
        """
        Advances the current phase sequentially:
        DRAW -> STANDBY -> MAIN_1 -> BATTLE -> MAIN_2 -> END -> DRAW (next turn).
        """
        phase_flow = {
            PHASE_DRAW: PHASE_STANDBY,
            PHASE_STANDBY: PHASE_MAIN_1,
            PHASE_MAIN_1: PHASE_BATTLE,
            PHASE_BATTLE: PHASE_MAIN_2,
            PHASE_MAIN_2: PHASE_END,
            PHASE_END: PHASE_DRAW,
        }
        next_p = phase_flow.get(self.current_phase, PHASE_DRAW)
        if next_p == PHASE_DRAW:
            # End Phase to next turn's Draw Phase
            self.next_turn()
        else:
            self.current_phase = next_p

        return self.current_phase

    def next_turn(self) -> Tuple[Any, int]:
        """
        Transitions to the next turn:
        - Toggles active turn player
        - Increments turn count
        - Resets normal summon flags
        - Resets phase to DRAW
        - Automatically draws card for active player (Turn 2+)
        """
        self.turn_player = self.p2 if self.turn_player.id == self.p1.id else self.p1
        self.turn_count += 1
        self.current_phase = PHASE_DRAW
        self.normal_summon_used[self.p1.id] = False
        self.normal_summon_used[self.p2.id] = False

        # Turn 1 player skips their first draw; all subsequent turns draw 1 card
        drawn = self.draw_card(self.turn_player.id)
        if drawn is None and len(self.decks[self.turn_player.id]) == 0:
            # Deck Out Victory for opponent
            self.duel_over = True
            self.winner = self.get_opponent(self.turn_player.id)
            logger.info(f"Duel concluded by Deck Out on Turn {self.turn_count}. Winner: {self.winner.id}")

        return self.turn_player, self.turn_count

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Life Point Calculations & Match Conclusion
    # -------------------------------------------------------------------------
    def adjust_lp(self, target_player_id: int, delta: int, reason: str = "Manual Adjustment") -> Tuple[int, int, bool]:
        """
        Adjusts Life Points for a player. Checks for victory conditions (LP <= 0).

        Args:
            target_player_id: The user ID receiving LP modification.
            delta: Positive integer to heal, negative integer to damage.
            reason: Context description for the duel log.

        Returns:
            Tuple of (old_lp, new_lp, is_duel_concluded).
        """
        old_lp = self.lp.get(target_player_id, 0)
        new_lp = max(0, old_lp + delta)
        self.lp[target_player_id] = new_lp

        if new_lp <= 0 and not self.duel_over:
            self.duel_over = True
            self.winner = self.get_opponent(target_player_id)
            return old_lp, new_lp, True

        return old_lp, new_lp, False

    def surrender(self, conceding_player_id: int) -> Tuple[Any, str]:
        """
        Processes a player surrender. Automatically awards victory to opponent.

        Returns:
            Tuple of (winner_user_instance, summary_text).
        """
        self.duel_over = True
        self.winner = self.get_opponent(conceding_player_id)
        conceding_user = self.p1 if conceding_player_id == self.p1.id else self.p2
        winner_name = getattr(self.winner, "display_name", str(self.winner))
        conceding_name = getattr(conceding_user, "display_name", str(conceding_user))
        summary = f"{conceding_name} surrendered. {winner_name} emerges victorious!"
        return self.winner, summary

    def get_opponent(self, player_id: int) -> Any:
        """Returns the opposing participant given a player's ID."""
        return self.p2 if player_id == self.p1.id else self.p1

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current match state into a dictionary snapshot."""
        return {
            "match_type": self.match_type,
            "turn_count": self.turn_count,
            "current_phase": self.current_phase,
            "turn_player_id": self.turn_player.id,
            "p1_id": self.p1.id,
            "p2_id": self.p2.id,
            "p1_lp": self.lp[self.p1.id],
            "p2_lp": self.lp[self.p2.id],
            "p1_hand_count": len(self.hands[self.p1.id]),
            "p2_hand_count": len(self.hands[self.p2.id]),
            "p1_deck_count": len(self.decks[self.p1.id]),
            "p2_deck_count": len(self.decks[self.p2.id]),
            "duel_over": self.duel_over,
            "winner_id": getattr(self.winner, "id", None) if self.winner else None,
        }


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DuelSession",
]
