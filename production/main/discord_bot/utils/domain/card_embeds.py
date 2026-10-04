# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.domain.card_embeds
Description:
    Card Presentation Embed Builders for Custom Cardpool & Telemetry.
    Constructs rich Discord embeds for single card inspection (/card),
    card usage and win-rate telemetry (/card_stats), collection catalog
    overviews (/cardpool, /recent_cards), server macro meta telemetry (/meta),
    and the comprehensive card types and rules guide (/card_types).
    Engineered with strict adherence to official Yu-Gi-Oh! Master Rule (MR5),
    EDOPro / YGOPro SQLite .cdb schema invariants, and Lua script conventions.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional
import discord

from ..foundation.colors import (
    FRAME_COLORS,
    get_card_color,
)

from ..foundation.formatters import (
    STAT_UNKNOWN,
    LINK_ARROW_GLYPHS,
    LINK_BIT_MAP,
    ATTRIBUTE_ICONS,
    SPELL_TRAP_ICONS,
    format_passcode,
    format_stat_value,
    format_link_arrows,
    format_spell_trap_property,
    get_spell_speed,
    format_monster_classification,
)

from ..foundation.types_guide_data import (
    SPELL_CARD_TYPES,
    TRAP_CARD_TYPES,
    MONSTER_CARD_FRAMES,
    MONSTER_SUBTYPES,
    ALL_26_MONSTER_RACES,
    CARD_ATTRIBUTES,
    LEVELS_AND_RANKS_DATA,
    SPELL_SPEEDS_DATA,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Card Presentation & Embed Generation Units)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Individual Card Inspection Presentation (/card, /random_card)
# -----------------------------------------------------------------------------

def build_card_embed(card: Dict[str, Any]) -> discord.Embed:
    """
    Constructs a rich Discord Embed displaying the card's artwork,
    stats, Set Number, Rarity, Banlist Status, Pendulum scales, effect text,
    and narrative story lore.
    Honors official Yu-Gi-Oh! mechanics and EDOPro/YGOPro data standards:
    - Variable ATK/DEF sentinel representation (? / -2)
    - Link rating, directional arrows, and lack of DEF (Link monsters cannot have DEF)
    - Xyz Rank vs Level distinction
    - Dual Pendulum Scale visibility
    - Spell/Trap property icons and Spell Speeds (1, 2, 3)
    - 8-digit canonical passcode formatting
    """
    card_type = card.get("card_type") or "Monster"
    card_subtype = card.get("card_subtype") or "Effect"
    attribute = card.get("attribute")
    color = get_card_color(card_type, card_subtype, attribute)

    set_num = card.get("set_number") or ""
    title_text = f"{card['name']} [{set_num}]" if set_num else card["name"]

    duelingbook_url = (
        card.get("duelingbook_url")
        or (f"https://www.duelingbook.com/card?id={card.get('duelingbook_id')}" if card.get("duelingbook_id") else None)
        or f"https://www.duelingbook.com/card?id={card.get('id', '')}"
    )

    rarity = card.get("rarity") or "Common"
    banlist = card.get("banlist_status") or "Unlimited"
    archetype = card.get("archetype")

    header_parts = [f"**[{card_type} / {card_subtype}]**", f"Rarity: **{rarity}**", f"Limit: **{banlist}**"]
    if archetype:
        header_parts.append(f"Archetype: **{archetype}**")

    embed = discord.Embed(
        title=title_text,
        url=duelingbook_url,
        description=" • ".join(header_parts),
        color=color
    )

    if card_type == "Monster":
        csub_lower = card_subtype.lower()
        attr_icon = ATTRIBUTE_ICONS.get(attribute or "", "")
        attr_display = f"{attr_icon} {attribute}" if attr_icon and attribute else (attribute or "N/A")
        race_display = card.get("monster_type") or "N/A"

        stats_lines = [f"**Attribute:** {attr_display} | **Type:** {race_display}"]

        level_val = card.get("level_or_rank_or_link") if card.get("level_or_rank_or_link") is not None else card.get("level", 0)

        # Distinguish Link vs Xyz vs Standard Level mechanics
        if "link" in csub_lower:
            arrow_str = format_link_arrows(card.get("link_arrows"))
            arrow_info = f" | **Arrows:** {arrow_str}" if arrow_str else ""
            stats_lines.append(f"**Link Rating:** Link-{level_val}{arrow_info}")
        elif "xyz" in csub_lower:
            stats_lines.append(f"**Rank:** {level_val}")
        else:
            stats_lines.append(f"**Level:** {level_val}")

        # Pendulum scale integration
        if card.get("scale") is not None:
            stats_lines[-1] += f" | **Scale:** {card['scale']}"

        # Resolve ATK/DEF honoring variable stats (? / -2) and Link DEF absence
        atk_val = format_stat_value(card.get("atk"))

        if "link" in csub_lower:
            def_val = "LINK"
        else:
            def_val = format_stat_value(card.get("def"))

        stats_lines.append(f"**ATK:** {atk_val} / **DEF:** {def_val}")

        embed.add_field(name="⚔️ Monster Parameters", value="\n".join(stats_lines), inline=False)
    else:
        # Resolve official Spell Speed and Property Icon for Spells and Traps
        prop_icon, prop_tag, speed_tier = format_spell_trap_property(card_type, card_subtype)
        csub_clean = card_subtype.strip() if card_subtype else "Normal"
        property_tag = f" [{prop_icon} Speed {speed_tier}]" if prop_icon else f" [Speed {speed_tier}]"

        embed.add_field(name="📜 Card Type", value=f"**{csub_clean} {card_type}**{property_tag}", inline=True)

    if card.get("pendulum_effect"):
        scale_badge = f" [Scale {card['scale']}]" if card.get("scale") is not None else ""
        embed.add_field(name=f"💎 Pendulum Effect{scale_badge}", value=f"```fix\n{card['pendulum_effect']}\n```", inline=False)

    effect_text = card.get("effect_text") or "No effect text recorded."
    embed.add_field(name="📖 Card Effect", value=f"```md\n{effect_text}\n```", inline=False)

    # Narrative Lore and Story Metadata
    meta = []
    if card.get("faction_name"):
        meta.append(f"**Faction:** {card['faction_name']}")
    if card.get("character_name"):
        meta.append(f"**Owner:** {card['character_name']}")
    if card.get("story_significance"):
        meta.append(f"**Role:** {card['story_significance']}")

    lore_content = []
    if card.get("lore_text"):
        lore_content.append(f"*{card['lore_text']}*")
    if meta:
        lore_content.append(" • ".join(meta))

    if lore_content:
        embed.add_field(name="🌌 Story Lore", value="\n\n".join(lore_content), inline=False)

    if card.get("image_url"):
        embed.set_thumbnail(url=card["image_url"])

    creator = card.get("creator_name") or "ProfessorSeanEX"
    passcode_str = format_passcode(card.get("id", "Unknown"))
    embed.set_footer(text=f"Passcode: {passcode_str} • Set: {set_num or 'TLOK'} • Designed by {creator} • Live in Simulator")
    return embed


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Card Usage Telemetry & Analytics (/card_stats)
# -----------------------------------------------------------------------------

def build_card_stats_embed(stats: Dict[str, Any]) -> discord.Embed:
    """
    Generates a card usage and telemetry overview embed.
    Includes deck inclusion counts, live duel appearances, and win rate.
    """
    cname = stats.get("name", "Unknown Card")
    set_num = stats.get("set_number", "")
    title = f"📈 Card Telemetry: {cname} [{set_num}]" if set_num else f"📈 Card Telemetry: {cname}"

    ctype = stats.get("card_type", "Monster")
    csub = stats.get("card_subtype", "Effect")
    attribute = stats.get("attribute")
    color = get_card_color(ctype, csub, attribute)

    embed = discord.Embed(
        title=title,
        description=f"**Type:** `{ctype} / {csub}` | **Rarity:** `{stats.get('rarity', 'Common')}`",
        color=color
    )

    times_decked = stats.get("times_decked", 0)
    times_drawn = stats.get("times_drawn", 0)
    times_played = stats.get("times_played", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = stats.get("win_rate", 0.0)

    embed.add_field(name="📦 Active Decks", value=f"Included in **{times_decked}** deck(s)", inline=True)
    embed.add_field(name="🃏 Duel Appearances", value=f"Drawn **{times_drawn}**x\nPlayed **{times_played}**x", inline=True)
    embed.add_field(name="🏆 Match Win Rate", value=f"**{win_rate}%** ({wins}W / {losses}L)", inline=True)

    embed.set_footer(text="Telemetry tracked live across player decks and Discord duels.")
    return embed


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Cardpool Catalog & Line Formatters (/cardpool, /recent_cards)
# -----------------------------------------------------------------------------

def format_cardpool_catalog_line(c: Dict[str, Any]) -> str:
    """
    Renders a single card entry into a catalog string with set codes,
    attributes, subtypes, ATK, and DEF/LINK metrics, respecting official
    Yu-Gi-Oh! card rules and EDOPro/YGOPro mechanics.
    """
    set_str = f"`{c['set_number']}`" if c.get("set_number") else f"`{format_passcode(c.get('id', ''))}`"
    card_type = c.get("card_type", "Monster")
    csub = c.get("card_subtype") or "Normal"

    if card_type == "Monster":
        csub_lower = csub.lower()
        attr = c.get("attribute", "DIVINE")
        attr_icon = ATTRIBUTE_ICONS.get(attr, "")
        attr_str = f"{attr_icon} {attr}" if attr_icon else attr
        lvl = c.get("level_or_rank_or_link") if c.get("level_or_rank_or_link") is not None else c.get("level", 0)

        # Distinguish Level vs Rank vs Link-Rating
        if "link" in csub_lower:
            arrow_str = format_link_arrows(c.get("link_arrows"))
            arrow_tag = f" {arrow_str.split(' [')[0]}" if arrow_str and " [" in arrow_str else ""
            rank_str = f"Link-{lvl}{arrow_tag}"
            def_str = "LINK"
        elif "xyz" in csub_lower:
            rank_str = f"Rank {lvl}"
            def_str = format_stat_value(c.get("def"))
        elif "pendulum" in csub_lower:
            scale = c.get("scale", 0)
            rank_str = f"★{lvl} [S:{scale}]"
            def_str = format_stat_value(c.get("def"))
        else:
            rank_str = f"★{lvl}"
            def_str = format_stat_value(c.get("def"))

        atk_str = format_stat_value(c.get("atk"))
        return f"{set_str} **{c['name']}** [{attr_str} | {csub} | {rank_str}] — ATK {atk_str} / DEF {def_str}"
    else:
        # Include property icons for spells/traps in catalog display
        prop_icon, _, _ = format_spell_trap_property(card_type, csub)
        icon_str = f"{prop_icon} " if prop_icon else ""
        return f"{set_str} **{c['name']}** [{icon_str}{csub} {card_type}]"


def add_chunked_catalog_fields(
    embed: discord.Embed,
    category_title: str,
    lines: List[str],
    max_field_length: int = 1000
) -> None:
    """
    Safely partitions catalog lines into multiple embed fields such that no individual
    field value exceeds Discord's strict 1024-character payload limit.
    Accounts for large and growing cardpools without payload rejection.
    """
    if not lines:
        return

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for line in lines:
        line_len = len(line) + 1  # include newline
        if current_chunk and (current_length + line_len > max_field_length):
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_len
        else:
            current_chunk.append(line)
            current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    if len(chunks) == 1:
        embed.add_field(name=f"{category_title} ({len(lines)})", value=chunks[0], inline=False)
    else:
        for idx, chunk in enumerate(chunks, start=1):
            embed.add_field(
                name=f"{category_title} (Part {idx}/{len(chunks)} • {len(lines)} Total)",
                value=chunk,
                inline=False
            )


def build_cardpool_catalog_embed(
    cards: List[Dict[str, Any]],
    category: str = "all",
    set_code: Optional[str] = None
) -> discord.Embed:
    """
    Constructs an authoritative, scalable cardpool catalog embed.
    Accounts for a growing cardpool across multiple sets and classifications without
    hitting Discord payload ceilings.
    """
    filtered = cards
    if set_code:
        clean_set = set_code.strip().upper()
        filtered = [
            c for c in cards
            if (c.get("set_code") or "").upper() == clean_set
            or (c.get("set_number") or "").upper().startswith(clean_set)
        ]

    monsters = [c for c in filtered if c.get("card_type") == "Monster"]
    spells = [c for c in filtered if c.get("card_type") == "Spell"]
    traps = [c for c in filtered if c.get("card_type") == "Trap"]
    extra_deck = [
        c for c in filtered
        if any(m in (c.get("card_subtype") or "").lower() for m in ("fusion", "synchro", "xyz", "link"))
        or (c.get("card_type") or "").lower() in ("fusion", "synchro", "xyz", "link")
    ]

    cat_lower = (category or "all").lower()

    if cat_lower == "overview" or (cat_lower == "all" and len(filtered) > 20):
        embed = discord.Embed(
            title="🌌 The Land of Kustomazi — Live Cardpool Catalog",
            description=(
                f"**Total Registered Cards:** {len(filtered)}\n"
                f"Authoritative custom cards registered in the database, compiled into "
                f"`custom_cards.cdb`, and live in the EDOPro simulator."
            ),
            color=0xF59E0B
        )

        embed.add_field(
            name="📊 Card Distribution",
            value=(
                f"• ⚔️ **Monsters:** {len(monsters)}\n"
                f"• ✨ **Spells:** {len(spells)}\n"
                f"• 🛡️ **Traps:** {len(traps)}\n"
                f"• 🌌 **Extra Deck:** {len(extra_deck)}"
            ),
            inline=True
        )

        distinct_sets = sorted(list({c.get("set_code") or (c.get("set_number", "").split("-")[0] if "-" in c.get("set_number", "") else "CUSTOM") for c in filtered}))
        sets_str = ", ".join(f"`{s}`" for s in distinct_sets) if distinct_sets else "`TLOK`"
        embed.add_field(
            name="📦 Sets Registered",
            value=f"• **Active Sets:** {sets_str}\n• **Total Sets:** {len(distinct_sets)}",
            inline=True
        )

        factions = sorted(list({c.get("faction_name") or c.get("archetype") for c in filtered if c.get("faction_name") or c.get("archetype")}))
        if factions:
            fac_str = "\n".join(f"• {f}" for f in factions[:5])
            embed.add_field(name="🏛️ Factions & Archetypes", value=fac_str, inline=False)

        embed.set_footer(text="Select a category from the dropdown menu below to browse cards!")
        return embed

    elif cat_lower == "monsters":
        embed = discord.Embed(
            title=f"⚔️ Monster Cards Catalog ({len(monsters)} Cards)",
            description=f"Browsing **{len(monsters)}** monster cards in the active cardpool.",
            color=0xD97706
        )
        lines = [format_cardpool_catalog_line(m) for m in monsters]
        add_chunked_catalog_fields(embed, "⚔️ Monsters", lines)
        embed.set_footer(text="Use /card <name> to view full stats, artwork, and lore.")
        return embed

    elif cat_lower == "spells":
        embed = discord.Embed(
            title=f"✨ Spell Cards Catalog ({len(spells)} Cards)",
            description=f"Browsing **{len(spells)}** spell cards in the active cardpool.",
            color=0x059669
        )
        lines = [format_cardpool_catalog_line(s) for s in spells]
        add_chunked_catalog_fields(embed, "✨ Spells", lines)
        embed.set_footer(text="Use /card <name> to view full stats, artwork, and lore.")
        return embed

    elif cat_lower == "traps":
        embed = discord.Embed(
            title=f"🛡️ Trap Cards Catalog ({len(traps)} Cards)",
            description=f"Browsing **{len(traps)}** trap cards in the active cardpool.",
            color=0xDC2626
        )
        lines = [format_cardpool_catalog_line(t) for t in traps]
        add_chunked_catalog_fields(embed, "🛡️ Traps", lines)
        embed.set_footer(text="Use /card <name> to view full stats, artwork, and lore.")
        return embed

    elif cat_lower == "extra_deck":
        embed = discord.Embed(
            title=f"🌌 Extra Deck Monsters ({len(extra_deck)} Cards)",
            description=f"Browsing **{len(extra_deck)}** Fusion, Synchro, Xyz, and Link monsters.",
            color=0x7C3AED
        )
        lines = [format_cardpool_catalog_line(e) for e in extra_deck]
        add_chunked_catalog_fields(embed, "🌌 Extra Deck", lines)
        embed.set_footer(text="Use /card <name> to view full stats, artwork, and lore.")
        return embed

    else:
        embed = discord.Embed(
            title="🌌 The Land of Kustomazi — Set 1 Cardpool",
            description=(
                f"**Total Registered Cards:** {len(filtered)}\n"
                f"All cards are live in the EDOPro simulator and compiled into `custom_cards.cdb`.\n"
                f"View the web catalog at `http://thelandofkustomazi.com` or local port `8000`."
            ),
            color=0xF59E0B
        )
        if monsters:
            lines = [format_cardpool_catalog_line(m) for m in monsters]
            add_chunked_catalog_fields(embed, "⚔️ Monster Cards", lines)
        if spells:
            lines = [format_cardpool_catalog_line(s) for s in spells]
            add_chunked_catalog_fields(embed, "✨ Spell Cards", lines)
        if traps:
            lines = [format_cardpool_catalog_line(t) for t in traps]
            add_chunked_catalog_fields(embed, "🛡️ Trap Cards", lines)

        embed.set_footer(text="Use /card <name> to view complete card artwork, stats, and effects!")
        return embed


def build_recent_cards_embed(cards: List[Dict[str, Any]]) -> discord.Embed:
    """
    Constructs an embed displaying recently registered custom cards in chronological order.
    Honors EDOPro and Yu-Gi-Oh! mechanics across all card classifications.
    """
    embed = discord.Embed(
        title=f"🆕 Custom Card Pool ({len(cards)} Cards Displayed)",
        description="These cards are live in the cardpool and ready for duels in the live simulator!",
        color=0x3498DB
    )

    for c in cards:
        card_type = c.get("card_type", "Spell")
        csub = c.get("card_subtype") or "Normal"
        creator = c.get("creator_name") or "ProfessorSeanEX"
        set_code = c.get("set_number") or f"ID:{format_passcode(c.get('id', ''))}"

        if card_type == "Monster":
            csub_lower = csub.lower()
            lvl = c.get("level_or_rank_or_link") if c.get("level_or_rank_or_link") is not None else c.get("level", 0)
            if "link" in csub_lower:
                rank_str = f"Link-{lvl}"
                def_str = "LINK"
            elif "xyz" in csub_lower:
                rank_str = f"Rank {lvl}"
                def_str = format_stat_value(c.get("def"))
            else:
                rank_str = f"★{lvl}"
                def_str = format_stat_value(c.get("def"))

            atk_str = format_stat_value(c.get("atk"))
            attr = c.get("attribute", "DIVINE")
            stats = f"{attr} | {csub} {card_type} ({rank_str}) | ATK {atk_str} / DEF {def_str}"
        else:
            prop_icon, speed_tag, _ = format_spell_trap_property(card_type, csub)
            icon_prefix = f"{prop_icon} " if prop_icon else ""
            stats = f"{icon_prefix}{csub} {card_type} [{speed_tag.split(' [')[-1]}"

        embed.add_field(
            name=f"[{set_code}] {c['name']} ({c.get('rarity') or 'Common'})",
            value=f"{stats}\n*Designed by {creator}*",
            inline=False
        )

    return embed


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Server Macro Telemetry & Meta Presentation (/meta)
# -----------------------------------------------------------------------------

def build_meta_telemetry_embed(meta: Dict[str, Any]) -> discord.Embed:
    """
    Constructs a rich overview embed displaying top custom cards by popularity and win rate.
    """
    embed = discord.Embed(
        title="📊 The Land of Kustomazi — Set 1 Meta Telemetry",
        description="Live statistics derived from player decks and live Discord duels.",
        color=0x3B82F6
    )

    pop_lines = []
    for c in meta.get("most_popular", []):
        set_str = f"[{c['set_number']}] " if c.get("set_number") else ""
        pop_lines.append(f"• **{set_str}{c['name']}**: In **{c['times_decked']}** deck(s) | Played **{c['times_played']}**x")

    embed.add_field(
        name="🔥 Most Popular in Decks",
        value="\n".join(pop_lines) if pop_lines else "*No deck data recorded yet.*",
        inline=False
    )

    win_lines = []
    for c in meta.get("most_victorious", []):
        set_str = f"[{c['set_number']}] " if c.get("set_number") else ""
        total = c["wins"] + c["losses"]
        wr = round((c["wins"] / total * 100), 1) if total > 0 else 0.0
        win_lines.append(f"• **{set_str}{c['name']}**: **{c['wins']} Wins** ({wr}% WR)")

    embed.add_field(
        name="🏆 Most Victorious in Matchups",
        value="\n".join(win_lines) if win_lines else "*No match telemetry recorded yet.*",
        inline=False
    )

    embed.set_footer(text="Play in /duel or add cards in /deck_add to influence meta telemetry!")
    return embed


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Master Rules Educational Guide & Category Router (/card_types)
# -----------------------------------------------------------------------------

def build_card_types_guide_embed(category: Optional[str] = None) -> discord.Embed:
    """
    Constructs a rich educational Discord Embed explaining Yu-Gi-Oh! card types,
    spell speeds, monster summoning frames, the 26 official monster races,
    elemental attributes, and Level vs Rank rules.
    """
    cat = (category or "overview").strip().lower()

    if cat == "spells":
        embed = discord.Embed(
            title="📗 Yu-Gi-Oh! Card Classification — Spell Cards",
            description="Spells provide instant, continuous, or environmental advantages. Identified by their top-right icon:",
            color=FRAME_COLORS["spell"]
        )
        for name, data in SPELL_CARD_TYPES.items():
            icon_str = f" `{data['icon']}`" if data['icon'] != "None" else ""
            embed.add_field(
                name=f"{name}{icon_str} [{data['speed']}]",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="Spell Speed 1: Normal, Continuous, Equip, Field, Ritual • Spell Speed 2: Quick-Play")
        return embed

    elif cat == "traps":
        embed = discord.Embed(
            title="📕 Yu-Gi-Oh! Card Classification — Trap Cards",
            description="Traps must be Set face-down for at least 1 turn before activation. Used to disrupt the opponent:",
            color=FRAME_COLORS["trap"]
        )
        for name, data in TRAP_CARD_TYPES.items():
            icon_str = f" `{data['icon']}`" if data['icon'] != "None" else ""
            embed.add_field(
                name=f"{name}{icon_str} [{data['speed']}]",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="Spell Speed 2: Normal, Continuous • Spell Speed 3: Counter Traps (Only Counter Traps can respond!)")
        return embed

    elif cat == "monsters":
        embed = discord.Embed(
            title="📙 Yu-Gi-Oh! Card Classification — Monster Categories & Frames",
            description="Monsters battle for field control and reduce the opponent's Life Points. Categorized by frame & summon mechanic:",
            color=FRAME_COLORS["effect"]
        )
        for frame, desc in MONSTER_CARD_FRAMES.items():
            embed.add_field(name=frame, value=desc, inline=False)
        embed.add_field(
            name="Sub-Classifications",
            value="• **Tuner:** Synchro material\n• **Flip:** Triggers on flip face-up\n• **Union:** Equips to other monsters\n• **Spirit:** Returns to hand at End Phase\n• **Gemini:** Re-summon to unlock effect",
            inline=False
        )
        embed.set_footer(text="Main Deck: Normal, Effect, Ritual, Pendulum • Extra Deck: Fusion, Synchro, Xyz, Link")
        return embed

    elif cat == "races":
        embed = discord.Embed(
            title="🐉 Yu-Gi-Oh! The 26 Official Monster Types (Races)",
            description="Printed on every monster card `[Type / Subtype]`. Distinguishes tribal synergy, not to be confused with Attributes (elements):",
            color=FRAME_COLORS["divine"]
        )
        col1 = []
        col2 = []
        for i, (race, desc) in enumerate(ALL_26_MONSTER_RACES):
            line = f"• **{race}**: *{desc}*"
            if i < 13:
                col1.append(line)
            else:
                col2.append(line)

        embed.add_field(name="Part 1 (Types 1-13)", value="\n".join(col1), inline=False)
        embed.add_field(name="Part 2 (Types 14-26)", value="\n".join(col2), inline=False)
        embed.set_footer(text="All 26 Official Yu-Gi-Oh! Monster Types • The Land of Kustomazi Platform")
        return embed

    elif cat == "attributes":
        embed = discord.Embed(
            title="✨ Yu-Gi-Oh! The 7 Elemental Card Attributes",
            description=(
                "Located in the upper-right corner of Monster cards. Dictates elemental alignment, "
                "attribute locking (e.g. *Gozen Match*), and fusion/archetype synergy:"
            ),
            color=0xF1C40F
        )
        for attr_name, data in CARD_ATTRIBUTES.items():
            embed.add_field(
                name=f"{data['symbol']} {attr_name} ({data['kanji']}) [Bitmask: {hex(data['bitmask'])}]",
                value=data["description"],
                inline=False
            )
        embed.set_footer(text="The 7 Canonical Attributes: LIGHT, DARK, EARTH, WATER, FIRE, WIND, DIVINE")
        return embed

    elif cat in ("levels_ranks", "levels", "ranks"):
        embed = discord.Embed(
            title="⭐ Yu-Gi-Oh! Monster Anatomy: Levels, Ranks & Scales",
            description="Every monster features distinct numeric scaling determining how it enters the field and participates in Extra Deck summons:",
            color=0xF39C12
        )
        lv_data = LEVELS_AND_RANKS_DATA["levels"]
        embed.add_field(
            name=f"{lv_data['title']} — {lv_data['stars_icon']}",
            value="\n".join(lv_data["tribute_rules"]) + "\n" + "\n".join(lv_data["summon_math"]),
            inline=False
        )

        rk_data = LEVELS_AND_RANKS_DATA["ranks"]
        embed.add_field(
            name=f"{rk_data['title']} — {rk_data['stars_icon']}",
            value=f"{rk_data['golden_rule']}\n" + "\n".join(rk_data["consequences"]) + "\n" + "\n".join(rk_data["xyz_mechanics"]),
            inline=False
        )

        lnk_data = LEVELS_AND_RANKS_DATA["link_ratings"]
        embed.add_field(
            name=lnk_data["title"],
            value=f"• **Stats:** {lnk_data['stats']}\n• **Rating:** {lnk_data['link_rating']}\n• **Arrows:** {lnk_data['link_arrows']}",
            inline=False
        )

        pen_data = LEVELS_AND_RANKS_DATA["pendulum_scales"]
        embed.add_field(
            name=pen_data["title"],
            value=f"• **Zones:** {pen_data['placement']}\n• **Summon Range:** {pen_data['pendulum_summon']}",
            inline=False
        )
        embed.set_footer(text="Master Rule 2020: Levels (Stars) • Ranks (Black Orbs) • Links (No DEF) • Scales (Summon Range)")
        return embed

    elif cat in ("subtypes", "subtype", "gemini"):
        embed = discord.Embed(
            title="🧬 Yu-Gi-Oh! Monster Sub-Classifications & Mechanics",
            description=(
                "Beyond primary card frames, monsters often bear sub-classifications defining unique "
                "field interaction rules, summoning conditions, or continuous states:"
            ),
            color=0x9B59B6
        )
        for sub_name, desc in MONSTER_SUBTYPES.items():
            embed.add_field(name=f"• {sub_name}", value=desc, inline=False)
        embed.add_field(
            name="🎃 Set 1 Spotlight: Gemini Monsters (LeSpookie Archetype)",
            value=(
                "Set 1 features **10 Gemini Monsters**! When Normal Summoned, they enter as Normal Monsters "
                "(no effect). While face-up on the field, you can use your turn's Normal Summon to 'Second Summon' "
                "them, permanently unlocking their powerful effects and Trick-or-Treat counter synergies!"
            ),
            inline=False
        )
        embed.set_footer(text="Official Subtypes: Gemini, Tuner, Flip, Union, Spirit, Toon • The Land of Kustomazi")
        return embed

    elif cat in ("spell_speeds", "speeds", "chains", "speed"):
        embed = discord.Embed(
            title="⚡ Yu-Gi-Oh! Spell Speeds & Chain Resolution Rules",
            description=(
                "Yu-Gi-Oh! card interactions operate on strict timing hierarchies known as **Spell Speeds (1, 2, and 3)**. "
                "A card or effect can only chain to an effect of equal or lower Spell Speed (except Speed 1 which cannot chain):"
            ),
            color=0xE67E22
        )
        for speed_name, data in SPELL_SPEEDS_DATA.items():
            embed.add_field(
                name=f"{data['speed']}",
                value=f"• **Cards:** {data['cards']}\n• **Chain Rule:** {data['chain_rule']}\n• **Timing:** {data['timing']}",
                inline=False
            )
        embed.set_footer(text="Chains resolve backwards (LIFO: Last In, First Out) • Spell Speed 3 is the fastest tier")
        return embed

    else:
        # Complete Overview
        embed = discord.Embed(
            title="🃏 Master Guide: Yu-Gi-Oh! Card Anatomy & Classifications",
            description="Yu-Gi-Oh! cards are governed by rigid structural classifications, elemental affinities, and numeric scaling.",
            color=0x3B82F6
        )
        embed.add_field(
            name="1. 📗 Spell Cards (6 Types)",
            value="• **Normal Spell** [Speed 1]\n• **Continuous Spell** `∞` [Speed 1]\n• **Equip Spell** `+` [Speed 1]\n• **Quick-Play Spell** `⚡` [Speed 2]\n• **Field Spell** `⨁` [Speed 1]\n• **Ritual Spell** `🔥` [Speed 1]",
            inline=True
        )
        embed.add_field(
            name="2. 📕 Trap Cards (3 Types)",
            value="• **Normal Trap** [Speed 2]\n• **Continuous Trap** `∞` [Speed 2]\n• **Counter Trap** `⤶` [Speed 3 — Unresponsive except by Counter Traps!]",
            inline=True
        )
        embed.add_field(
            name="3. 📙 Monster Frames & Mechanics",
            value="• **Main Deck:** Normal, Effect, Ritual, Pendulum\n• **Extra Deck:** Fusion, Synchro, Xyz, Link\n• **Special:** Tuner, Flip, Union, Spirit, Gemini, Token",
            inline=True
        )
        embed.add_field(
            name="4. 🧬 Subtypes & Gemini",
            value="• **Gemini:** Normal until 2nd Summon (*LeSpookie* archetype!)\n• **Tuner, Flip, Union, Spirit, Toon**",
            inline=True
        )
        embed.add_field(
            name="5. ⚡ Spell Speeds & Chains",
            value="• **Speed 1:** Ignition / Normal / Spells\n• **Speed 2:** Quick Effects & Traps\n• **Speed 3:** Counter Traps (Only SS3 responds!)",
            inline=True
        )
        embed.add_field(
            name="6. ✨ The 7 Attributes",
            value="☀️ **LIGHT** • 🌑 **DARK** • ⛰️ **EARTH** • 🌊 **WATER** • 🔥 **FIRE** • 🌪️ **WIND** • ✨ **DIVINE**",
            inline=True
        )
        embed.add_field(
            name="7. ⭐ Levels VS Ranks",
            value="• **Levels (1-12):** Stars ⭐. Determines 0/1/2 Tributes and Synchro/Ritual math.\n• **Ranks (1-13):** Black Stars ⯪. **RANKS ARE NOT LEVELS!** Overlaid Xyz materials.",
            inline=True
        )
        races_preview = ", ".join([r[0] for r in ALL_26_MONSTER_RACES[:10]]) + f", ... (+{len(ALL_26_MONSTER_RACES)-10} more)"
        embed.add_field(
            name="8. 🐉 The 26 Monster Types (Races)",
            value=f"Tribal classifications distinguishing species: *{races_preview}*",
            inline=False
        )
        embed.set_footer(text="Use /card_types [category] or the dropdown menu below to inspect each section in detail!")
        return embed


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Sub-Block 3.1: Individual Card Inspection Presentation
    "build_card_embed",
    # Sub-Block 3.2: Card Usage Telemetry
    "build_card_stats_embed",
    # Sub-Block 3.3: Cardpool Catalog & Line Formatters
    "format_cardpool_catalog_line",
    "add_chunked_catalog_fields",
    "build_cardpool_catalog_embed",
    "build_recent_cards_embed",
    # Sub-Block 3.4: Server Macro Telemetry
    "build_meta_telemetry_embed",
    # Sub-Block 3.5: Master Rules Educational Guide
    "build_card_types_guide_embed",
    # Re-exported Foundation Formatters & Invariant Primitives
    "STAT_UNKNOWN",
    "format_passcode",
    "format_stat_value",
    "format_link_arrows",
    "format_spell_trap_property",
    "get_spell_speed",
    "format_monster_classification",
    "LINK_ARROW_GLYPHS",
    "LINK_BIT_MAP",
    "ATTRIBUTE_ICONS",
    "SPELL_TRAP_ICONS",
]
