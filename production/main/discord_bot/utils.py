#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Formatting & UI Utilities
=============================================================================
Provides card frame color palettes, parameter formatters, and rich Discord
embed generators matching authentic Yu-Gi-Oh! visual styles.
=============================================================================
"""

import discord
from typing import Optional, Dict, Any

# Standard Yu-Gi-Oh! Card Frame Hex Colors
FRAME_COLORS = {
    'normal': 0xD4B37F,       # Normal Monster Yellow
    'effect': 0xC97434,       # Effect Monster Orange
    'ritual': 0x6E9ED4,       # Ritual Blue
    'fusion': 0x9356A0,       # Fusion Violet
    'synchro': 0xEEEEEE,      # Synchro White
    'xyz': 0x111111,          # Xyz Black
    'link': 0x0055AA,         # Link Dark Blue
    'spell': 0x1D9E74,        # Spell Green
    'trap': 0xBC3576          # Trap Magenta
}


def get_card_color(card_type: Optional[str], card_subtype: Optional[str]) -> int:
    """
    Selects the authentic Discord embed border color corresponding to
    the card's frame category.
    """
    ctype = (card_type or '').strip().lower()
    csub = (card_subtype or '').strip().lower()

    if ctype == 'spell':
        return FRAME_COLORS['spell']
    if ctype == 'trap':
        return FRAME_COLORS['trap']

    # For monsters, check specific summon frames in priority order
    for mechanic in ['link', 'xyz', 'synchro', 'fusion', 'ritual', 'effect', 'normal']:
        if mechanic in csub:
            return FRAME_COLORS[mechanic]

    return FRAME_COLORS['effect']


def build_card_embed(card: Dict[str, Any]) -> discord.Embed:
    """
    Constructs a rich Discord Embed displaying the card's artwork,
    stats, Pendulum scales, effect text, and story lore.
    """
    color = get_card_color(card.get("card_type"), card.get("card_subtype"))
    card_type = card.get("card_type") or "Monster"
    card_subtype = card.get("card_subtype") or "Effect"

    embed = discord.Embed(
        title=f"{card['name']}",
        url=card.get("duelingbook_url") or f"https://www.duelingbook.com/card?id={card['id']}",
        description=f"**[{card_type} / {card_subtype}]**",
        color=color
    )

    if card_type == "Monster":
        stats_line = f"**Attribute:** {card.get('attribute') or 'N/A'} | **Type:** {card.get('monster_type') or 'N/A'}"
        csub_lower = card_subtype.lower()

        if "link" in csub_lower:
            stats_line += f"\n**Link Rating:** Link-{card.get('level_or_rank_or_link') or 0} | **Arrows:** {card.get('link_arrows') or 'N/A'}"
        elif "xyz" in csub_lower:
            stats_line += f"\n**Rank:** {card.get('level_or_rank_or_link') or 0}"
        else:
            stats_line += f"\n**Level:** {card.get('level_or_rank_or_link') or 0}"

        if card.get("scale") is not None:
            stats_line += f" | **Scale:** {card['scale']}"

        def_val = "LINK" if "link" in csub_lower else (card.get("def") if card.get("def") is not None else 0)
        stats_line += f"\n**ATK:** {card.get('atk', 0)} / **DEF:** {def_val}"
        embed.add_field(name="⚔️ Monster Parameters", value=stats_line, inline=False)
    else:
        embed.add_field(name="📜 Card Type", value=f"**{card_subtype} {card_type}**", inline=True)

    if card.get("pendulum_effect"):
        embed.add_field(name="💎 Pendulum Effect", value=f"```fix\n{card['pendulum_effect']}\n```", inline=False)

    effect_text = card.get("effect_text") or "No effect text recorded."
    embed.add_field(name="📖 Card Effect", value=f"```md\n{effect_text}\n```", inline=False)

    # Narrative Lore metadata
    lore_field = f"*{card.get('lore_text') or 'No lore recorded.'}*"
    meta = []
    if card.get("faction_name"):
        meta.append(f"**Faction:** {card['faction_name']}")
    if card.get("character_name"):
        meta.append(f"**Owner:** {card['character_name']}")
    if card.get("story_significance"):
        meta.append(f"**Role:** {card['story_significance']}")
    if meta:
        lore_field += "\n\n" + " • ".join(meta)

    embed.add_field(name="🌌 Story Lore", value=lore_field, inline=False)

    if card.get("image_url"):
        embed.set_thumbnail(url=card["image_url"])

    creator = card.get("creator_name") or "Custom Designer"
    embed.set_footer(text=f"Passcode: {card['id']} • Designed by {creator} • Live in Simulator")
    return embed
