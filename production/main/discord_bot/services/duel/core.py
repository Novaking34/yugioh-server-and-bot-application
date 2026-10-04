# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.core
Description:
    Central Duel Service Engine & Match Orchestrator.
    Coordinates match initialization, concurrency validation, DuelSession lifecycle,
    board state synchronization, victory declarations, and telemetry recording.

Architectural Classification:
    Layer 1 (L1) - Core Service Orchestrator
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional, Tuple

from production.main.logger import get_logger
from .foundation.constants import (
    DEFAULT_OPENING_HAND_SIZE,
    DEFAULT_STARTING_LP,
    MATCH_TYPE_CASUAL,
    MATCH_TYPE_RANKED,
)
from .foundation.types import MatchResultPayload
from .domain.manager import DuelManager
from .domain.session import DuelSession

logger = get_logger("discord_bot.services.duel.core")


# =============================================================================
# BLOCK 3: BODY BLOCK (Core Duel Service Orchestrator)
# =============================================================================

class DuelService:
    """
    Central orchestrator service managing live duel lifecycles, matchmaking concurrency,
    and post-match rating telemetry updates.
    """

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Constructor & Dependency Injection
    # -------------------------------------------------------------------------
    def __init__(
        self,
        manager: Optional[DuelManager] = None,
        rating_service: Optional[Any] = None,
    ) -> None:
        self.manager: DuelManager = manager or DuelManager()
        self.rating_service: Optional[Any] = rating_service

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Match Creation & Concurrency Validation
    # -------------------------------------------------------------------------
    def start_duel(
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
    ) -> DuelSession:
        """
        Validates concurrency and initializes an active DuelSession for two participants.

        Args:
            p1: Participant 1 instance (challenger).
            p2: Participant 2 instance (challenged or AI).
            p1_deck: List of card passcodes for player 1 Main Deck.
            p2_deck: List of card passcodes for player 2 Main Deck.
            match_type: Match category ("RANKED", "CASUAL", "STORY", "PRACTICE").
            p1_deck_name: Optional custom deck name for player 1.
            p2_deck_name: Optional custom deck name for player 2.
            starting_lp: Starting life points (default 8000).
            opening_hand_size: Opening hand size (default 5).
            p1_extra_deck: Optional Extra Deck card passcodes for player 1.
            p2_extra_deck: Optional Extra Deck card passcodes for player 2.

        Returns:
            The initialized DuelSession instance.

        Raises:
            ValueError: If either participant is already engaged in an active duel.
        """
        if self.manager.is_user_dueling(p1.id):
            raise ValueError(f"Player {p1.id} is already in an active duel match.")
        if getattr(p2, "id", 0) != 0 and self.manager.is_user_dueling(p2.id):
            raise ValueError(f"Player {p2.id} is already in an active duel match.")

        session = DuelSession(
            p1=p1,
            p2=p2,
            p1_deck=p1_deck,
            p2_deck=p2_deck,
            match_type=match_type,
            p1_deck_name=p1_deck_name,
            p2_deck_name=p2_deck_name,
            starting_lp=starting_lp,
            opening_hand_size=opening_hand_size,
            p1_extra_deck=p1_extra_deck,
            p2_extra_deck=p2_extra_deck,
        )

        p2_id = getattr(p2, "id", 0)
        self.manager.register_session(p1.id, p2_id, session)
        logger.info(
            f"DuelService successfully initiated {match_type} match between "
            f"{p1.id} and {p2_id}."
        )
        return session

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Match Resolution & Post-Game Telemetry
    # -------------------------------------------------------------------------
    async def conclude_duel(
        self,
        session: DuelSession,
        winner_id: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Finalizes an active match, unregisters the session, and triggers rating updates.

        Args:
            session: The DuelSession instance.
            winner_id: String ID of winning player, "DRAW", or None.
            summary: Human-readable victory summary description.

        Returns:
            The match recording result dict from RatingService, or None.
        """
        session.duel_over = True
        self.manager.unregister_session(session)

        # Lazy load or use injected RatingService
        if self.rating_service is None:
            try:
                from ..rating import RatingService
                self.rating_service = RatingService()
            except Exception as e:
                logger.warning(f"Could not load RatingService for match recording: {e}")
                return None

        try:
            p1_name = getattr(session.p1, "display_name", str(session.p1))
            p2_name = getattr(session.p2, "display_name", str(session.p2))
            res = await self.rating_service.record_duel_match(
                p1_id=str(session.p1.id),
                p2_id=str(session.p2.id),
                winner_id=winner_id,
                match_type=session.match_type,
                turns=session.turn_count,
                summary=summary or f"Match concluded on turn {session.turn_count}.",
                p1_deck=session.original_decks.get(session.p1.id, []),
                p2_deck=session.original_decks.get(session.p2.id, []),
                p1_name=p1_name,
                p2_name=p2_name,
                p1_deck_name=session.deck_names.get(session.p1.id),
                p2_deck_name=session.deck_names.get(session.p2.id),
            )
            session.match_result = res
            return res
        except Exception as e:
            logger.error(f"Error recording duel match telemetry: {e}", exc_info=True)
            return None

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Concurrency & State Queries
    # -------------------------------------------------------------------------
    def is_user_dueling(self, user_id: int) -> bool:
        """Returns True if user is currently in a match."""
        return self.manager.is_user_dueling(user_id)

    def get_session(self, user_id: int) -> Optional[DuelSession]:
        """Retrieves active DuelSession for a user."""
        return self.manager.get_session(user_id)

    @property
    def active_duel_count(self) -> int:
        """Returns total active duels."""
        return self.manager.active_duel_count

    def force_reset_user(self, user_id: int) -> bool:
        """Administrative termination of stuck match."""
        return self.manager.force_reset_user(user_id)

    def clear_all(self) -> int:
        """Purges all active duel matches."""
        return self.manager.clear_all()


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DuelService",
]
