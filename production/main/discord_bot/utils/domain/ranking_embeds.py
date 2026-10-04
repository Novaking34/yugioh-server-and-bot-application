# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.domain.ranking_embeds
Description:
    Competitive Ranking & Leaderboard Presentation Embed Builders.
    Constructs rich Discord embeds for Duelist Licenses (/rank)
    and seasonal competitive leaderboards (/leaderboard).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Optional
import discord

# =============================================================================
# BLOCK 3: BODY BLOCK (Ranking Embed Generators)
# =============================================================================

def build_rank_embed(player: Dict[str, Any], user: Optional[discord.User] = None) -> discord.Embed:
    """
    Constructs an authentic Duelist License / Ranking card embed.
    """
    from services.rating import RatingService
    elo = player.get("elo", 1200)
    tier_name, badge, color = RatingService.get_tier_info(elo)
    username = player.get("username") or (user.display_name if user else "Duelist")

    wins = player.get("wins", 0)
    losses = player.get("losses", 0)
    draws = player.get("draws", 0)
    total_games = wins + losses + draws
    win_rate = round((wins / total_games * 100), 1) if total_games > 0 else 0.0

    streak = player.get("win_streak", 0)
    best_streak = player.get("highest_streak", streak)
    highest_elo = player.get("highest_elo", elo)
    season = player.get("season_id", "Season 1")

    embed = discord.Embed(
        title=f"🪪 Official Duelist License — {username}",
        description=f"**Current Division:** {badge} **{tier_name}**\n*The Land of Kustomazi Custom Card League ({season})*",
        color=color
    )

    embed.add_field(name="⚔️ Competitive Rating", value=f"**{elo} ELO**\n*(Peak: {highest_elo} ELO)*", inline=True)
    embed.add_field(name="📊 Win Rate", value=f"**{win_rate}%**\n`{wins}W - {losses}L - {draws}D`", inline=True)
    embed.add_field(name="🔥 Current Streak", value=f"**{streak} Wins**\n*(Best: {best_streak})*", inline=True)

    if user and user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)

    embed.set_footer(text=f"Duelist ID: {player.get('user_id')} • FIDE K=32 • Set 1: The Land of Kustomazi")
    return embed


def build_leaderboard_embed(entries: List[Dict[str, Any]], season_id: str = "Season 1") -> discord.Embed:
    """
    Constructs a rich competitive leaderboard for the custom card league.
    """
    from services.rating import RatingService
    embed = discord.Embed(
        title=f"🏆 The Land of Kustomazi — Leaderboard ({season_id})",
        description="Top rated duelists battling with Set 1 custom cards.",
        color=0xF59E0B
    )

    if not entries:
        embed.description += "\n\n*No ranked duels recorded yet for this season. Be the first to duel!*"
        return embed

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(entries, start=1):
        medal = medals[i-1] if i <= 3 else f"`#{i}`"
        _, badge, _ = RatingService.get_tier_info(p["elo"])
        uname = p.get("username", "Unknown")
        streak_str = f" 🔥{p['win_streak']}" if p.get("win_streak", 0) >= 3 else ""
        wins = p.get("wins", 0)
        losses = p.get("losses", 0)
        wr = p.get("win_rate")
        if wr is None:
            tot = wins + losses + p.get("draws", 0)
            wr = round((wins / tot * 100), 1) if tot > 0 else 0.0
        lines.append(
            f"{medal} {badge} **{uname}** — **{p['elo']} ELO** "
            f"({wins}W/{losses}L | {wr}%){streak_str}"
        )

    embed.add_field(name="Rankings", value="\n".join(lines), inline=False)
    embed.set_footer(text="Use /duel to challenge an opponent to a Ranked match and climb the ladder!")
    return embed


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "build_rank_embed",
    "build_leaderboard_embed",
]
