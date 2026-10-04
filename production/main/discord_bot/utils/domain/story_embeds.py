# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.domain.story_embeds
Description:
    Story Campaign & RPG Encounter Presentation Embed Builders.
    Constructs rich Discord embeds for story chapters, stage objectives,
    boss profiles, NPC dialogue, and first-time clear rewards (/story).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict
import discord

# =============================================================================
# BLOCK 3: BODY BLOCK (Story Embed Generators)
# =============================================================================

def build_story_stage_embed(stage: Dict[str, Any], progress: Dict[str, Any]) -> discord.Embed:
    """
    Builds an RPG story encounter embed displaying dialogue, boss profile, and rewards.
    """
    embed = discord.Embed(
        title=f"🌌 Story Chapter 1 — Stage {stage['stage_number']}: {stage['title']}",
        description=f"*{stage['intro_dialogue']}*",
        color=0x8B5CF6
    )

    opp_title = f" ({stage['opponent_title']})" if stage.get("opponent_title") else ""
    deck_name = stage.get("opponent_deck_name") or "Kasutamaiza - Creation Control"
    embed.add_field(
        name="⚔️ Encounter Challenger",
        value=f"**{stage['opponent_name']}**{opp_title}\nDeck: *{deck_name}*",
        inline=False
    )

    rewards = []
    if stage.get("reward_title"):
        rewards.append(f"🏅 Title: **{stage['reward_title']}**")
    if stage.get("reward_card_name"):
        set_num = f" [{stage.get('reward_card_set')}]" if stage.get('reward_card_set') else ""
        rewards.append(f"🃏 Custom Card: **{stage['reward_card_name']}**{set_num}")

    if rewards:
        embed.add_field(name="🎁 First-Time Clear Rewards", value="\n".join(rewards), inline=False)

    highest = progress.get("highest_stage_completed", 0)
    is_cleared = (highest >= stage["stage_number"])
    status = "✅ Completed (Replayable)" if is_cleared else "⏳ In Progress / Uncompleted"
    embed.add_field(name="📜 Mission Status", value=f"**{status}**", inline=False)

    if stage.get("opponent_avatar"):
        embed.set_thumbnail(url=stage["opponent_avatar"])

    embed.set_footer(text="Click 'Begin Story Duel' below to challenge this encounter!")
    return embed


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "build_story_stage_embed",
]
