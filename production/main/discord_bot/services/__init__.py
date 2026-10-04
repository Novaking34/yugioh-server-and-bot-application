"""
=============================================================================
Yu-Gi-Oh! Discord Bot Services Subsystem
=============================================================================
Provides decoupled domain logic, database abstraction, ELO calculations,
story campaign progression, and card/deck usage telemetry.
=============================================================================
"""

from .card import CardService
from .deck import DeckService
from .rating import RatingService
from .story import StoryService, story_service, StoryDuelSession
from .duel import DuelService, DuelManager

__all__ = [
    "CardService",
    "DeckService",
    "RatingService",
    "StoryService",
    "story_service",
    "StoryDuelSession",
    "DuelService",
    "DuelManager",
]
