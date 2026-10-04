# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.foundation.duel_math
Description:
    Tribute Threshold & Battle Damage Math Calculations.
    Simulates official Yu-Gi-Oh! Master Rule (MR5) battle damage calculation,
    destruction rules, piercing damage, and tribute summon level requirements.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, Optional

# =============================================================================
# BLOCK 3: BODY BLOCK (Tribute & Combat Calculations)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Tribute Requirements & Normal Summon Rules
# -----------------------------------------------------------------------------

def get_tribute_requirement(level: Optional[int]) -> int:
    """
    Returns the minimum number of field tributes required for a standard Normal/Tribute Summon.
    - Level 1-4: 0 tributes
    - Level 5-6: 1 tribute
    - Level 7+: 2 tributes
    - None / <=0: 0 tributes
    """
    if not level or level <= 4:
        return 0
    if level in (5, 6):
        return 1
    return 2


def is_tribute_summon(level: Optional[int]) -> bool:
    """
    Returns True if summoning a monster of this Level requires 1 or more Tributes.
    """
    return get_tribute_requirement(level) > 0


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Battle Damage Calculation & Position Comparison
# -----------------------------------------------------------------------------

def calculate_battle_damage(
    attacker: Dict[str, Any],
    defender: Optional[Dict[str, Any]],
    is_direct: bool = False
) -> Dict[str, Any]:
    """
    Simulates complete official Yu-Gi-Oh! battle damage calculation and destruction rules.
    - Direct Attack: Defender takes damage equal to attacker's ATK.
    - Attack Position vs Attack Position: Lower ATK monster destroyed; controller takes difference.
    - Attack Position vs Defense Position: Higher ATK destroys defender (no damage); lower ATK attacker takes difference (attacker not destroyed).
    """
    atk_val = attacker.get("atk", 0)
    atk_name = attacker.get("name", "Attacking Monster")

    if is_direct or defender is None:
        return {
            "is_direct": True,
            "damage": atk_val,
            "damaged_side": "defender",
            "attacker_destroyed": False,
            "defender_destroyed": False,
            "summary": f"⚔️ **{atk_name}** attacks directly for **{atk_val}** battle damage!"
        }

    def_name = defender.get("name", "Defending Monster")
    def_pos = defender.get("position", "ATK").upper()
    def_atk = defender.get("atk", 0)
    def_def = defender.get("def", 0)

    # 1. Defender is in Attack Position: Compare ATK vs ATK
    if def_pos == "ATK":
        if atk_val > def_atk:
            diff = atk_val - def_atk
            return {
                "is_direct": False,
                "damage": diff,
                "damaged_side": "defender",
                "attacker_destroyed": False,
                "defender_destroyed": True,
                "summary": f"💥 **{atk_name}** ({atk_val} ATK) destroys **{def_name}** ({def_atk} ATK)! Opponent takes **{diff}** battle damage."
            }
        elif atk_val < def_atk:
            diff = def_atk - atk_val
            return {
                "is_direct": False,
                "damage": diff,
                "damaged_side": "attacker",
                "attacker_destroyed": True,
                "defender_destroyed": False,
                "summary": f"🛡️ **{atk_name}** ({atk_val} ATK) crashes into **{def_name}** ({def_atk} ATK) and is destroyed! You take **{diff}** battle damage."
            }
        else:
            return {
                "is_direct": False,
                "damage": 0,
                "damaged_side": "neither",
                "attacker_destroyed": True,
                "defender_destroyed": True,
                "summary": f"💥 Both **{atk_name}** and **{def_name}** have equal ATK ({atk_val})! Both monsters are destroyed; 0 damage taken."
            }

    # 2. Defender is in Defense Position (Face-up or Face-down Set): Compare ATK vs DEF
    else:
        was_set = (def_pos == "SET")
        flip_txt = " (flipped face-up)" if was_set else ""
        if atk_val > def_def:
            return {
                "is_direct": False,
                "damage": 0,
                "damaged_side": "neither",
                "attacker_destroyed": False,
                "defender_destroyed": True,
                "summary": f"🛡️ **{atk_name}** ({atk_val} ATK) destroys defending **{def_name}**{flip_txt} ({def_def} DEF)! No battle damage inflicted."
            }
        elif atk_val < def_def:
            diff = def_def - atk_val
            return {
                "is_direct": False,
                "damage": diff,
                "damaged_side": "attacker",
                "attacker_destroyed": False,
                "defender_destroyed": False,
                "summary": f"🧱 **{atk_name}** ({atk_val} ATK) fails to pierce **{def_name}**{flip_txt} ({def_def} DEF)! Neither monster is destroyed; attacker takes **{diff}** battle damage."
            }
        else:
            return {
                "is_direct": False,
                "damage": 0,
                "damaged_side": "neither",
                "attacker_destroyed": False,
                "defender_destroyed": False,
                "summary": f"🛡️ **{atk_name}** ({atk_val} ATK) matches **{def_name}**{flip_txt} ({def_def} DEF). Neither monster is destroyed; 0 damage taken."
            }


def calculate_piercing_damage(atk_val: int, def_val: int) -> int:
    """
    Calculates piercing battle damage inflicted to the opponent when attacking
    a Defense Position monster with a piercing effect.
    Returns max(0, atk_val - def_val).
    """
    return max(0, atk_val - def_val)


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Numeric Range & Game Rule Invariant Validators
# -----------------------------------------------------------------------------

def is_valid_level(val: Any) -> bool:
    """Checks whether a value is a legal Yu-Gi-Oh! Level (1-12)."""
    return isinstance(val, int) and 1 <= val <= 12


def is_valid_rank(val: Any) -> bool:
    """Checks whether a value is a legal Yu-Gi-Oh! Xyz Rank (1-13)."""
    return isinstance(val, int) and 1 <= val <= 13


def is_valid_link_rating(val: Any) -> bool:
    """Checks whether a value is a legal Yu-Gi-Oh! Link Rating (1-6)."""
    return isinstance(val, int) and 1 <= val <= 6


def is_valid_scale(val: Any) -> bool:
    """Checks whether a value is a legal Yu-Gi-Oh! Pendulum Scale (0-13)."""
    return isinstance(val, int) and 0 <= val <= 13


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    # Tribute Math
    "get_tribute_requirement",
    "is_tribute_summon",
    # Combat Math
    "calculate_battle_damage",
    "calculate_piercing_damage",
    # Range Invariants
    "is_valid_level",
    "is_valid_rank",
    "is_valid_link_rating",
    "is_valid_scale",
]
