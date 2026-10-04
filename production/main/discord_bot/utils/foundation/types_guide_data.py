# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.utils.foundation.types_guide_data
Description:
    Card Types, Subtypes, Attributes & 26 Monster Races Master Guide Metadata.
    Provides structured educational reference dictionaries for spell speeds,
    trap categories, monster summoning frames, all 26 official monster races,
    elemental attributes (with bitmasks and kanji), and Level vs Rank rules.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Any, Dict, List, Tuple

# =============================================================================
# BLOCK 3: BODY BLOCK (Card Anatomy & Reference Metadata Dictionaries)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Spell Classification & Speed Tiers
# -----------------------------------------------------------------------------
SPELL_CARD_TYPES: Dict[str, Dict[str, str]] = {
    "Normal Spell": {
        "icon": "None",
        "speed": "Spell Speed 1",
        "description": "Activated during your Main Phase on an open game state. Sent to the Graveyard immediately upon resolving."
    },
    "Continuous Spell": {
        "icon": "∞ (Infinity)",
        "speed": "Spell Speed 1",
        "description": "Remains face-up on the field in a Spell & Trap Zone after activation, providing ongoing or triggered effects."
    },
    "Equip Spell": {
        "icon": "+ (Crossed Swords)",
        "speed": "Spell Speed 1",
        "description": "Attaches to 1 face-up monster on field, modifying stats or granting effects. Destroyed if the monster leaves the field."
    },
    "Quick-Play Spell": {
        "icon": "⚡ (Lightning Bolt)",
        "speed": "Spell Speed 2",
        "description": "Can be activated from hand during any phase of your turn, or Set face-down to activate during the opponent's turn like a Trap."
    },
    "Field Spell": {
        "icon": "⨁ (Compass Rose)",
        "speed": "Spell Speed 1",
        "description": "Placed in the dedicated Field Spell Zone (does not take up a S/T Zone). Provides global or archetype-wide environment effects."
    },
    "Ritual Spell": {
        "icon": "🔥 (Flame)",
        "speed": "Spell Speed 1",
        "description": "Tributes monsters from hand or field to Special Summon a designated Ritual Monster from hand."
    }
}


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Trap Classification & Speed Tiers
# -----------------------------------------------------------------------------
TRAP_CARD_TYPES: Dict[str, Dict[str, str]] = {
    "Normal Trap": {
        "icon": "None",
        "speed": "Spell Speed 2",
        "description": "One-time reactive effect. Activated in response to an action or game state, resolves, and is sent to Graveyard."
    },
    "Continuous Trap": {
        "icon": "∞ (Infinity)",
        "speed": "Spell Speed 2",
        "description": "Remains face-up in the Spell & Trap Zone after activation, continuously altering game rules, floodgating, or triggering per turn."
    },
    "Counter Trap": {
        "icon": "⤶ (Counter Arrow)",
        "speed": "Spell Speed 3",
        "description": "The fastest cards in the game. Used specifically to negate summons, activations, or attacks. Only another Counter Trap can respond."
    }
}


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Monster Summoning Mechanics & Frames
# -----------------------------------------------------------------------------
MONSTER_CARD_FRAMES: Dict[str, str] = {
    "Normal Monster": "Yellow Frame • Has no card effects; features flavor text describing its lore and combat style.",
    "Effect Monster": "Orange Frame • The cornerstone of Yu-Gi-Oh!; possesses Ignition, Trigger, Continuous, or Quick effects.",
    "Ritual Monster": "Light Blue Frame • Main Deck monster; summoned via a Ritual Spell with required material Tributes.",
    "Pendulum Monster": "Half Monster / Half Spell Frame • Can be summoned as a monster or placed in Column 1/5 to set Pendulum Scales.",
    "Fusion Monster": "Violet Frame (Extra Deck) • Summoned by fusing materials together (e.g. Polymerization or contact fusion).",
    "Synchro Monster": "White Frame (Extra Deck) • Summoned by sending 1 Tuner + 1+ non-Tuners whose Levels exactly equal the Synchro's Level.",
    "Xyz Monster": "Black Frame (Extra Deck) • Possesses Ranks instead of Levels. Summoned by overlaying same-Level monsters as Xyz Materials.",
    "Link Monster": "Dark Blue Frame (Extra Deck) • Has Link Arrows and Link Rating instead of DEF. Cannot exist in Defense Position.",
    "Token Monster": "Grey Frame • Generated on field by card effects; ceases to exist if it leaves the field."
}

MONSTER_SUBTYPES: Dict[str, str] = {
    "Gemini": "Treated as a Normal Monster on the field and in the GY until Normal Summoned a second time on the field to become an Effect Monster (Cornerstone mechanic of Set 1's LeSpookie archetype!).",
    "Tuner": "Required material component for Synchro Summons. Can be Normal, Effect, or Pendulum.",
    "Flip": "Triggers its effect when flipped from face-down Defense Position to face-up.",
    "Union": "Can equip itself to another monster on field or unequip itself to Special Summon back to the field.",
    "Spirit": "Cannot be Special Summoned. Returns to the owner's hand during the End Phase of the turn it was summoned.",
    "Toon": "Archetypal subtype with direct attack mechanics and reliance on Toon World on the field."
}


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Official 26 Monster Types / Races
# -----------------------------------------------------------------------------
ALL_26_MONSTER_RACES: List[Tuple[str, str]] = [
    ("Dragon", "Legendary scaled beasts, cosmic wyrms, and cataclysmic powerhouses."),
    ("Spellcaster", "Mystics, sorcerers, alchemists, and wielders of arcane spellcraft."),
    ("Warrior", "Combat soldiers, knights, samurai, and masters of armed martial combat."),
    ("Beast-Warrior", "Humanoid beings fusing the strength of beasts with martial discipline."),
    ("Beast", "Wild animals, primal fauna, predators, and woodland spirits."),
    ("Winged Beast", "Avian predators, harpies, falcons, and airborne creatures."),
    ("Fiend", "Demons, shadow dwellers, archfiends, and dark netherworld entities."),
    ("Fairy", "Angels, celestial beings, holy heralds, and divine emissaries."),
    ("Zombie", "Undead ghouls, vampires, spectral spirits, and Graveyard recursors."),
    ("Machine", "Mechs, automatons, clockwork gear, robotic superweapons, and vehicles."),
    ("Aqua", "Water elementals, marine amphibians, oozes, and liquid entities."),
    ("Pyro", "Creatures of pure flame, magma, volcanics, and incinerating fire."),
    ("Rock", "Earthen golems, geological formations, fossils, and crystal entities."),
    ("Plant", "Botanical flora, carnivorous vines, sentient blossoms, and forest roots."),
    ("Insect", "Bugs, arachnids, mantises, and hive swarms."),
    ("Thunder", "Beings of raw lightning, voltage, storms, and electrostatic energy."),
    ("Dinosaur", "Prehistoric behemoths, apex carnivores, and primal giants."),
    ("Fish", "Aquatic swimmers, sharks, and abyssal swimmers."),
    ("Sea Serpent", "Leviathans, sea serpents, krakens, and colossal trench terrors."),
    ("Reptile", "Snakes, lizards, chameleons, and venomous cold-blooded beasts."),
    ("Psychic", "Beings of mental power, telekinesis, brainwaves, and cyber-kinetics."),
    ("Cyberse", "Digital lifeforms, network avatars, and AI constructs."),
    ("Wyrm", "Spiritual dragons, ethereal serpents, and celestial energy beings."),
    ("Illusion", "Phantasms and mirages that neither destroy nor can be destroyed in battle."),
    ("Divine-Beast", "Supreme primordial god-entities (The Egyptian Gods & The Great Kasutamaiza)."),
    ("Creator-God", "The transcendent divine architect (Holactie the Creator of Light).")
]


# -----------------------------------------------------------------------------
# Sub-Block 3.5: The 7 Elemental Card Attributes
# -----------------------------------------------------------------------------
CARD_ATTRIBUTES: Dict[str, Dict[str, Any]] = {
    "LIGHT": {
        "kanji": "光",
        "symbol": "☀️",
        "bitmask": 0x10,
        "color": 0xF1C40F,
        "description": "Radiance, celestial messengers, purity, and illumination. Central to the Kasutamaiza creation pantheon."
    },
    "DARK": {
        "kanji": "闇",
        "symbol": "🌑",
        "bitmask": 0x20,
        "color": 0x8E44AD,
        "description": "Shadow arts, netherworld entities, occult sorcerers, fiends, necromancy, and void manipulation."
    },
    "EARTH": {
        "kanji": "地",
        "symbol": "⛰️",
        "bitmask": 0x01,
        "color": 0xB9770E,
        "description": "Terrestrial bedrock, steadfast warriors, mineral golems, and primal physical force."
    },
    "WATER": {
        "kanji": "水",
        "symbol": "🌊",
        "bitmask": 0x02,
        "color": 0x2980B9,
        "description": "Tidal currents, glacial ice, aquatic fauna, oceanic abysses, and fluid combat adaptability."
    },
    "FIRE": {
        "kanji": "炎",
        "symbol": "🔥",
        "bitmask": 0x04,
        "color": 0xE74C3C,
        "description": "Combustion, molten magma, volcanic beasts, explosive burnout, and fiery passion."
    },
    "WIND": {
        "kanji": "風",
        "symbol": "🌪️",
        "bitmask": 0x08,
        "color": 0x27AE60,
        "description": "Atmospheric gales, avian predators, cyclone storms, and rapid tempo acceleration."
    },
    "DIVINE": {
        "kanji": "神",
        "symbol": "✨",
        "bitmask": 0x40,
        "color": 0xD4AC0D,
        "description": "Transcendent primordial god-entities (The Egyptian Gods, Holactie, and The Great Kasutamaiza)."
    }
}


# -----------------------------------------------------------------------------
# Sub-Block 3.6: Level, Rank, Link & Pendulum Math Guides
# -----------------------------------------------------------------------------
LEVELS_AND_RANKS_DATA: Dict[str, Any] = {
    "levels": {
        "title": "⭐ Monster Levels (1 – 12)",
        "stars_icon": "⭐ (Yellow/Orange Stars)",
        "reading_order": "Top-Right, reading right-to-left",
        "applies_to": "Main Deck monsters (Normal, Effect, Ritual, Pendulum) and Extra Deck (Fusion, Synchro)",
        "tribute_rules": [
            "• **Level 1 to 4 (Low-Level):** Normal Summoned or Set directly with **0 Tributes**.",
            "• **Level 5 to 6 (Mid-Level):** Requires **1 Tribute** (sending 1 monster from your field to the GY).",
            "• **Level 7 to 9 (High-Level):** Requires **2 Tributes** (sending 2 monsters from your field to the GY).",
            "• **Level 10 to 12 (God-Tier):** Standard **2 Tributes**, unless card text requires 3 Tributes (e.g. *The Great Kasutamaiza*, Egyptian Gods)."
        ],
        "summon_math": [
            "• **Synchro Summoning:** Tuner Level + 1+ Non-Tuner Levels must exactly equal the Synchro Monster's Level.",
            "• **Ritual Summoning:** Tributes must have total Levels equal to or exceeding the Ritual Monster's Level."
        ]
    },
    "ranks": {
        "title": "⯪ Monster Ranks (1 – 13)",
        "stars_icon": "⯪ (Yellow Stars in Black Orbs)",
        "reading_order": "Top-Left, reading left-to-right",
        "applies_to": "Exclusively Xyz Monsters (Black Frame)",
        "golden_rule": "⚠️ **RANKS ARE NOT LEVELS!** An Xyz monster has NO Level (Level 0 / undefined).",
        "consequences": [
            "• Cannot be used as material for Synchro, Ritual, or Tribute Summons that demand a Level.",
            "• Completely unaffected by Level-modifying effects (e.g. *Gravity Bind*, *Level Limit - Area B*)."
        ],
        "xyz_mechanics": [
            "• **Xyz Summoning:** Overlay 2 or more monsters with the *exact same Level* matching the Xyz Monster's Rank.",
            "• **Xyz Materials:** Stacked underneath the card; they do not occupy monster zones and do not count as cards on field.",
            "• **Detaching:** Sent to the GY as costs to activate devastating Xyz effects."
        ]
    },
    "link_ratings": {
        "title": "🔗 Link Ratings & Link Arrows",
        "icon": "HEXAGON & ARROWS (Dark Blue Frame)",
        "stats": "No Level, No Rank, and **NO DEF** (cannot exist in Defense Position)",
        "link_rating": "The number in the bottom right (Link-1 to Link-6+) dictates the exact material count required.",
        "link_arrows": "Red directional arrows pointing to adjacent zones, unlocking Extra Monster Zones and Co-Linking."
    },
    "pendulum_scales": {
        "title": "⚖️ Pendulum Scales (0 – 13)",
        "icon": "💎 Blue (Left) & Red (Right) Scales",
        "placement": "Placed in the leftmost (Column 1) and rightmost (Column 5) Spell & Trap Zones.",
        "pendulum_summon": "Once per turn during Main Phase, Special Summon any number of monsters from hand (and face-up from Extra Deck to EMZ/Link zones) whose Levels fall strictly **between** the two scales (exclusive: e.g. Scales 1 and 8 summon Levels 2 through 7)."
    }
}


# -----------------------------------------------------------------------------
# Sub-Block 3.7: Spell Speeds & Chain Mechanics Guides
# -----------------------------------------------------------------------------
SPELL_SPEEDS_DATA: Dict[str, Dict[str, str]] = {
    "Spell Speed 1": {
        "speed": "Spell Speed 1 (Slow)",
        "cards": "Normal Spells, Equip Spells, Continuous Spells, Field Spells, Ritual Spells, Monster Ignition/Trigger Effects",
        "chain_rule": "Cannot be activated in response to another card or effect (cannot start a chain higher than Chain Link 1, unless simultaneous trigger effects form a chain via SEGOC).",
        "timing": "Only during your Main Phase in an open game state (except Trigger Effects which activate when their conditions are met)."
    },
    "Spell Speed 2": {
        "speed": "Spell Speed 2 (Fast)",
        "cards": "Quick-Play Spells, Normal Traps, Continuous Traps, Monster Quick Effects ('(Quick Effect)' or 'during either player's turn')",
        "chain_rule": "Can respond to Spell Speed 1 or Spell Speed 2 effects. Can form Chain Link 2 or higher.",
        "timing": "During either player's turn in response to an action or during any phase (Quick-Play Spells must be Set for 1 turn to activate on opponent's turn)."
    },
    "Spell Speed 3": {
        "speed": "Spell Speed 3 (Fastest)",
        "cards": "Counter Traps (identified by the curved counter arrow icon ⤶)",
        "chain_rule": "Can respond to Spell Speed 1, 2, or 3. ONLY another Spell Speed 3 effect (Counter Trap) can respond to a Spell Speed 3 effect!",
        "timing": "Activated directly in response to card activations, summons, or attacks to negate and destroy."
    },
    "Chain Resolution": {
        "speed": "LIFO (Last In, First Out)",
        "cards": "Chain Links (CL1, CL2, CL3...)",
        "chain_rule": "Chains always resolve in reverse order: the last card activated (highest Chain Link) resolves first, working backwards to Chain Link 1. No new cards can be activated while a chain is resolving.",
        "timing": "Resolves once both players pass priority without adding more chain links."
    }
}


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest)
# =============================================================================

__all__ = [
    "SPELL_CARD_TYPES",
    "TRAP_CARD_TYPES",
    "MONSTER_CARD_FRAMES",
    "MONSTER_SUBTYPES",
    "ALL_26_MONSTER_RACES",
    "CARD_ATTRIBUTES",
    "LEVELS_AND_RANKS_DATA",
    "SPELL_SPEEDS_DATA",
]

