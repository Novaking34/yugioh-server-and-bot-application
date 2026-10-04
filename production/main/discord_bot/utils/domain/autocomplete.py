# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.domain.autocomplete
Description:
    Real-Time Autocomplete Handlers & Choice Builders for Discord Slash Commands.
    Provides robust, exception-guarded autocomplete handlers for card names,
    set numbers, and passcodes across all bot cogs.
    Enforces Discord's 25-choice API limit, 100-character choice name limit,
    and 3-second interaction timeout protection with contextual scoping.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Callable, Coroutine, Dict, List, Optional
import discord
from discord import app_commands

from production.main.logger import get_logger
from services.card import CardService, DEFAULT_AUTOCOMPLETE_LIMIT

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Module-Level Logger & Service Instances
# -----------------------------------------------------------------------------
logger = get_logger("discord_bot.utils.domain.autocomplete")

# Shared default CardService instance for autocomplete query execution
_card_service = CardService()

# Discord slash command autocomplete protocol hard ceiling
DISCORD_MAX_AUTOCOMPLETE_CHOICES = 25

# =============================================================================
# BLOCK 3: BODY BLOCK (Autocomplete Handlers & Choice Builders)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Choice Model Transformation Primitives
# -----------------------------------------------------------------------------

def build_card_autocomplete_choices(
    matches: List[Dict[str, Any]],
    limit: int = DEFAULT_AUTOCOMPLETE_LIMIT
) -> List[app_commands.Choice[str]]:
    """
    Transforms card dictionary matches into safe Discord Choice objects.
    Enforces:
    - Discord's hard 25-choice protocol ceiling
    - Discord's strict 100-character ceiling per choice name label
    - Fallback label generation if autocomplete_label is absent
    """
    safe_limit = min(max(1, limit), DISCORD_MAX_AUTOCOMPLETE_CHOICES)
    choices: List[app_commands.Choice[str]] = []

    for m in matches[:safe_limit]:
        cid = m.get("id", "Unknown")
        set_num = m.get("set_number", "")
        name = m.get("name", "Unknown Card")

        label = m.get("autocomplete_label") or (f"{set_num} | {name}" if set_num else f"[{cid}] {name}")
        if len(label) > 100:
            label = label[:97] + "..."

        choices.append(app_commands.Choice(name=label, value=name))

    return choices


def _resolve_card_service(interaction: Optional[discord.Interaction]) -> CardService:
    """Safely resolves an active CardService from interaction.client if available, else returns default."""
    if interaction is not None:
        client = getattr(interaction, "client", None)
        if client is not None:
            service = getattr(client, "card_service", None)
            if isinstance(service, CardService):
                return service
    return _card_service


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Universal Card Name Autocomplete Handler
# -----------------------------------------------------------------------------

async def card_name_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """
    Universal real-time autocomplete handler for Discord slash commands.
    Queries the custom card pool by card name, set number (TLOK-001), or passcode.
    Provides:
    - 3-second timeout protection with defensive error boundary
    - Discord 25-choice API guard
    - Zero-query discovery yielding canonical set order
    """
    try:
        service = _resolve_card_service(interaction)
        matches = await service.search_cards(current, limit=DEFAULT_AUTOCOMPLETE_LIMIT)
        return build_card_autocomplete_choices(matches, limit=DEFAULT_AUTOCOMPLETE_LIMIT)
    except Exception as e:
        logger.warning(f"Error during card_name_autocomplete query '{current}': {e}")
        return []


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Contextual Autocomplete Factory (Mechanics & Scope Filtering)
# -----------------------------------------------------------------------------

def create_card_autocomplete(
    card_type: Optional[str] = None,
    card_subtype: Optional[str] = None,
    is_extra_deck: Optional[bool] = None,
    archetype: Optional[str] = None,
    limit: int = DEFAULT_AUTOCOMPLETE_LIMIT,
) -> Callable[[discord.Interaction, str], Coroutine[Any, Any, List[app_commands.Choice[str]]]]:
    """
    Generates a specialized autocomplete handler scoped to specific Yu-Gi-Oh!
    game mechanics:
    - card_type: "Monster", "Spell", or "Trap"
    - card_subtype: e.g. "Continuous", "Field", "Quick-Play", "Counter"
    - is_extra_deck: True for Fusion/Synchro/Xyz/Link; False for Main Deck
    - archetype: e.g. "Kasutamaiza"
    """
    async def scoped_card_autocomplete(
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        try:
            service = _resolve_card_service(interaction)
            matches = await service.search_cards(
                current,
                limit=limit,
                card_type=card_type,
                card_subtype=card_subtype,
                is_extra_deck=is_extra_deck,
                archetype=archetype,
            )
            return build_card_autocomplete_choices(matches, limit=limit)
        except Exception as e:
            logger.warning(f"Error in scoped_card_autocomplete ({card_type}/{card_subtype}): {e}")
            return []

    return scoped_card_autocomplete


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "DISCORD_MAX_AUTOCOMPLETE_CHOICES",
    "build_card_autocomplete_choices",
    "card_name_autocomplete",
    "create_card_autocomplete",
]
