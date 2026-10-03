"""
=============================================================================
Yu-Gi-Oh! Discord Bot Services Subsystem
=============================================================================
Provides decoupled domain logic, database abstraction, ELO calculations,
story campaign progression, and card/deck usage telemetry.
=============================================================================
"""

from .card import CardService
from .card_service import CardService
from .deck import DeckService
from .rating_service import RatingService
from .story_service import StoryService
from .duel_service import DuelManager

__all__ = [
    "CardService",
    "DeckService",
    "RatingService",
    "StoryService",
    "DuelManager",
]
