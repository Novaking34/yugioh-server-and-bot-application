# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.foundation.math
Description:
    Bottom-Up Foundation: Deck mathematics, hypergeometric probability
    distributions, fair Fisher-Yates PRNG shuffle, and hand bounds.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import math
import random
from typing import List, Tuple, Optional, Any

from .constants import (
    MIN_HAND_SIZE,
    DEFAULT_END_PHASE_HAND_LIMIT,
    HIEROGLYPH_HAND_LIMIT,
    NO_HAND_LIMIT,
    MAX_HAND_SIZE,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Probability, Shuffle & Hand Logic Engine)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Deckout & Hand Bounds Verification
# -----------------------------------------------------------------------------

def is_deckout_condition(remaining_deck_count: int, cards_to_draw: int = 1, required_draw: Optional[int] = None) -> bool:
    """
    Evaluates whether an attempted draw results in a Master Rule Deck Out loss.
    Accepts cards_to_draw or required_draw.
    """
    draw_req = cards_to_draw if required_draw is None else required_draw
    return remaining_deck_count < draw_req


def validate_hand_size(
    current_hand_size: int,
    is_end_phase: bool = False,
    hand_limit: Optional[int] = DEFAULT_END_PHASE_HAND_LIMIT
) -> Tuple[bool, str]:
    """
    Validates hand size against Master Rule limits:
    - current_hand_size cannot be negative.
    - During active play, any hand size >= 0 is legal.
    - During End Phase, checks against hand_limit (default 6), calculating discard count if exceeded.
    """
    if current_hand_size < MIN_HAND_SIZE:
        return False, f"Hand size cannot be negative ({current_hand_size} < {MIN_HAND_SIZE})."

    if not is_end_phase:
        return True, f"Hand size {current_hand_size} is legal during active play."

    if hand_limit is NO_HAND_LIMIT:
        return True, "No hand limit active (Infinite Cards rule)."

    if current_hand_size > hand_limit:
        excess = current_hand_size - hand_limit
        return True, f"End Phase hand size ({current_hand_size}) requires player to discard {excess} card(s) down to limit ({hand_limit})."

    return True, f"End Phase hand size ({current_hand_size}) is within End Phase limit of {hand_limit}."


def check_end_phase_discard_requirement(
    current_hand_size: int,
    hand_limit: Optional[int] = DEFAULT_END_PHASE_HAND_LIMIT
) -> int:
    """Calculates the exact number of cards a player must discard during the End Phase."""
    if hand_limit is NO_HAND_LIMIT:
        return 0
    return max(0, current_hand_size - hand_limit)


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Hypergeometric Probability Distributions
# -----------------------------------------------------------------------------

def _comb(n: int, k: int) -> int:
    """Helper for combinations n choose k."""
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def calculate_draw_prob(
    deck_size: int,
    target_count: int,
    draw_count: int = 5,
    min_hits: int = 1
) -> float:
    """
    Calculates hypergeometric probability of drawing at least `min_hits` copies
    of a target card in `draw_count` cards drawn from `deck_size`.
    """
    if deck_size <= 0 or target_count <= 0 or draw_count <= 0:
        return 0.0
    if target_count > deck_size or draw_count > deck_size:
        return 0.0

    total_ways = _comb(deck_size, draw_count)
    if total_ways == 0:
        return 0.0

    prob_less_than_min = 0.0
    for k in range(0, min_hits):
        ways_k = _comb(target_count, k) * _comb(deck_size - target_count, draw_count - k)
        prob_less_than_min += ways_k / total_ways

    prob_at_least_min = max(0.0, 1.0 - prob_less_than_min)
    return round(prob_at_least_min * 100.0, 2)


def calculate_opening_hand_prob(
    deck_size: int,
    target_count: int,
    hand_size: int = 5,
    min_hits: int = 1
) -> float:
    """Calculates opening hand probability (Turn 1: 5 cards, or Turn 2: 6 cards)."""
    return calculate_draw_prob(deck_size, target_count, hand_size, min_hits)


def calculate_combo_prob(
    deck_size: int,
    target_a_count: int,
    target_b_count: int,
    draw_count: int = 5
) -> float:
    """
    Calculates probability of drawing at least 1 copy of Card A AND at least 1 copy of Card B
    in an opening hand using the bivariate hypergeometric distribution.
    """
    if deck_size <= 0 or draw_count <= 0:
        return 0.0
    if (target_a_count + target_b_count) > deck_size or draw_count > deck_size:
        return 0.0

    total_ways = _comb(deck_size, draw_count)
    if total_ways == 0:
        return 0.0

    ways_with_both = 0
    other_cards = deck_size - target_a_count - target_b_count

    for a in range(1, min(target_a_count, draw_count) + 1):
        for b in range(1, min(target_b_count, draw_count - a) + 1):
            c = draw_count - a - b
            if 0 <= c <= other_cards:
                ways = _comb(target_a_count, a) * _comb(target_b_count, b) * _comb(other_cards, c)
                ways_with_both += ways

    prob = ways_with_both / total_ways
    return round(prob * 100.0, 2)


# -----------------------------------------------------------------------------
# Sub-Block 3.3: PRNG Fair Shuffle & Draw Simulations
# -----------------------------------------------------------------------------

def fair_shuffle(cards: List[Any], seed: Optional[int] = None) -> List[Any]:
    """
    Executes a cryptographically fair / PRNG reproducible Fisher-Yates shuffle.
    Does not mutate the input list.
    """
    shuffled = list(cards)
    rng = random.Random(seed) if seed is not None else random.Random()
    for i in range(len(shuffled) - 1, 0, -1):
        j = rng.randint(0, i)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def simulate_fair_draw(
    deck: List[Any],
    draw_count: int = 5,
    seed: Optional[int] = None
) -> Tuple[List[Any], List[Any], bool]:
    """
    Simulates a fair shuffle and draw.
    Returns: (drawn_cards, remaining_deck, is_deckout)
    """
    shuffled = fair_shuffle(deck, seed=seed)
    is_deckout = len(shuffled) < draw_count
    drawn = shuffled[:draw_count]
    remaining = shuffled[draw_count:]
    return drawn, remaining, is_deckout


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "is_deckout_condition",
    "validate_hand_size",
    "check_end_phase_discard_requirement",
    "calculate_draw_prob",
    "calculate_opening_hand_prob",
    "calculate_combo_prob",
    "fair_shuffle",
    "simulate_fair_draw",
]

