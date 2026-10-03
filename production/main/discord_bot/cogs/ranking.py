#!/usr/bin/env python3
"""
=============================================================================
Discord Bot Cog: Competitive ELO & Duelist Rankings
=============================================================================
Provides slash commands for community members to inspect their official
duelist license, view server leaderboard standings, and check tier criteria.
=============================================================================
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from services.rating_service import RatingService, TIER_BRACKETS
from utils import build_rank_embed, build_leaderboard_embed
from production.main.logger import get_logger

logger = get_logger("discord_bot.cogs.ranking")


class RankingCog(commands.Cog, name="Ranking"):
    """Commands for competitive ELO ratings, leaderboards, and tier progression."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rating_service = RatingService()

    @app_commands.command(name="rank", description="View your or another duelist's official rating license and stats")
    @app_commands.describe(user="The duelist to inspect (defaults to yourself)")
    async def rank_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Displays duelist rating, tier badge, win rate, and win streak."""
        target_user = user or interaction.user
        player_data = await self.rating_service.get_or_create_player(
            str(target_user.id),
            username=target_user.display_name
        )
        embed = build_rank_embed(player_data, user=target_user)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View top-ranked custom card duelists in The Land of Kustomazi")
    @app_commands.describe(season="Ranking season identifier (default: Season 1)")
    async def leaderboard_command(self, interaction: discord.Interaction, season: Optional[str] = "Season 1"):
        """Displays top 10 duelists ordered by ELO score."""
        entries = await self.rating_service.get_leaderboard(limit=10, season_id=season or "Season 1")
        embed = build_leaderboard_embed(entries, season_id=season or "Season 1")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rank_tiers", description="View official ELO brackets, tier badges, and rank requirements")
    async def rank_tiers_command(self, interaction: discord.Interaction):
        """Displays all competitive rank tiers and their requirements."""
        embed = discord.Embed(
            title="🏅 Custom Card League — Rank Division System",
            description="Compete in `/duel` Ranked matches to earn ELO and ascend through the competitive divisions.",
            color=0x3B82F6
        )

        for min_elo, name, badge, _ in TIER_BRACKETS:
            threshold = f"**{min_elo}+ ELO**" if min_elo > 0 else "**Placement / <1100 ELO**"
            embed.add_field(
                name=f"{badge} {name}",
                value=f"Threshold: {threshold}",
                inline=True
            )

        embed.set_footer(text="Default Starting ELO: 1200 • FIDE K=32 • Set 1: The Land of Kustomazi")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Extension loader entrypoint."""
    await bot.add_cog(RankingCog(bot))
