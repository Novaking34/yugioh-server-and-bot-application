#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.cogs.ranking
Description:
    Discord Bot Cog: Competitive ELO & Duelist Rankings Presentation Gateway.
    Provides slash commands for community members to inspect their official
    duelist license, view seasonal leaderboard standings, and check tier criteria.

Architectural Classification:
    Layer 3 (L3) - Presentation & Discord Gateway Cog
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Layered Package Imports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 2.1: Discord & Async Primitives
# -----------------------------------------------------------------------------
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

# -----------------------------------------------------------------------------
# Sub-Block 2.2: Services & Domain Subsystems
# -----------------------------------------------------------------------------
from services.rating import RatingService, TIER_BRACKETS, rating_service

# -----------------------------------------------------------------------------
# Sub-Block 2.3: Foundation & Visual Helpers
# -----------------------------------------------------------------------------
from utils import build_rank_embed, build_leaderboard_embed
from production.main.logger import get_logger

# -----------------------------------------------------------------------------
# Sub-Block 2.4: System Logger
# -----------------------------------------------------------------------------
logger = get_logger("discord_bot.cogs.ranking")


# =============================================================================
# BLOCK 3: BODY BLOCK (Ranking Slash Commands Cog)
# =============================================================================

class RankingCog(commands.Cog, name="Ranking"):
    """Commands for competitive ELO ratings, leaderboards, and tier progression."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rating_service: RatingService = rating_service

    # -------------------------------------------------------------------------
    # Sub-Block 3.1: Duelist License & Profile Command (/rank)
    # -------------------------------------------------------------------------
    @app_commands.command(name="rank", description="View your or another duelist's official rating license and stats")
    @app_commands.describe(
        user="The duelist to inspect (defaults to yourself)",
        hidden="Whether to display the license ephemerally (Default: False)"
    )
    async def rank_command(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
        hidden: Optional[bool] = False
    ):
        """Displays duelist rating, tier badge, win rate, and win streak."""
        target_user = user or interaction.user
        player_data = await self.rating_service.get_or_create_player(
            str(target_user.id),
            username=target_user.display_name
        )
        embed = build_rank_embed(player_data, user=target_user)
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))

    # -------------------------------------------------------------------------
    # Sub-Block 3.2: Seasonal Leaderboard Command (/leaderboard)
    # -------------------------------------------------------------------------
    @app_commands.command(name="leaderboard", description="View top-ranked custom card duelists in The Land of Kustomazi")
    @app_commands.describe(
        season="Ranking season identifier (default: Season 1)",
        limit="Maximum number of leaderboard standings to show (1-50, default: 10)",
        hidden="Whether to display the leaderboard ephemerally (Default: False)"
    )
    async def leaderboard_command(
        self,
        interaction: discord.Interaction,
        season: Optional[str] = "Season 1",
        limit: Optional[int] = 10,
        hidden: Optional[bool] = False
    ):
        """Displays top duelists ordered by ELO score."""
        safe_limit = max(1, min(limit or 10, 50))
        season_str = season or "Season 1"
        entries = await self.rating_service.get_leaderboard(limit=safe_limit, season_id=season_str)
        embed = build_leaderboard_embed(entries, season_id=season_str)
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))

    # -------------------------------------------------------------------------
    # Sub-Block 3.3: Rank Tiers & Division Guide Command (/rank_tiers)
    # -------------------------------------------------------------------------
    @app_commands.command(name="rank_tiers", description="View official ELO brackets, tier badges, and rank requirements")
    @app_commands.describe(hidden="Whether to display the tier guide ephemerally (Default: False)")
    async def rank_tiers_command(
        self,
        interaction: discord.Interaction,
        hidden: Optional[bool] = False
    ):
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
        await interaction.response.send_message(embed=embed, ephemeral=bool(hidden))


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Setup & Public Manifest)
# =============================================================================

async def setup(bot: commands.Bot):
    """Extension loader entrypoint."""
    await bot.add_cog(RankingCog(bot))


__all__ = [
    "RankingCog",
    "setup",
]
