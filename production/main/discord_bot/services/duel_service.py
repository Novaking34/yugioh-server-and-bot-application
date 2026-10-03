#!/usr/bin/env python3
"""
=============================================================================
Duel Service: Active Duel Session Management & Recovery
=============================================================================
Maintains in-memory live duel sessions with concurrency guards, state tracking,
and administrative recovery utilities so stuck matches can be safely reset.
=============================================================================
"""

from typing import Dict, Any, Optional
from production.main.logger import get_logger

logger = get_logger("discord_bot.services.duel")


class DuelManager:
    """Manages active live duel state across discord channels."""

    def __init__(self):
        # Maps user_id -> active duel session
        self._user_to_session: Dict[int, Any] = {}
        # Set of active session objects
        self._active_sessions = set()

    def is_user_dueling(self, user_id: int) -> bool:
        """Checks if a user is currently engaged in an active match."""
        return user_id in self._user_to_session

    def get_session(self, user_id: int) -> Optional[Any]:
        """Retrieves active duel session for a user."""
        return self._user_to_session.get(user_id)

    def register_session(self, p1_id: int, p2_id: int, session: Any):
        """Registers a live duel session for two players."""
        self._user_to_session[p1_id] = session
        self._user_to_session[p2_id] = session
        self._active_sessions.add(session)
        logger.info(f"Registered duel session for players {p1_id} and {p2_id}. Total active: {len(self._active_sessions)}")

    def unregister_session(self, session: Any):
        """Cleans up session upon duel conclusion or surrender."""
        if session in self._active_sessions:
            self._active_sessions.remove(session)

        # Remove mapping for users
        to_remove = [uid for uid, s in self._user_to_session.items() if s is session]
        for uid in to_remove:
            self._user_to_session.pop(uid, None)

        logger.info(f"Unregistered duel session. Remaining active: {len(self._active_sessions)}")

    def force_reset_user(self, user_id: int) -> bool:
        """Administrative command to terminate a stuck duel for a user."""
        session = self._user_to_session.get(user_id)
        if session:
            self.unregister_session(session)
            return True
        return False

    def clear_all(self) -> int:
        """Administrative emergency reset for all active duel sessions."""
        count = len(self._active_sessions)
        self._user_to_session.clear()
        self._active_sessions.clear()
        logger.warning(f"Cleared all active duel sessions ({count} sessions purged).")
        return count

    @property
    def active_duel_count(self) -> int:
        """Returns total number of concurrent duels."""
        return len(self._active_sessions)


# Global singleton instance for shared cog access
duel_manager = DuelManager()
