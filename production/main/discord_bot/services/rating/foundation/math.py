# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.rating.foundation.math
Description:
    Pure Mathematical Functions for FIDE ELO Calculations & Tier Resolution.
    Calculates expected match win probabilities, K-factor dynamics, Elo shifts,
    win rates, and division tier badge mappings.

Architectural Classification:
    Layer 0 (L0) - Foundation Layer
    Subsystem: Competitive Rating & ELO Analytics
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import math
from typing import Tuple

from .constants import (
    ESTABLISHED_K_FACTOR,
    MIN_ELO_FLOOR,
    PROVISIONAL_K_FACTOR,
    PROVISIONAL_MATCHES_THRESHOLD,
    TIER_BRACKETS,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Mathematical Algorithms)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Tier Badge & Division Resolution
# -----------------------------------------------------------------------------

def resolve_tier_info(elo: int) -> Tuple[str, str, int]:
    """
    Returns (tier_name, badge_icon, embed_color) for a given Elo rating.

    Args:
        elo: Numerical duelist rating.

    Returns:
        Tuple containing tier name, emoji icon badge, and hexadecimal color.
    """
    for min_elo, name, badge, color in TIER_BRACKETS:
        if elo >= min_elo:
            return name, badge, color
    return "Novice Duelist", "🔰", 0x6B7280


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Logistic ELO Probability & Rating Adjustments
# -----------------------------------------------------------------------------

def calculate_expected_score(p1_elo: int, p2_elo: int) -> Tuple[float, float]:
    """
    Calculates the expected victory probability for two duelists using the
    logistic curve: E_A = 1 / (1 + 10^((R_B - R_A) / 400)).

    Args:
        p1_elo: Player 1 Elo rating.
        p2_elo: Player 2 Elo rating.

    Returns:
        Tuple of (expected_p1_score, expected_p2_score).
    """
    exponent = (p2_elo - p1_elo) / 400.0
    expected_p1 = 1.0 / (1.0 + (10.0 ** exponent))
    expected_p2 = 1.0 - expected_p1
    return expected_p1, expected_p2


def compute_elo_change(
    p1_elo: int,
    p2_elo: int,
    p1_score: float,
    p1_matches: int = 15,
    p2_matches: int = 15
) -> Tuple[int, int]:
    """
    Calculates updated Elo ratings using standard FIDE logistic Elo equations.

    Args:
        p1_elo: Current rating of Player 1.
        p2_elo: Current rating of Player 2.
        p1_score: Match outcome score for P1 (1.0 = win, 0.5 = draw, 0.0 = loss).
        p1_matches: Total competitive matches played by Player 1.
        p2_matches: Total competitive matches played by Player 2.

    Returns:
        Tuple of (new_p1_elo, new_p2_elo), respecting the minimum Elo floor.
    """
    k1 = PROVISIONAL_K_FACTOR if p1_matches < PROVISIONAL_MATCHES_THRESHOLD else ESTABLISHED_K_FACTOR
    k2 = PROVISIONAL_K_FACTOR if p2_matches < PROVISIONAL_MATCHES_THRESHOLD else ESTABLISHED_K_FACTOR

    expected_p1, expected_p2 = calculate_expected_score(p1_elo, p2_elo)
    p2_score = 1.0 - p1_score

    new_p1 = max(MIN_ELO_FLOOR, round(p1_elo + k1 * (p1_score - expected_p1)))
    new_p2 = max(MIN_ELO_FLOOR, round(p2_elo + k2 * (p2_score - expected_p2)))

    return new_p1, new_p2


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Win Rate Calculation
# -----------------------------------------------------------------------------

def calculate_win_rate(wins: int, losses: int, draws: int) -> float:
    """
    Computes percentage win rate rounded to 1 decimal place.

    Args:
        wins: Total victories.
        losses: Total defeats.
        draws: Total stalemates.

    Returns:
        Float win percentage (0.0 to 100.0).
    """
    total = wins + losses + draws
    if total <= 0:
        return 0.0
    return round((wins / total) * 100.0, 1)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "resolve_tier_info",
    "calculate_expected_score",
    "compute_elo_change",
    "calculate_win_rate",
]
