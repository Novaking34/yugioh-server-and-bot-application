# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.domain.manager
Description:
    Active Live Duel Session Concurrency Registry & Recovery Manager.
    Maintains thread-safe in-memory participant-to-session mappings,
    enforcing mutual exclusion so duelists cannot start concurrent duels,
    and provides administrative rescue operations for stuck matches.

Architectural Classification:
    Layer 1 (L1) - Domain Component
    Subsystem: Duel Management & State Isolation
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional, Set
from production.main.logger import get_logger

logger = get_logger("discord_bot.services.duel.manager")


# =============================================================================
# BLOCK 3: BODY BLOCK (Core Duel Manager Orchestrator)
# =============================================================================

class DuelManager:
    """
    Manages active live duel sessions across Discord channels.
    Maintains thread-safe in-memory participant-to-session mappings,
    enforcing mutual exclusion so duelists cannot start concurrent duels.
    """

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Constructor & State Storage Primitives
    # -------------------------------------------------------------------------
    def __init__(self) -> None:
        # Maps user_id -> active duel session instance
        self._user_to_session: Dict[int, Any] = {}
        # Set of active unique duel session instances
        self._active_sessions: Set[Any] = set()

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Session Queries & Concurrency Predicates
    # -------------------------------------------------------------------------
    def is_user_dueling(self, user_id: int) -> bool:
        """
        Checks if a user is currently engaged in an active match.

        Args:
            user_id: The Discord snowflake user ID to inspect.

        Returns:
            True if the user is already bound to an active session, else False.
        """
        return user_id in self._user_to_session

    def get_session(self, user_id: int) -> Optional[Any]:
        """
        Retrieves the active duel session for a user.

        Args:
            user_id: The Discord snowflake user ID.

        Returns:
            The active session instance if found, or None.
        """
        return self._user_to_session.get(user_id)

    @property
    def active_duel_count(self) -> int:
        """Returns the total number of concurrent active duel sessions."""
        return len(self._active_sessions)

    def get_all_active_sessions(self) -> List[Any]:
        """Returns a snapshot list of all currently registered active duel sessions."""
        return list(self._active_sessions)

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Session Lifecycle Handlers (Registration & Teardown)
    # -------------------------------------------------------------------------
    def register_session(self, p1_id: int, p2_id: int, session: Any) -> None:
        """
        Registers a live duel session for two players (or player vs AI/story).

        Args:
            p1_id: Discord user ID of player 1 (or challenger).
            p2_id: Discord user ID of player 2 (or 0 for AI/Story encounter).
            session: The active DuelSession instance.
        """
        self._user_to_session[p1_id] = session
        if p2_id != 0:
            self._user_to_session[p2_id] = session
        self._active_sessions.add(session)
        logger.info(
            f"Registered duel session for players {p1_id} and {p2_id}. "
            f"Total active matches: {len(self._active_sessions)}"
        )

    def unregister_session(self, session: Any) -> None:
        """
        Cleans up and removes a duel session upon normal conclusion, surrender, or timeout.

        Args:
            session: The DuelSession instance to unregister.
        """
        if session in self._active_sessions:
            self._active_sessions.remove(session)

        # Remove mapping for all users mapped to this session
        to_remove = [uid for uid, s in self._user_to_session.items() if s is session]
        for uid in to_remove:
            self._user_to_session.pop(uid, None)

        logger.info(
            f"Unregistered duel session. Remaining active matches: {len(self._active_sessions)}"
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Administrative Intervention & Recovery Handlers
    # -------------------------------------------------------------------------
    def force_reset_user(self, user_id: int) -> bool:
        """
        Administrative recovery utility to terminate a stuck duel for a specific user.

        Args:
            user_id: The Discord snowflake user ID to release.

        Returns:
            True if an active session was found and unregistered, False otherwise.
        """
        session = self._user_to_session.get(user_id)
        if session:
            self.unregister_session(session)
            return True
        return False

    def clear_all(self) -> int:
        """
        Emergency reset for all active duel sessions across the entire server.

        Returns:
            The number of purged duel sessions.
        """
        count = len(self._active_sessions)
        self._user_to_session.clear()
        self._active_sessions.clear()
        logger.warning(f"Cleared all active duel sessions ({count} sessions purged).")
        return count


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DuelManager",
]
