#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.cogs.deckbuilding
Description:
    Discord Bot Cog for Player Deckbuilding & Tactical Deck Management.
    Provides real-time interactive slash commands for custom deck construction,
    Master Rule legality auditing, visual DuelingBook grid rendering, story character
    deck duplication, tactical deck analytics, named profile slots, and YDK serialization.
    Dynamically synchronized with the live 64-card custom pool and dual telemetry tracking.

Slash Commands:
    - /deck_add: Add a custom card to active deck with live capacity feedback
    - /deck_remove: Remove a card from active deck
    - /deck_clear: Empty active deck
    - /mydeck: View active deck categorized cardlist, curves, field engine & legality
    - /deck_visual: Render active deck as a visual card grid image (DuelingBook style)
    - /load_character_deck: Clone a story character's pre-constructed deck
    - /story_decks: Browse canonical story character decks, chapters & AI ELO ratings
    - /story_deck_visual: Render visual card grid of any story character deck
    - /deck_analyze: Deep tactical telemetry (Curves, Attributes, Races, Field Awareness)
    - /deck_save: Save active deck into a named profile slot
    - /deck_load: Load a saved deck profile into active deck with real-time autocomplete
    - /deck_slots: List all saved deck profiles with real-time duel win/loss records
    - /deck_delete: Delete a saved deck profile slot with autocomplete
    - /deck_export: Export active deck as an official EDOPro / Project Ignis .ydk file
    - /deck_cardpool: Live dynamic cardpool dimensions and Master Rule format legality
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Constants, UI Formatters & Autocomplete Handlers)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Standard & Third-Party Library Inclusions
# -----------------------------------------------------------------------------
import io
import os
from typing import Any, Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Internal Architecture & Service Inclusions
# -----------------------------------------------------------------------------
from utils.domain.autocomplete import card_name_autocomplete
from production.main.logger import get_logger
from services.card import CardService
from services.deck import MAX_USER_DECK_SLOTS, DeckService

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Module-Level Logger & Service Instances
# -----------------------------------------------------------------------------
logger = get_logger("discord_bot.cogs.deckbuilding")

_deck_service = DeckService()
_card_service = CardService()


# -----------------------------------------------------------------------------
# Sub-Block 2.4: Presentation Formatters & Modular Embed Builders
# -----------------------------------------------------------------------------
def format_deck_card_line(c: Dict[str, Any]) -> str:
    """
    Renders a single card entry into a rich, informative Discord markdown string
    displaying set numbers, rarities, frame mechanics, attributes, and species.
    """
    set_tag = f"`{c['set_number']}` " if c.get("set_number") else ""
    rarity_tag = f"`{c.get('rarity', 'Common')}`"
    qty = c.get("quantity", 1)
    name = c.get("name", "Unknown Card")
    card_type = c.get("card_type", "Monster")
    sub = c.get("card_subtype", "Normal")

    if card_type == "Monster":
        attr = c.get("attribute", "DIVINE")
        race = c.get("monster_type", "Unknown")
        lvl = c.get("level_or_rank_or_link", 0)
        sub_lower = sub.lower()
        if "link" in sub_lower:
            metric = f"Link-{lvl}"
        elif "xyz" in sub_lower:
            metric = f"Rank {lvl}"
        elif "pendulum" in sub_lower:
            scale = c.get("scale", 0)
            metric = f"★{lvl} [S:{scale}]"
        else:
            metric = f"★{lvl}"
        return f"{qty}x {set_tag}**{name}** [{attr} | {race} | {metric}] • {rarity_tag}"

    return f"{qty}x {set_tag}**{name}** ({sub}) • {rarity_tag}"


def build_active_deck_embed(
    user: discord.User,
    analysis: Dict[str, Any],
    partition: Dict[str, Any],
    matched_slot: Optional[Dict[str, Any]] = None,
) -> discord.Embed:
    """
    Constructs the primary /mydeck Discord embed incorporating real-time
    card lists, tactical curves, field awareness diagnostic, and format legality.
    """
    monsters = [format_deck_card_line(c) for c in analysis["main_cards"] if c["card_type"] == "Monster"]
    spells = [format_deck_card_line(c) for c in analysis["main_cards"] if c["card_type"] == "Spell"]
    traps = [format_deck_card_line(c) for c in analysis["main_cards"] if c["card_type"] == "Trap"]
    extra = [format_deck_card_line(c) for c in analysis["extra_cards"]]

    side_str = f" | Side: {analysis['side_count']}" if analysis.get("side_count") else ""

    desc_lines = [
        f"**Total Cards:** {analysis['total_count']} *(Main: {analysis['main_count']}/60 | Extra: {analysis['extra_count']}/15{side_str})*",
        f"**Legality Status:** {partition['legality_badge']}",
    ]

    if matched_slot:
        wins = matched_slot.get("wins", 0)
        losses = matched_slot.get("losses", 0)
        wr = matched_slot.get("win_rate", 0.0)
        desc_lines.append(
            f"**Saved Profile:** 🏷️ **{matched_slot['deck_name']}** • Record: **{wins}W - {losses}L** ({wr}% WR)"
        )
    else:
        desc_lines.append("**Profile:** ✏️ Active Custom Deck *(Unsaved — use `/deck_save` to record duel telemetry)*")

    embed = discord.Embed(
        title=f"🃏 {user.display_name}'s Active Deck",
        description="\n".join(desc_lines),
        color=0x2ECC71 if partition["is_legal"] else 0xF1C40F,
    )

    if monsters:
        embed.add_field(name=f"⚔️ Monsters ({analysis['monsters']})", value="\n".join(monsters[:15]), inline=False)
        if len(monsters) > 15:
            embed.add_field(name="⚔️ Monsters (Continued)", value="\n".join(monsters[15:]), inline=False)
    if spells:
        embed.add_field(name=f"✨ Spells ({analysis['spells']})", value="\n".join(spells), inline=False)
    if traps:
        embed.add_field(name=f"🛡️ Traps ({analysis['traps']})", value="\n".join(traps), inline=False)
    if extra:
        embed.add_field(name=f"🔮 Extra Deck ({analysis['extra_count']})", value="\n".join(extra), inline=False)

    # 1. Level / Tribute Curve
    trib = analysis.get("tributes", {})
    trib_str = (
        f"• **Normal/No Tribute (Lv 1-4):** {trib.get('level_1_to_4', 0)}\n"
        f"• **1 Tribute (Lv 5-6):** {trib.get('level_5_to_6', 0)}\n"
        f"• **2+ Tributes (Lv 7+):** {trib.get('level_7_plus', 0)}"
    )
    embed.add_field(name="⭐ Tribute & Level Curve", value=trib_str, inline=True)

    # 2. Attributes & Species Breakdown
    attr_str = ", ".join(f"`{k}`: {v}" for k, v in analysis.get("attributes", {}).items()) or "None"
    race_str = ", ".join(f"`{k}`: {v}" for k, v in analysis.get("races", {}).items()) or "None"
    embed.add_field(
        name="🧬 Attributes & Species",
        value=f"**Attributes:** {attr_str}\n**Species/Races:** {race_str}",
        inline=True,
    )

    # 3. Field Awareness Engine Diagnostic
    field_spells_list = ", ".join(f"{fs['quantity']}x **{fs['name']}**" for fs in analysis.get("field_spells", []))
    field_desc = f"{analysis.get('field_status', '')}\n"
    if field_spells_list:
        field_desc += f"• **Field Spells:** {field_spells_list}\n"
    if analysis.get("field_dependent_count"):
        field_desc += f"• **Field-Dependent Cards:** {analysis['field_dependent_count']} card(s) active"
    embed.add_field(name="🗺️ Field Awareness Engine", value=field_desc, inline=False)

    # 4. Official Rarity Breakdown
    rarity_str = " • ".join(f"**{r}:** {c}" for r, c in sorted(analysis.get("rarities", {}).items()))
    if rarity_str:
        embed.add_field(name="✨ Rarity Distribution", value=rarity_str, inline=False)

    # 5. Format Violations / Status Notes
    if partition["violations"]:
        embed.add_field(name="⚠️ Format Violations", value="\n".join(partition["violations"]), inline=False)
    elif analysis["notes"]:
        embed.add_field(name="📋 Format Status", value="\n".join(analysis["notes"]), inline=False)

    embed.set_footer(text="Use /deck_visual to view card images • /deck_add / /deck_remove to edit • /deck_save to store.")
    return embed


def build_deck_analysis_embed(
    user: discord.User,
    analysis: Dict[str, Any],
    matched_slot: Optional[Dict[str, Any]] = None,
) -> discord.Embed:
    """
    Constructs the deep statistical analytics embed for /deck_analyze.
    """
    side_str = f" | **Side Deck:** {analysis['side_count']}" if analysis.get("side_count") else ""

    desc_lines = [
        f"**Main Deck:** {analysis['main_count']} | **Extra Deck:** {analysis['extra_count']}{side_str}",
        f"**Card Composition:** {analysis['monsters']} Monsters • {analysis['spells']} Spells • {analysis['traps']} Traps",
    ]

    if matched_slot:
        wins = matched_slot.get("wins", 0)
        losses = matched_slot.get("losses", 0)
        wr = matched_slot.get("win_rate", 0.0)
        created = str(matched_slot.get("created_at") or "")[:10]
        desc_lines.append(f"**Duel Telemetry:** 🏷️ **{matched_slot['deck_name']}** — **{wins}W / {losses}L** (**{wr}% WR**) • Saved: `{created}`")

    embed = discord.Embed(
        title=f"🔬 Tactical Deck Analytics: {user.display_name}",
        description="\n".join(desc_lines),
        color=0x3498DB,
    )

    # Level / Rank / Link Breakdown
    levels_str = "\n".join(f"• **{k}:** {v} monster(s)" for k, v in sorted(analysis.get("levels", {}).items())) or "• No monsters"
    embed.add_field(name="⭐ Level / Rank / Link Distribution", value=levels_str, inline=True)

    # Tribute curve
    trib = analysis.get("tributes", {})
    trib_str = (
        f"• **Normal/No Tribute (Lv 1-4):** {trib.get('level_1_to_4', 0)}\n"
        f"• **1 Tribute (Lv 5-6):** {trib.get('level_5_to_6', 0)}\n"
        f"• **2+ Tributes (Lv 7+):** {trib.get('level_7_plus', 0)}"
    )
    embed.add_field(name="⚖️ Tribute Curve", value=trib_str, inline=True)

    # Extra Deck Mechanics
    extra_mech = analysis.get("extra_mechanics", {})
    mech_str = "\n".join(f"• **{k}:** {v} card(s)" for k, v in extra_mech.items() if v > 0) or "• None"
    embed.add_field(name="🔮 Extra Deck Mechanics", value=mech_str, inline=True)

    # Attribute & Species
    attrs = "\n".join(f"• **{k}:** {v}" for k, v in analysis.get("attributes", {}).items()) or "• None"
    races = "\n".join(f"• **{k}:** {v}" for k, v in analysis.get("races", {}).items()) or "• None"
    embed.add_field(name="🔥 Elemental Attributes", value=attrs, inline=True)
    embed.add_field(name="🧬 Monster Species / Races", value=races, inline=True)

    # Field Awareness Engine Diagnostic
    field_status = analysis.get("field_status", "")
    field_spells = [f"{fs['quantity']}x {fs['name']}" for fs in analysis.get("field_spells", [])]
    field_deps = [f"{fd['quantity']}x {fd['name']}" for fd in analysis.get("field_dependent_cards", [])]

    field_report = f"{field_status}\n"
    if field_spells:
        field_report += f"**Field Spells ({analysis.get('field_spell_count', 0)}):**\n" + "\n".join(f"  └ {fs}" for fs in field_spells) + "\n"
    if field_deps:
        field_report += f"**Field-Aware Cards ({analysis.get('field_dependent_count', 0)}):**\n" + "\n".join(f"  └ {fd}" for fd in field_deps[:8])
        if len(field_deps) > 8:
            field_report += f"\n  └ ...and {len(field_deps) - 8} more"

    embed.add_field(name="🗺️ Field Awareness Engine Diagnostic", value=field_report, inline=False)

    # Rarity Profile
    rarities_str = " • ".join(f"**{r}:** {c}" for r, c in sorted(analysis.get("rarities", {}).items()))
    if rarities_str:
        embed.add_field(name="✨ Rarity Portfolio", value=rarities_str, inline=False)

    embed.set_footer(text="The Land of Kustomazi Deckbuilder • Use /mydeck to view complete cardlist.")
    return embed


def build_story_decks_directory_embed(decks: List[Dict[str, Any]]) -> discord.Embed:
    """
    Constructs the canonical story character deck directory embed for /story_decks.
    """
    embed = discord.Embed(
        title="📖 The Land of Kustomazi: Story & Progression Decks",
        description="Use `/load_character_deck <deck>` to clone any pre-constructed deck into your active profile.",
        color=0xE67E22,
    )
    for d in decks:
        d_id = d["id"]
        name = d["name"]
        duelist = d.get("duelist_name") or "Story Duelist"
        chapter = d.get("story_chapter") or "Chapter Deck"
        elo = d.get("ai_elo", 1200)
        main_c = d.get("main_count", 0)
        extra_c = d.get("extra_count", 0)
        badge = d.get("legality_badge", "")
        desc = (d.get("description") or "")[:120]
        embed.add_field(
            name=f"#{d_id}: {name} [{chapter}]",
            value=(
                f"• **Duelist:** {duelist} (AI ELO: {elo})\n"
                f"• **Cards:** {main_c} Main | {extra_c} Extra ({badge})\n"
                f"• *{desc}...*"
            ),
            inline=False,
        )
    return embed


def build_deck_slots_embed(user: discord.User, slots: List[Dict[str, Any]]) -> discord.Embed:
    """
    Constructs the /deck_slots embed displaying all saved profiles with live match winrates.
    """
    embed = discord.Embed(
        title=f"📁 {user.display_name}'s Saved Deck Profiles ({len(slots)}/{MAX_USER_DECK_SLOTS})",
        description="Use `/deck_load <name>` to activate any profile, or `/deck_save <name>` to update.",
        color=0x2ECC71,
    )
    for idx, d in enumerate(slots, 1):
        created = str(d.get("created_at") or "")[:10]
        main_c = d.get("main_count", 0)
        extra_c = d.get("extra_count", 0)
        badge = d.get("legality_badge", "")
        wins = d.get("wins", 0)
        losses = d.get("losses", 0)
        wr = d.get("win_rate", 0.0)
        total_duels = wins + losses
        duel_str = f"**{wins}W - {losses}L** ({wr}% WR)" if total_duels > 0 else "*No matches played yet*"

        embed.add_field(
            name=f"Slot #{idx}: {d['deck_name']}",
            value=(
                f"• **Cards:** {main_c} Main | {extra_c} Extra ({badge})\n"
                f"• **Match Record:** {duel_str}\n"
                f"• **Saved on:** `{created}`"
            ),
            inline=False,
        )
    return embed


# -----------------------------------------------------------------------------
# Sub-Block 2.5: Real-Time Interactive Autocomplete Handlers
# -----------------------------------------------------------------------------
async def character_deck_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """
    Real-time autocomplete handler fetching matching character decks from SQLite.
    Enriched with real-time duelist name, main/extra card counts, and AI ELO.
    """
    decks = await _deck_service.get_character_decks()
    choices = []
    for d in decks:
        dname = d["name"]
        duelist = d.get("duelist_name") or "Story Duelist"
        main_c = d.get("main_count", 0)
        extra_c = d.get("extra_count", 0)
        elo = d.get("ai_elo", 1200)
        label = f"{duelist} — {dname} ({main_c}M/{extra_c}E | ELO: {elo})"
        if not current.strip() or current.lower() in label.lower():
            if len(label) > 100:
                label = label[:97] + "..."
            choices.append(app_commands.Choice(name=label, value=dname))
    return choices[:15]


async def user_deck_slot_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """
    Real-time autocomplete handler fetching user's saved deck slots from SQLite,
    displaying card counts and live match win rates in the choice labels.
    """
    try:
        user_id = str(interaction.user.id)
        slots = await _deck_service.list_user_decks(user_id)
        choices = []
        for s in slots:
            dname = s["deck_name"]
            if not current.strip() or current.lower() in dname.lower():
                wins = s.get("wins", 0)
                losses = s.get("losses", 0)
                total = wins + losses
                wr_str = f"{s.get('win_rate', 0.0)}% WR" if total > 0 else "0 duels"
                label = f"{dname} ({s.get('main_count', 0)}M/{s.get('extra_count', 0)}E | {wins}W-{losses}L | {wr_str})"
                if len(label) > 100:
                    label = label[:97] + "..."
                choices.append(app_commands.Choice(name=label, value=dname))
        return choices[:25]
    except Exception as e:
        logger.warning(f"Error in user_deck_slot_autocomplete: {e}")
        return []


# =============================================================================
# BLOCK 3: BODY BLOCK (Deckbuilding Cog & Application Slash Commands)
# =============================================================================

class DeckbuildingCog(commands.Cog, name="Deckbuilding"):
    """
    Commands for player custom deck construction, Master Rule verification,
    visual rendering, story deck imports, and tactical analytics.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.deck_service = _deck_service
        self.card_service = _card_service

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Active Deck Construction & Mutators
    # -------------------------------------------------------------------------

    @app_commands.command(name="deck_add", description="Add a custom card to your personal active deck")
    @app_commands.autocomplete(card_name=card_name_autocomplete)
    @app_commands.describe(card_name="Name of the card", quantity="Copies to add (1 to 3)")
    async def deck_add_command(self, interaction: discord.Interaction, card_name: str, quantity: Optional[int] = 1):
        """Adds 1-3 copies of a custom card to the player's active deck with live capacity feedback."""
        card = await self.card_service.get_card_by_query(card_name)
        if not card:
            await interaction.response.send_message(f"❌ Card **'{card_name}'** not found in the custom pool.", ephemeral=True)
            return

        qty = min(max(1, quantity or 1), 3)
        user_id = str(interaction.user.id)
        success, display_name, total_copies = await self.deck_service.add_card_to_deck(user_id, card["id"], qty)

        if success:
            partition = await self.deck_service.get_player_deck_partitioned(user_id)
            status_desc = f"Main: **{partition['main_count']}**/60 | Extra: **{partition['extra_count']}**/15"
            await interaction.response.send_message(
                f"✅ Added **{qty}x** copy of **{display_name}** to your active deck! (Total copies in deck: **{total_copies}**/3)\n"
                f"• **Deck Status:** {partition['legality_badge']} ({status_desc})\n"
                f"Use `/mydeck` to view or `/deck_visual` for card grid.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message("❌ Failed to add card to deck.", ephemeral=True)

    @app_commands.command(name="deck_remove", description="Remove a card from your personal active deck")
    @app_commands.autocomplete(card_name=card_name_autocomplete)
    @app_commands.describe(card_name="Name of the card to remove")
    async def deck_remove_command(self, interaction: discord.Interaction, card_name: str):
        """Removes a card completely from the player's deck with updated real-time counts."""
        card = await self.card_service.get_card_by_query(card_name)
        if not card:
            await interaction.response.send_message(f"❌ Card **'{card_name}'** not found.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        success, removed_name = await self.deck_service.remove_card_from_deck(user_id, card["id"])

        if success:
            partition = await self.deck_service.get_player_deck_partitioned(user_id)
            status_desc = f"Main: **{partition['main_count']}**/60 | Extra: **{partition['extra_count']}**/15"
            await interaction.response.send_message(
                f"🗑️ Removed **{removed_name}** from your deck.\n"
                f"• **Remaining:** {partition['legality_badge']} ({status_desc})",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(f"⚠️ **{card['name']}** is not in your active deck.", ephemeral=True)

    @app_commands.command(name="deck_clear", description="Clear all cards from your personal active deck")
    async def deck_clear_command(self, interaction: discord.Interaction):
        """Empties the player's active deck."""
        count = await self.deck_service.clear_deck(str(interaction.user.id))
        await interaction.response.send_message(
            f"🗑️ Cleared **{count}** card entry(ies) from your deck. Active deck is now empty (0/60).",
            ephemeral=True,
        )

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Deck Inspection & Visual Rendering
    # -------------------------------------------------------------------------

    @app_commands.command(name="mydeck", description="View your current personal active deck and format validity")
    async def mydeck_command(self, interaction: discord.Interaction):
        """Displays the player's current card list categorized by Monster, Spell, Trap, and Extra Deck."""
        user_id = str(interaction.user.id)
        cards = await self.deck_service.get_player_deck(user_id)

        if not cards:
            await interaction.response.send_message(
                "📦 Your deck is currently empty!\n"
                "• Use `/deck_add <card>` to add cards.\n"
                "• Use `/load_character_deck` to clone a pre-built story deck (e.g. Kasutamaiza or LeSpookie).\n"
                "• Use `/deck_cardpool` to browse legal card pool dimensions.",
                ephemeral=True,
            )
            return

        analysis = self.deck_service.analyze_deck_structure(cards)
        partition = await self.deck_service.get_player_deck_partitioned(user_id)

        # Check if the active deck matches a saved profile
        matched_slot = None
        matched_name = await self.deck_service.find_matching_saved_deck(user_id)
        if matched_name:
            matched_slot = await self.deck_service.get_saved_deck(user_id, matched_name)

        embed = build_active_deck_embed(interaction.user, analysis, partition, matched_slot)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deck_visual", description="View your active deck rendered as a visual card grid image (DuelingBook style)")
    async def deck_visual_command(self, interaction: discord.Interaction):
        """Renders the player's active deck into a visual image grid."""
        user_id = str(interaction.user.id)
        cards = await self.deck_service.get_player_deck(user_id)
        if not cards:
            await interaction.response.send_message("📦 Your active deck is currently empty! Add cards before viewing.", ephemeral=True)
            return

        render_path = await self.deck_service.generate_deck_visual(
            user_id, deck_title=f"{interaction.user.display_name}'s Deck"
        )
        if not render_path or not os.path.exists(render_path):
            await interaction.response.send_message("❌ Failed to generate visual deck image.", ephemeral=True)
            return

        discord_file = discord.File(render_path, filename=f"deck_{user_id}.png")
        partition = await self.deck_service.get_player_deck_partitioned(user_id)

        embed = discord.Embed(
            title=f"🎨 {interaction.user.display_name}'s Visual Deck Grid",
            description=(
                f"**Deck Status:** {partition['legality_badge']}\n"
                f"• Main Deck: **{partition['main_count']}** / 60 (Min 40)\n"
                f"• Extra Deck: **{partition['extra_count']}** / 15\n"
                f"• Side Deck: **{partition['side_count']}** / 15"
            ),
            color=0x2ECC71 if partition["is_legal"] else 0xE74C3C,
        )
        embed.set_image(url=f"attachment://deck_{user_id}.png")
        await interaction.response.send_message(embed=embed, file=discord_file)

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Story & Character Deck Integration
    # -------------------------------------------------------------------------

    @app_commands.command(name="load_character_deck", description="Copy a story character's pre-made deck into your personal deck")
    @app_commands.autocomplete(character=character_deck_autocomplete)
    @app_commands.describe(character="Story duelist or deck name (e.g. Kasutamaiza or LeSpookie)")
    async def load_character_deck_command(self, interaction: discord.Interaction, character: str):
        """Loads a story duelist's pre-built deck directly into the user's active deck."""
        decks = await self.deck_service.get_character_decks()
        matched_deck = None
        for d in decks:
            if character.lower() in d["name"].lower() or (d.get("duelist_name") and character.lower() in d["duelist_name"].lower()):
                matched_deck = d
                break

        if not matched_deck and decks:
            matched_deck = decks[0]

        if not matched_deck:
            await interaction.response.send_message(f"❌ Deck matching **'{character}'** not found.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        success, deck_name, card_count = await self.deck_service.copy_character_deck_to_player(
            user_id, matched_deck["id"]
        )

        if success:
            duelist = matched_deck.get("duelist_name") or "Story Duelist"
            elo = matched_deck.get("ai_elo", 1200)
            badge = matched_deck.get("legality_badge", "")
            await interaction.response.send_message(
                f"✨ Successfully loaded **{deck_name}** (**{card_count}** cards) into your active deck!\n"
                f"• **Duelist:** {duelist} | **Story ELO:** {elo}\n"
                f"• **Format:** {badge}\n"
                f"Use `/mydeck` to view your complete deck layout or `/deck_visual` for image view.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message("❌ Failed to copy deck.", ephemeral=True)

    @app_commands.command(name="story_decks", description="Browse all canonical story decks, chapters, duelists, and AI ELO tiers")
    async def story_decks_command(self, interaction: discord.Interaction):
        """Displays a directory of all pre-built story character decks and their tactical profiles."""
        decks = await self.deck_service.get_character_decks()
        if not decks:
            await interaction.response.send_message("❌ No story decks registered.", ephemeral=True)
            return

        embed = build_story_decks_directory_embed(decks)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="story_deck_visual", description="Render visual DuelingBook-style image of a story character deck")
    @app_commands.autocomplete(character=character_deck_autocomplete)
    @app_commands.describe(character="Story duelist or deck name")
    async def story_deck_visual_command(self, interaction: discord.Interaction, character: str):
        """Generates and displays a DuelingBook-style visual card grid for any story character deck."""
        decks = await self.deck_service.get_character_decks()
        matched = None
        for d in decks:
            if character.lower() in d["name"].lower() or (d.get("duelist_name") and character.lower() in d["duelist_name"].lower()):
                matched = d
                break
        if not matched and decks:
            matched = decks[0]
        if not matched:
            await interaction.response.send_message("❌ Story deck not found.", ephemeral=True)
            return

        img_path = await self.deck_service.generate_character_deck_visual(matched["id"])
        if not img_path or not os.path.exists(img_path):
            await interaction.response.send_message("❌ Failed to render story deck canvas.", ephemeral=True)
            return

        discord_file = discord.File(img_path, filename=f"story_deck_{matched['id']}.png")
        embed = discord.Embed(
            title=f"🃏 Story Deck: {matched['name']}",
            description=(
                f"**Duelist:** {matched.get('duelist_name') or 'Story'} | **AI ELO:** {matched.get('ai_elo', 1200)}\n"
                f"**Format:** {matched.get('legality_badge', '')}\n"
                f"Use `/load_character_deck {matched['name']}` to play this deck."
            ),
            color=0x2ECC71 if matched.get("is_legal") else 0xF39C12,
        )
        embed.set_image(url=f"attachment://story_deck_{matched['id']}.png")
        await interaction.response.send_message(embed=embed, file=discord_file)

    # -------------------------------------------------------------------------
    # Sub-Block 3.4: Tactical Analytics & Telemetry Diagnostics
    # -------------------------------------------------------------------------

    @app_commands.command(name="deck_analyze", description="Deep statistical analysis of your deck (Level curves, Attributes, Races, Field Awareness)")
    async def deck_analyze_command(self, interaction: discord.Interaction):
        """Generates an in-depth tactical telemetry report on the player's active deck."""
        user_id = str(interaction.user.id)
        cards = await self.deck_service.get_player_deck(user_id)
        if not cards:
            await interaction.response.send_message("📦 Your deck is empty! Add cards before analyzing.", ephemeral=True)
            return

        analysis = self.deck_service.analyze_deck_structure(cards)

        matched_slot = None
        matched_name = await self.deck_service.find_matching_saved_deck(user_id)
        if matched_name:
            matched_slot = await self.deck_service.get_saved_deck(user_id, matched_name)

        embed = build_deck_analysis_embed(interaction.user, analysis, matched_slot)
        await interaction.response.send_message(embed=embed)

    # -------------------------------------------------------------------------
    # Sub-Block 3.5: Multi-Deck Slot Profiles & Persistence
    # -------------------------------------------------------------------------

    @app_commands.command(name="deck_save", description="Save your active deck into a named profile slot")
    @app_commands.describe(name="Name for this deck profile (e.g. 'Kasutamaiza Beatdown')")
    async def deck_save_command(self, interaction: discord.Interaction, name: str):
        """Saves current active deck to a named profile slot."""
        user_id = str(interaction.user.id)
        ok, saved_name = await self.deck_service.save_named_deck(user_id, name)
        if ok:
            await interaction.response.send_message(
                f"💾 Successfully saved your deck as **'{saved_name}'**! Use `/deck_slots` to view all saved decks.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(f"❌ Failed to save deck: {saved_name}", ephemeral=True)

    @app_commands.command(name="deck_load", description="Load a previously saved deck into your active deck")
    @app_commands.autocomplete(name=user_deck_slot_autocomplete)
    @app_commands.describe(name="Name of the saved deck profile to load")
    async def deck_load_command(self, interaction: discord.Interaction, name: str):
        """Loads a saved named deck into the user's active deck with autocomplete assistance."""
        user_id = str(interaction.user.id)
        ok, msg, count = await self.deck_service.load_named_deck(user_id, name)
        if ok:
            slot = await self.deck_service.get_saved_deck(user_id, name)
            duel_str = ""
            if slot and (slot.get("wins", 0) + slot.get("losses", 0) > 0):
                duel_str = f" • Record: **{slot['wins']}W - {slot['losses']}L** ({slot.get('win_rate', 0.0)}% WR)"

            await interaction.response.send_message(
                f"✨ Successfully loaded **'{name}'** (**{count}** cards{duel_str}) into your active deck!\nUse `/mydeck` to view.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)

    @app_commands.command(name="deck_slots", description="List all your saved custom deck profiles with live match winrates")
    async def deck_slots_command(self, interaction: discord.Interaction):
        """Lists all custom deck profiles saved by the user with real-time match records."""
        user_id = str(interaction.user.id)
        slots = await self.deck_service.list_user_decks(user_id)
        if not slots:
            await interaction.response.send_message(
                "📂 You haven't saved any named deck profiles yet! Use `/deck_save <name>` to save your active deck.",
                ephemeral=True,
            )
            return

        embed = build_deck_slots_embed(interaction.user, slots)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="deck_delete", description="Delete a saved deck profile slot from your account")
    @app_commands.autocomplete(name=user_deck_slot_autocomplete)
    @app_commands.describe(name="Name of the saved deck profile to delete")
    async def deck_delete_command(self, interaction: discord.Interaction, name: str):
        """Deletes a saved named deck profile slot."""
        user_id = str(interaction.user.id)
        success = await self.deck_service.delete_named_deck(user_id, name)
        if success:
            await interaction.response.send_message(
                f"🗑️ Successfully deleted deck profile **'{name}'**.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Saved deck profile **'{name}'** was not found.",
                ephemeral=True,
            )

    # -------------------------------------------------------------------------
    # Sub-Block 3.6: YDK Serialization & Dynamic Cardpool Telemetry
    # -------------------------------------------------------------------------

    @app_commands.command(name="deck_export", description="Export your active deck as an official EDOPro .ydk file")
    async def deck_export_command(self, interaction: discord.Interaction):
        """Exports the player's active deck as a downloadable .ydk file."""
        cards = await self.deck_service.get_player_deck(str(interaction.user.id))
        if not cards:
            await interaction.response.send_message("📦 Your active deck is empty! Add cards before exporting.", ephemeral=True)
            return

        ydk_text = self.deck_service.export_to_ydk(cards, deck_title=f"{interaction.user.display_name} Active Deck")
        file_bytes = io.BytesIO(ydk_text.encode("utf-8"))
        discord_file = discord.File(file_bytes, filename=f"{interaction.user.name}_deck.ydk")

        await interaction.response.send_message(
            "📥 Here is your official **.ydk** file for EDOPro / Project Ignis!",
            file=discord_file,
            ephemeral=True,
        )

    @app_commands.command(name="deck_cardpool", description="View live dynamic cardpool statistics and 40-card format status")
    async def deck_cardpool_command(self, interaction: discord.Interaction):
        """Displays live dynamic cardpool metrics directly from SQLite."""
        stats = await self.deck_service.get_cardpool_stats()

        embed = discord.Embed(
            title="🌐 Live Cardpool Dimensions & Master Rule Status",
            color=0x9B59B6,
        )
        embed.add_field(name="📦 Total Custom Cards", value=f"**{stats['total_cards']}** cards registered", inline=True)
        embed.add_field(name="⚔️ Main Deck Pool", value=f"**{stats['main_deck_pool']}** distinct cards", inline=True)
        embed.add_field(name="🔮 Extra Deck Pool", value=f"**{stats['extra_monsters']}** cards (Fusion/Synchro/Xyz/Link)", inline=True)
        embed.add_field(name="✨ Spells & Traps", value=f"{stats['spells']} Spells • {stats['traps']} Traps", inline=True)
        embed.add_field(name="🗺️ Field Spells", value=f"**{stats['field_spells']}** Field Spells available", inline=True)

        status_text = (
            "✅ **Full Master Rule Legality**: Pool exceeds 40 single Main Deck cards! "
            "Legal 40-to-60 card constructed and singleton formats are active."
            if stats["has_legal_40_singles"] else
            "⚠️ **Alpha Cardpool**: Main deck singles are under 40."
        )
        embed.add_field(name="⚖️ Format Legality Status", value=status_text, inline=False)
        await interaction.response.send_message(embed=embed)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Extension Entrypoint & Translation Manifest)
# =============================================================================

async def setup(bot: commands.Bot):
    """Cog registration entrypoint."""
    await bot.add_cog(DeckbuildingCog(bot))


__all__ = [
    "DeckbuildingCog",
    "character_deck_autocomplete",
    "user_deck_slot_autocomplete",
    "format_deck_card_line",
    "build_active_deck_embed",
    "build_deck_analysis_embed",
    "build_deck_slots_embed",
    "build_story_decks_directory_embed",
    "setup",
]
