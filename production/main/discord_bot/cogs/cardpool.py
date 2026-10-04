#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.cogs.cardpool
Description:
    Discord Bot Cog for Custom Cardpool Discovery, Search & Live Telemetry.
    Provides slash commands and real-time interactive autocompletion for querying
    custom cards registered in the Story Database. Displays Duelingbook artwork,
    stats, lore chronicles, and live card usage telemetry.
    Organized with Top-Down / Bottom-Up C-style compilation unit architecture.

Slash Commands:
    - /card: Full Duelingbook artwork, stats, and lore card inspection
    - /cardpool: Complete overview of Set 1: The Land of Kustomazi
    - /card_stats: Real-time card inclusion rate, win rate, and dueling stats
    - /meta: Top most popular and most victorious custom cards
    - /random_card: Random card spotlight from the active cardpool
    - /recent_cards: Chronological list of registered custom cards
    - /card_types: Guide to Monster/Spell/Trap types, speeds, 26 races, 7 attributes, and Levels/Ranks
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Constants, UI Formatters & Autocomplete Handlers)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Standard & Third-Party Library Inclusions
# -----------------------------------------------------------------------------
from typing import Any, Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Internal Architecture & Service Inclusions
# -----------------------------------------------------------------------------
from production.main.logger import get_logger
from services.card import CardService
from utils.domain.card_embeds import (
    build_card_embed,
    build_card_stats_embed,
    build_card_types_guide_embed,
    format_cardpool_catalog_line,
    build_meta_telemetry_embed,
    build_cardpool_catalog_embed,
    build_recent_cards_embed,
)
from utils.domain.autocomplete import card_name_autocomplete

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Module-Level Logger & Service Instances
# -----------------------------------------------------------------------------
logger = get_logger("discord_bot.cogs.cardpool")

# Shared card service instance for cog and autocomplete operations
_card_service = CardService()


# -----------------------------------------------------------------------------
# Sub-Block 2.4: Presentation Formatters & Modular Embed Builders (Delegated to utils)
# -----------------------------------------------------------------------------
# Formatters and Embed Builders are encapsulated in utils.domain.card_embeds
# and imported above to maintain clean modular separation between presentation
# and Discord command orchestration.


# -----------------------------------------------------------------------------
# Sub-Block 2.5: Real-Time Autocomplete Handlers (Delegated to utils.domain)
# -----------------------------------------------------------------------------
# Universal card autocomplete handler is centralized in utils.domain.autocomplete
# with 3-second timeout protection and 25-choice API guards, imported above
# for slash command binding and public export in Block 4.



# =============================================================================
# BLOCK 3: BODY BLOCK (Cardpool Cog & Application Slash Commands)
# =============================================================================

class CardpoolCog(commands.Cog, name="Cardpool"):
    """Commands for searching and inspecting custom cards in the live pool."""

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Individual Card Inspection & Single-Card Discovery (/card, /card_stats, /random_card)
    # -------------------------------------------------------------------------

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._card_service = _card_service

    @property
    def card_service(self) -> CardService:
        """Dynamically retrieves the authoritative CardService from bot or fallback."""
        bot_service = getattr(self.bot, "card_service", None)
        if isinstance(bot_service, CardService):
            return bot_service
        return self._card_service

    async def _resolve_card_or_reply(
        self,
        interaction: discord.Interaction,
        query: str,
        ephemeral: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Deduplicated, authoritative card resolver across slash commands.
        Defensively executes live database lookup with timeout and error protection.
        Sends standard formatted error message if card is not found or DB fails.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            await interaction.response.send_message(
                "❌ Please specify a card name, set number (e.g. TLOK-001), or 8-digit passcode.",
                ephemeral=True
            )
            return None

        try:
            card = await self.card_service.get_card_by_query(clean_query)
        except Exception as e:
            logger.error(f"Database error during card resolution for '{clean_query}': {e}", exc_info=True)
            await interaction.response.send_message(
                "⚠️ An error occurred while communicating with the card database. Please try again shortly.",
                ephemeral=True
            )
            return None

        if not card:
            await interaction.response.send_message(
                f"❌ Card **'{clean_query}'** not found in the custom card pool.",
                ephemeral=ephemeral
            )
            return None

        return card

    @app_commands.command(name="card", description="Search custom card pool with Duelingbook artwork, stats, and lore")
    @app_commands.autocomplete(name=card_name_autocomplete)
    @app_commands.describe(
        name="Name, Set Number (e.g. TLOK-001), or Passcode of the card",
        hidden="Whether to show the card only to you (ephemeral) for tactical duel privacy"
    )
    async def card_command(
        self,
        interaction: discord.Interaction,
        name: str,
        hidden: Optional[bool] = False
    ):
        """Displays rich card details for the queried card name, set number, or ID."""
        card = await self._resolve_card_or_reply(interaction, name, ephemeral=True)
        if not card:
            return

        embed = build_card_embed(card)
        view = CardActionView(card=card, card_service=self.card_service, user_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=bool(hidden))

    @app_commands.command(name="card_stats", description="View live usage telemetry, deck inclusion, and win rate for a card")
    @app_commands.autocomplete(name=card_name_autocomplete)
    @app_commands.describe(
        name="Name or Set Number of the custom card",
        hidden="Whether to show the stats only to you (ephemeral)"
    )
    async def card_stats_command(
        self,
        interaction: discord.Interaction,
        name: str,
        hidden: Optional[bool] = False
    ):
        """Displays telemetry metrics (times decked, drawn, played, win rate)."""
        card = await self._resolve_card_or_reply(interaction, name, ephemeral=True)
        if not card:
            return

        try:
            stats = await self.card_service.get_card_usage_stats(card["id"])
            embed = build_card_stats_embed(stats)
            await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))
        except Exception as e:
            logger.error(f"Error fetching stats for card id {card.get('id')}: {e}", exc_info=True)
            await interaction.response.send_message(
                "⚠️ Failed to retrieve telemetry stats from the database.",
                ephemeral=True
            )

    @app_commands.command(name="random_card", description="Spotlight a random custom card from the active pool")
    @app_commands.describe(
        category="Filter random selection: all, monsters, spells, traps, extra_deck",
        hidden="Whether to show the spotlight only to you (ephemeral)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🌟 All Cards", value="all"),
        app_commands.Choice(name="📙 Monster Cards", value="monsters"),
        app_commands.Choice(name="📗 Spell Cards", value="spells"),
        app_commands.Choice(name="📕 Trap Cards", value="traps"),
        app_commands.Choice(name="🌌 Extra Deck Cards", value="extra_deck"),
    ])
    async def random_card_command(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = "all",
        hidden: Optional[bool] = False
    ):
        """Picks a random card from the database and showcases its full embed."""
        chosen_cat = (category or "all").lower()
        filter_kwargs = {}
        if chosen_cat == "monsters":
            filter_kwargs["card_type"] = "Monster"
        elif chosen_cat == "spells":
            filter_kwargs["card_type"] = "Spell"
        elif chosen_cat == "traps":
            filter_kwargs["card_type"] = "Trap"
        elif chosen_cat == "extra_deck":
            filter_kwargs["is_extra_deck"] = True

        try:
            card = await self.card_service.get_random_card(**filter_kwargs)
        except Exception as e:
            logger.error(f"Database error during get_random_card: {e}", exc_info=True)
            await interaction.response.send_message(
                "⚠️ An error occurred while querying the card pool.",
                ephemeral=True
            )
            return

        if not card:
            cat_label = f" for category '{category}'" if category and category != "all" else ""
            await interaction.response.send_message(f"❌ Card pool is currently empty{cat_label}.", ephemeral=True)
            return

        embed = build_card_embed(card)
        view = RandomCardView(card_service=self.card_service, category=chosen_cat, user_id=interaction.user.id)
        cat_title = chosen_cat.replace('_', ' ').title()
        header = "🌟 **Card Spotlight — Random Discovery:**" if chosen_cat == "all" else f"🌟 **Card Spotlight — Random Discovery ({cat_title}):**"
        await interaction.response.send_message(
            content=header,
            embed=embed,
            view=view,
            ephemeral=bool(hidden)
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Cardpool Catalog & Server Macro Meta Commands (/cardpool, /recent_cards, /meta)
    # -------------------------------------------------------------------------

    @app_commands.command(name="cardpool", description="Browse custom cards in the live pool grouped by type and set")
    @app_commands.describe(
        category="Filter catalog by category: overview, monsters, spells, traps, extra_deck",
        set_code="Filter catalog by specific set code (e.g. TLOK)",
        hidden="Whether to display the catalog only to you (ephemeral)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="📊 Cardpool Overview", value="overview"),
        app_commands.Choice(name="⚔️ Monster Cards", value="monsters"),
        app_commands.Choice(name="✨ Spell Cards", value="spells"),
        app_commands.Choice(name="🛡️ Trap Cards", value="traps"),
        app_commands.Choice(name="🌌 Extra Deck Monsters", value="extra_deck"),
    ])
    async def cardpool_command(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = "overview",
        set_code: Optional[str] = None,
        hidden: Optional[bool] = False
    ):
        """Displays complete custom card catalog organized by Monsters, Spells, and Traps."""
        try:
            cards = await self.card_service.get_all_cards()
        except Exception as e:
            logger.error(f"Database error fetching cardpool catalog: {e}", exc_info=True)
            await interaction.response.send_message("⚠️ An error occurred while querying the cardpool database.", ephemeral=True)
            return

        if not cards:
            await interaction.response.send_message("❌ No cards currently registered in the database.", ephemeral=True)
            return

        chosen_cat = category or "overview"
        embed = build_cardpool_catalog_embed(cards, category=chosen_cat, set_code=set_code)
        view = CardpoolView(cards=cards, set_code=set_code, user_id=interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=bool(hidden))

    @app_commands.command(name="recent_cards", description="View custom cards in the pool in chronological order")
    @app_commands.describe(
        limit="Number of cards to display (1 to 25)",
        hidden="Whether to display the list only to you (ephemeral)"
    )
    async def recent_cards_command(
        self,
        interaction: discord.Interaction,
        limit: Optional[int] = 10,
        hidden: Optional[bool] = False
    ):
        """Lists registered custom cards in descending order."""
        card_limit = min(max(1, limit or 10), 25)
        try:
            cards = await self.card_service.get_recent_cards(limit=card_limit)
        except Exception as e:
            logger.error(f"Database error fetching recent cards: {e}", exc_info=True)
            await interaction.response.send_message("⚠️ An error occurred while retrieving recent cards.", ephemeral=True)
            return

        embed = build_recent_cards_embed(cards)
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))

    @app_commands.command(name="meta", description="Overview of top custom cards by popularity and duel win rate")
    @app_commands.describe(hidden="Whether to display meta overview only to you (ephemeral)")
    async def meta_command(self, interaction: discord.Interaction, hidden: Optional[bool] = False):
        """Displays meta tier telemetry across player decks and duels."""
        try:
            meta = await self.card_service.get_meta_overview(limit=5)
        except Exception as e:
            logger.error(f"Database error fetching meta overview: {e}", exc_info=True)
            await interaction.response.send_message("⚠️ An error occurred while generating meta telemetry.", ephemeral=True)
            return

        embed = build_meta_telemetry_embed(meta)
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Master Rules Educational Guide Command (/card_types)
    # -------------------------------------------------------------------------

    @app_commands.command(
        name="card_types",
        description="Guide to Monster/Spell/Trap types, speeds, 26 races, 7 attributes, and Levels/Ranks"
    )
    @app_commands.describe(
        category="Category to view (Overview, Spells, Traps, Monsters, Subtypes/Gemini, Speeds, Races, Attributes, Levels/Ranks)",
        hidden="Whether to display the rules guide only to you (ephemeral)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🃏 Full Overview", value="overview"),
        app_commands.Choice(name="📗 Spell Cards (6 Types)", value="spells"),
        app_commands.Choice(name="📕 Trap Cards (3 Types)", value="traps"),
        app_commands.Choice(name="📙 Monster Categories & Frames", value="monsters"),
        app_commands.Choice(name="🧬 Monster Subtypes & Gemini", value="subtypes"),
        app_commands.Choice(name="⚡ Spell Speeds & Chain Rules", value="spell_speeds"),
        app_commands.Choice(name="🐉 The 26 Monster Types (Races)", value="races"),
        app_commands.Choice(name="✨ The 7 Elemental Attributes", value="attributes"),
        app_commands.Choice(name="⭐ Levels, Ranks & Scales", value="levels_ranks"),
    ])
    async def card_types_command(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = "overview",
        hidden: Optional[bool] = False
    ):
        """Displays rich breakdown of card types, icons, spell speeds, monster races, attributes, and ranks."""
        try:
            chosen = category or "overview"
            embed = build_card_types_guide_embed(chosen)
            view = CardTypesView(user_id=interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=bool(hidden))
        except Exception as e:
            logger.error(f"Error executing /card_types command: {e}", exc_info=True)
            await interaction.response.send_message("⚠️ An error occurred while generating the card types guide.", ephemeral=True)


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Interactive UI Components & Views
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Sub-Sub-Block 3.4.1: Individual Card Action Views (CardActionView)
# -----------------------------------------------------------------------------

class CardActionView(discord.ui.View):
    """Action buttons attached to /card embeds for quick telemetry inspection and external artwork."""

    def __init__(
        self,
        card: Dict[str, Any],
        card_service: CardService,
        user_id: Optional[int] = None
    ):
        super().__init__(timeout=120)
        self.card = card
        self.card_service = card_service
        self.user_id = user_id
        self.message: Optional[discord.Message] = None

        # External artwork or Duelingbook link button if URL is valid
        artwork_url = card.get("duelingbook_url") or card.get("image_url")
        if artwork_url and isinstance(artwork_url, str) and artwork_url.startswith(("http://", "https://")):
            self.add_item(discord.ui.Button(
                label="Artwork",
                url=artwork_url,
                emoji="🖼️"
            ))

    async def on_timeout(self) -> None:
        """Deactivates action buttons upon timeout."""
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.url is None:
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @discord.ui.button(label="Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fetches live telemetry stats dynamically from the database for the active card."""
        card_id = self.card.get("id")
        if not card_id:
            await interaction.response.send_message("❌ Card ID missing for this card.", ephemeral=True)
            return

        try:
            stats = await self.card_service.get_card_usage_stats(card_id)
            embed = build_card_stats_embed(stats)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error fetching stats via CardActionView for card id {card_id}: {e}", exc_info=True)
            await interaction.response.send_message("⚠️ Failed to retrieve telemetry stats.", ephemeral=True)


# -----------------------------------------------------------------------------
# Sub-Sub-Block 3.4.2: Random Card Exploration Views (RandomCardView)
# -----------------------------------------------------------------------------

class RandomCardView(discord.ui.View):
    """Interactive view for rerolling a random card spotlight dynamically from the database."""

    def __init__(
        self,
        card_service: CardService,
        category: str = "all",
        user_id: Optional[int] = None
    ):
        super().__init__(timeout=180)
        self.card_service = card_service
        self.category = category
        self.user_id = user_id
        self.message: Optional[discord.Message] = None

    async def on_timeout(self) -> None:
        """Deactivates the reroll button when view expires."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @discord.ui.button(label="Reroll", style=discord.ButtonStyle.primary, emoji="🎲")
    async def reroll_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fetches a fresh random card from the live database matching the active category."""
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ This spotlight belongs to another duelist. Run `/random_card` to start your own!",
                ephemeral=True
            )
            return

        filter_kwargs = {}
        if self.category == "monsters":
            filter_kwargs["card_type"] = "Monster"
        elif self.category == "spells":
            filter_kwargs["card_type"] = "Spell"
        elif self.category == "traps":
            filter_kwargs["card_type"] = "Trap"
        elif self.category == "extra_deck":
            filter_kwargs["is_extra_deck"] = True

        try:
            card = await self.card_service.get_random_card(**filter_kwargs)
        except Exception as e:
            logger.error(f"Database error during RandomCardView reroll: {e}", exc_info=True)
            await interaction.response.send_message("⚠️ Database error while rerolling.", ephemeral=True)
            return

        if not card:
            await interaction.response.send_message("❌ No cards found for this category.", ephemeral=True)
            return

        embed = build_card_embed(card)
        cat_title = self.category.replace('_', ' ').title()
        header = "🌟 **Card Spotlight — Random Discovery:**" if self.category == "all" else f"🌟 **Card Spotlight — Random Discovery ({cat_title}):**"
        await interaction.response.edit_message(content=header, embed=embed, view=self)


# -----------------------------------------------------------------------------
# Sub-Sub-Block 3.4.3: Cardpool Catalog Navigation Components (CardpoolSelect, CardpoolView)
# -----------------------------------------------------------------------------

class CardpoolSelect(discord.ui.Select):
    """Dropdown menu for browsing through cardpool categories (Overview, Monsters, Spells, Traps, Extra Deck)."""

    def __init__(self, cards: List[Dict[str, Any]], set_code: Optional[str] = None):
        self.cards = cards
        self.set_code = set_code
        monsters = sum(1 for c in cards if c.get("card_type") == "Monster")
        spells = sum(1 for c in cards if c.get("card_type") == "Spell")
        traps = sum(1 for c in cards if c.get("card_type") == "Trap")
        extra_deck = sum(
            1 for c in cards
            if any(m in (c.get("card_subtype") or "").lower() for m in ("fusion", "synchro", "xyz", "link"))
            or (c.get("card_type") or "").lower() in ("fusion", "synchro", "xyz", "link")
        )

        options = [
            discord.SelectOption(label="Cardpool Overview", value="overview", description=f"Macro stats, sets, and distribution ({len(cards)} cards)", emoji="📊"),
            discord.SelectOption(label=f"Monster Cards ({monsters})", value="monsters", description="Main & Extra deck monster cards", emoji="⚔️"),
            discord.SelectOption(label=f"Spell Cards ({spells})", value="spells", description="Normal, Continuous, Field, Quick-Play, Equip", emoji="✨"),
            discord.SelectOption(label=f"Trap Cards ({traps})", value="traps", description="Normal, Continuous, and Counter Traps", emoji="🛡️"),
            discord.SelectOption(label=f"Extra Deck Monsters ({extra_deck})", value="extra_deck", description="Fusion, Synchro, Xyz, and Link monsters", emoji="🌌"),
        ]
        super().__init__(placeholder="Select a cardpool category to browse...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.view and getattr(self.view, 'user_id', None) and interaction.user.id != self.view.user_id:
            await interaction.response.send_message(
                "❌ This cardpool catalog belongs to another duelist. Run `/cardpool` to explore on your own!",
                ephemeral=True
            )
            return

        selected = self.values[0]
        embed = build_cardpool_catalog_embed(self.cards, category=selected, set_code=self.set_code)
        await interaction.response.edit_message(embed=embed, view=self.view)


class CardpoolView(discord.ui.View):
    """Interactive view holding the cardpool category dropdown."""

    def __init__(self, cards: List[Dict[str, Any]], set_code: Optional[str] = None, user_id: Optional[int] = None):
        super().__init__(timeout=180)
        self.cards = cards
        self.set_code = set_code
        self.user_id = user_id
        self.message: Optional[discord.Message] = None
        self.add_item(CardpoolSelect(cards, set_code=set_code))

    async def on_timeout(self) -> None:
        """Deactivates dropdown upon timeout."""
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


# -----------------------------------------------------------------------------
# Sub-Sub-Block 3.4.4: Master Rules Educational Guide Components (CardTypesSelect, CardTypesView)
# -----------------------------------------------------------------------------

class CardTypesSelect(discord.ui.Select):
    """Dropdown menu for switching between all Master Rules categories and custom cardpool mechanics."""

    def __init__(self):
        options = [
            discord.SelectOption(label="Full Overview", value="overview", description="Core card types, attributes, levels/ranks summary", emoji="🃏"),
            discord.SelectOption(label="Spell Cards (6 Types)", value="spells", description="Normal, Continuous, Equip, Quick-Play, Field, Ritual", emoji="📗"),
            discord.SelectOption(label="Trap Cards (3 Types)", value="traps", description="Normal, Continuous, and Counter Traps (Speed 3)", emoji="📕"),
            discord.SelectOption(label="Monster Frames & Summons", value="monsters", description="Main Deck vs Extra Deck frames and summon rules", emoji="📙"),
            discord.SelectOption(label="Monster Subtypes & Gemini", value="subtypes", description="Gemini (LeSpookie Set 1!), Tuner, Flip, Union, Spirit, Toon", emoji="🧬"),
            discord.SelectOption(label="Spell Speeds & Chain Rules", value="spell_speeds", description="Speed 1, Speed 2, Speed 3 Counter Traps, and LIFO chain resolution", emoji="⚡"),
            discord.SelectOption(label="26 Monster Types (Races)", value="races", description="All 26 official monster races/tribes", emoji="🐉"),
            discord.SelectOption(label="7 Elemental Attributes", value="attributes", description="LIGHT, DARK, EARTH, WATER, FIRE, WIND, DIVINE", emoji="✨"),
            discord.SelectOption(label="Levels, Ranks & Scales", value="levels_ranks", description="Level tribute thresholds, Xyz Ranks, and Link/Scale rules", emoji="⭐"),
        ]
        super().__init__(placeholder="Select a rules category to inspect...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.view and getattr(self.view, 'user_id', None) and interaction.user.id != self.view.user_id:
            await interaction.response.send_message(
                "❌ This educational guide belongs to another duelist. Run `/card_types` to open your own!",
                ephemeral=True
            )
            return

        selected = self.values[0]
        embed = build_card_types_guide_embed(selected)
        await interaction.response.edit_message(embed=embed, view=self.view)


class CardTypesView(discord.ui.View):
    """Interactive view holding the category dropdown for rules and taxonomy."""

    def __init__(self, user_id: Optional[int] = None):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.message: Optional[discord.Message] = None
        self.add_item(CardTypesSelect())

    async def on_timeout(self) -> None:
        """Deactivates dropdown upon timeout."""
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Extension Entrypoint & Translation Manifest)
# =============================================================================

async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(CardpoolCog(bot))


__all__ = [
    "CardpoolCog",
    "CardpoolSelect",
    "CardpoolView",
    "CardActionView",
    "RandomCardView",
    "CardTypesSelect",
    "CardTypesView",
    "card_name_autocomplete",
    "format_cardpool_catalog_line",
    "build_meta_telemetry_embed",
    "build_cardpool_catalog_embed",
    "build_recent_cards_embed",
    "setup",
]
