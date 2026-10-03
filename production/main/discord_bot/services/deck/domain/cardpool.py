# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.domain.cardpool
Description:
    Section 3.1: Live Cardpool Telemetry Subsystem.
    Queries the live SQLite custom card database for cardpool dimensions,
    rarity distributions, mechanics breakdowns, and zone/PSCT ecosystems.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import aiosqlite
from typing import List, Dict, Any, Optional

from ..foundation.constants import STANDARD_MIN_MAIN_DECK
from ..foundation.classifier import (
    is_extra_deck_card,
    is_extra_deck_pendulum,
    is_main_deck_pendulum,
    is_ritual_monster,
    get_tribute_cost,
    is_field_spell,
    has_field_awareness,
    has_graveyard_interaction,
    has_banishment_interaction,
    has_extra_monster_zone_interaction,
    has_pendulum_zone_interaction,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Cardpool Engine & Telemetry Aggregation)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Live Cardpool Database Queries
# -----------------------------------------------------------------------------

async def query_cardpool_cards(
    db_path: str,
    archetype_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Queries the live custom_cards database for all cards in the cardpool."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        if archetype_filter:
            cur = await db.execute("""
                SELECT id, name, set_number, card_type, card_subtype, attribute, 
                       monster_type, level_or_rank_or_link AS level, scale, 
                       atk, def, link_arrows, effect_text, pendulum_effect, 
                       rarity, archetype, banlist_status
                FROM custom_cards
                WHERE archetype LIKE ? OR name LIKE ?
                ORDER BY id ASC
            """, (f"%{archetype_filter}%", f"%{archetype_filter}%"))
        else:
            cur = await db.execute("""
                SELECT id, name, set_number, card_type, card_subtype, attribute, 
                       monster_type, level_or_rank_or_link AS level, scale, 
                       atk, def, link_arrows, effect_text, pendulum_effect, 
                       rarity, archetype, banlist_status
                FROM custom_cards
                ORDER BY id ASC
            """)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Cardpool Dimensions, Mechanics & Zone Telemetry Calculation
# -----------------------------------------------------------------------------

async def calculate_cardpool_stats(
    db_path: str,
    archetype_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Queries the database dynamically for live cardpool dimensions and telemetry:
    - Master Rule 40-card singleton construction viability
    - Official booster rarity distribution (Secret, Ultra, Super, Rare, Common)
    - Mechanics breakdown (Normal, Effect, Ritual, Tribute, Pendulum, Extra Deck)
    - Zone & PSCT ecosystem (Field Providers, Beneficiaries, GY, Banishment, EMZ, PZ)
    """
    cards = await query_cardpool_cards(db_path, archetype_filter=archetype_filter)
    total = len(cards)

    extra_cards = [c for c in cards if is_extra_deck_card(c)]
    main_monsters = [c for c in cards if (c.get("card_type") or "").lower() == "monster" and not is_extra_deck_card(c)]
    spells = [c for c in cards if (c.get("card_type") or "").lower() == "spell"]
    traps = [c for c in cards if (c.get("card_type") or "").lower() == "trap"]

    main_pool_size = len(main_monsters) + len(spells) + len(traps)
    has_legal_40_singles = main_pool_size >= STANDARD_MIN_MAIN_DECK

    # 1. Rarity Telemetry
    rarity_counts: Dict[str, int] = {}
    for c in cards:
        r = c.get("rarity") or "Common"
        rarity_counts[r] = rarity_counts.get(r, 0) + 1

    rarity_breakdown = {
        "secret_rares": rarity_counts.get("Secret Rare", 0),
        "ultra_rares": rarity_counts.get("Ultra Rare", 0),
        "super_rares": rarity_counts.get("Super Rare", 0),
        "rares": rarity_counts.get("Rare", 0),
        "commons": rarity_counts.get("Common", 0),
        "by_rarity": rarity_counts
    }

    # 2. Mechanics Breakdown
    normal_monsters = [c for c in main_monsters if "normal" in (c.get("card_subtype") or "").lower()]
    effect_monsters = [c for c in main_monsters if "effect" in (c.get("card_subtype") or "").lower() and not is_ritual_monster(c)]
    ritual_monsters = [c for c in main_monsters if is_ritual_monster(c)]
    tribute_1 = [c for c in main_monsters if get_tribute_cost(c) == 1]
    tribute_2 = [c for c in main_monsters if get_tribute_cost(c) == 2]

    main_pendulums = [c for c in cards if is_main_deck_pendulum(c)]
    extra_pendulums = [c for c in cards if is_extra_deck_pendulum(c)]

    fusions = [c for c in extra_cards if "fusion" in (c.get("card_subtype") or "").lower()]
    synchros = [c for c in extra_cards if "synchro" in (c.get("card_subtype") or "").lower()]
    xyz_monsters = [c for c in extra_cards if "xyz" in (c.get("card_subtype") or "").lower()]
    links = [c for c in extra_cards if "link" in (c.get("card_subtype") or "").lower()]

    spells_normal = [c for c in spells if "normal" in (c.get("card_subtype") or "").lower() or (c.get("card_subtype") or "") == ""]
    spells_quick = [c for c in spells if "quick" in (c.get("card_subtype") or "").lower()]
    spells_cont = [c for c in spells if "continuous" in (c.get("card_subtype") or "").lower()]
    spells_field = [c for c in spells if is_field_spell(c)]
    spells_equip = [c for c in spells if "equip" in (c.get("card_subtype") or "").lower()]
    spells_ritual = [c for c in spells if "ritual" in (c.get("card_subtype") or "").lower()]

    traps_normal = [c for c in traps if "normal" in (c.get("card_subtype") or "").lower() or (c.get("card_subtype") or "") == ""]
    traps_cont = [c for c in traps if "continuous" in (c.get("card_subtype") or "").lower()]
    traps_counter = [c for c in traps if "counter" in (c.get("card_subtype") or "").lower()]

    mechanics_breakdown = {
        "normal_monsters": len(normal_monsters),
        "effect_monsters": len(effect_monsters),
        "ritual_monsters": len(ritual_monsters),
        "tribute_monsters": {
            "level_5_6": len(tribute_1),
            "level_7_plus": len(tribute_2),
            "total": len(tribute_1) + len(tribute_2)
        },
        "pendulum_monsters": {
            "main_deck": len(main_pendulums),
            "extra_deck": len(extra_pendulums),
            "total": len(main_pendulums) + len(extra_pendulums)
        },
        "extra_deck": {
            "fusions": len(fusions),
            "synchros": len(synchros),
            "xyz": len(xyz_monsters),
            "links": len(links),
            "total": len(extra_cards)
        },
        "spells": {
            "normal": len(spells_normal),
            "quick_play": len(spells_quick),
            "continuous": len(spells_cont),
            "field": len(spells_field),
            "equip": len(spells_equip),
            "ritual": len(spells_ritual)
        },
        "traps": {
            "normal": len(traps_normal),
            "continuous": len(traps_cont),
            "counter": len(traps_counter)
        }
    }

    # 3. Zone & PSCT Ecosystem
    field_providers = [c for c in cards if is_field_spell(c)]
    field_beneficiaries = [c for c in cards if has_field_awareness(c) and not is_field_spell(c)]
    gy_cards = [c for c in cards if has_graveyard_interaction(c)]
    banish_cards = [c for c in cards if has_banishment_interaction(c)]
    emz_cards = [c for c in cards if has_extra_monster_zone_interaction(c)]
    pz_cards = [c for c in cards if has_pendulum_zone_interaction(c)]

    zone_breakdown = {
        "field_providers": len(field_providers),
        "field_beneficiaries": len(field_beneficiaries),
        "total_field_engine": len(field_providers) + len(field_beneficiaries),
        "graveyard_interactors": len(gy_cards),
        "banishment_interactors": len(banish_cards),
        "extra_monster_zone_interactors": len(emz_cards),
        "pendulum_zone_interactors": len(pz_cards)
    }

    # 4. Archetype Breakdown
    archetype_counts: Dict[str, int] = {}
    for c in cards:
        arch = c.get("archetype") or "Generic"
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    return {
        "total_cards": total,
        "main_deck_pool": main_pool_size,
        "main_monsters": len(main_monsters),
        "spells": len(spells),
        "traps": len(traps),
        "extra_monsters": len(extra_cards),
        "field_spells": len(field_providers),
        "has_legal_40_singles": has_legal_40_singles,
        "rarity_breakdown": rarity_breakdown,
        "mechanics_breakdown": mechanics_breakdown,
        "zone_awareness": zone_breakdown,
        "archetype_breakdown": archetype_counts,
    }


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Telemetry Formatting & Human-Readable Reporting
# -----------------------------------------------------------------------------

def format_cardpool_summary(stats: Dict[str, Any]) -> str:
    """Formats cardpool telemetry statistics into a structured, human-readable report."""
    total = stats.get("total_cards", 0)
    main_pool = stats.get("main_deck_pool", 0)
    legal_status = "✅ Legal (>= 40 singles)" if stats.get("has_legal_40_singles") else "❌ Insufficient (< 40 singles)"
    
    rarities = stats.get("rarity_breakdown", {})
    mech = stats.get("mechanics_breakdown", {})
    zones = stats.get("zone_awareness", {})
    extra = mech.get("extra_deck", {})
    
    lines = [
        f"**Cardpool Telemetry Report**",
        f"• **Dimensions**: {total} Total Cards | Main Pool: {main_pool} cards ({legal_status})",
        f"• **Card Breakdown**: {stats.get('main_monsters', 0)} Main Monsters | {stats.get('spells', 0)} Spells | {stats.get('traps', 0)} Traps | {stats.get('extra_monsters', 0)} Extra Deck",
        f"• **Extra Deck**: {extra.get('fusions', 0)} Fusion | {extra.get('synchros', 0)} Synchro | {extra.get('xyz', 0)} Xyz | {extra.get('links', 0)} Link",
        f"• **Rarities**: {rarities.get('secret_rares', 0)} Secret | {rarities.get('ultra_rares', 0)} Ultra | {rarities.get('super_rares', 0)} Super | {rarities.get('rares', 0)} Rare | {rarities.get('commons', 0)} Common",
        f"• **Zone Engine**: {zones.get('field_providers', 0)} Field Spells ({zones.get('field_beneficiaries', 0)} Beneficiaries) | {zones.get('graveyard_interactors', 0)} GY | {zones.get('banishment_interactors', 0)} Banish"
    ]
    return "\n".join(lines)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "query_cardpool_cards",
    "calculate_cardpool_stats",
    "format_cardpool_summary",
]

