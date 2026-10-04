# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.duel.domain
Description:
    Domain Package Initialization for the Duel Subsystem.
    Re-exports the core DuelSession state machine and DuelManager concurrency registry.

Architectural Classification:
    Layer 1 (L1) - Domain Layer
    Subsystem: Duel Management & Match Engine
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from .manager import DuelManager
from .session import DuelSession

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DuelManager",
    "DuelSession",
]
