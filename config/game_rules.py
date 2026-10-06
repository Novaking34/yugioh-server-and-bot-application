# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.game_rules
Description:
    Authoritative Yu-Gi-Oh! Game Rules, ocgcore Engine Bitmasks & Tournament Limits.
    Centralizes all domain constants across the 3 applications (Simulator, Bot, Web):
    - Card Types, Subtypes, and Speeds (datas.type bitmask)
    - Attributes (datas.attribute bitmask)
    - Monster Races / Species (datas.race bitmask)
    - Link Arrows (datas.def compass bitmask & octal values)
    - Official Master Rule 5 Deck Limits (Main 40-60, Extra 15, Side 15, Copy 3)
    - Hand Size, Turn Order, and Field Zone Identifiers
    - Official Rarities & Color Profiles
    - Custom Passcode Allocations (50000000 - 99999999)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Type Declarations)
# =============================================================================

from typing import Dict, List, Optional, Set, Any

# =============================================================================
# BLOCK 3: BODY BLOCK (Authoritative Game Rules & Bitmasks)
# =============================================================================

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.1: Passcode Partitions & Security Boundaries
# -----------------------------------------------------------------------------
CUSTOM_PASSCODE_MIN: int = 50000000
CUSTOM_PASSCODE_MAX: int = 99999999
OFFICIAL_PASSCODE_MAX: int = 49999999

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.2: Card Types & Mechanics (datas.type bitmask)
# -----------------------------------------------------------------------------
TYPE_MONSTER: int        = 0x1          # 1: General Monster card
TYPE_SPELL: int          = 0x2          # 2: Spell / Magic card
TYPE_TRAP: int           = 0x4          # 4: Trap card
TYPE_NORMAL: int         = 0x10         # 16: Normal Monster or Normal Spell/Trap
TYPE_EFFECT: int         = 0x20         # 32: Effect Monster
TYPE_FUSION: int         = 0x40         # 64: Fusion Monster (Extra Deck)
TYPE_RITUAL: int         = 0x80         # 128: Ritual Monster or Ritual Spell
TYPE_TRAPMONSTER: int    = 0x100        # 256: Trap card treating itself as a monster
TYPE_SPIRIT: int         = 0x200        # 512: Spirit Monster
TYPE_UNION: int          = 0x400        # 1024: Union Monster
TYPE_DUAL: int           = 0x800        # 2048: Gemini / Dual Monster
TYPE_TUNER: int          = 0x1000       # 4096: Tuner Monster (used for Synchro)
TYPE_SYNCHRO: int        = 0x2000       # 8192: Synchro Monster (Extra Deck)
TYPE_TOKEN: int          = 0x4000       # 16384: Token Monster
TYPE_QUICKPLAY: int      = 0x10000      # 65536: Quick-Play Spell Card
TYPE_CONTINUOUS: int     = 0x20000      # 131072: Continuous Spell or Continuous Trap
TYPE_EQUIP: int          = 0x40000      # 262144: Equip Spell Card
TYPE_FIELD: int          = 0x80000      # 524288: Field Spell Card
TYPE_COUNTER: int        = 0x100000     # 1048576: Counter Trap Card
TYPE_FLIP: int           = 0x200000     # 2097152: Flip Effect Monster
TYPE_TOON: int           = 0x400000     # 4194304: Toon Monster
TYPE_XYZ: int            = 0x800000     # 8388608: Xyz Monster (Extra Deck)
TYPE_PENDULUM: int       = 0x1000000    # 16777216: Pendulum Monster
TYPE_SPECIAL: int        = 0x2000000    # 33554432: Special Summon-only Monster
TYPE_SPSUMMON: int       = TYPE_SPECIAL # Alias for Special Summon-only Monster
TYPE_LINK: int           = 0x4000000    # 67108864: Link Monster (Extra Deck)

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.3: Card Attributes (datas.attribute bitmask)
# -----------------------------------------------------------------------------
ATTRIBUTE_EARTH: int     = 0x01         # 1: Earth attribute
ATTRIBUTE_WATER: int     = 0x02         # 2: Water attribute
ATTRIBUTE_FIRE: int      = 0x04         # 4: Fire attribute
ATTRIBUTE_WIND: int      = 0x08         # 8: Wind attribute
ATTRIBUTE_LIGHT: int     = 0x10         # 16: Light attribute
ATTRIBUTE_DARK: int      = 0x20         # 32: Dark attribute
ATTRIBUTE_DIVINE: int    = 0x40         # 64: Divine attribute (Egyptian Gods)

ATTRIBUTE_MAP: Dict[str, int] = {
    'earth': ATTRIBUTE_EARTH,
    'water': ATTRIBUTE_WATER,
    'fire': ATTRIBUTE_FIRE,
    'wind': ATTRIBUTE_WIND,
    'light': ATTRIBUTE_LIGHT,
    'dark': ATTRIBUTE_DARK,
    'divine': ATTRIBUTE_DIVINE
}

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.4: Monster Races / Species (datas.race bitmask)
# -----------------------------------------------------------------------------
RACE_WARRIOR: int        = 0x1          # Warrior
RACE_SPELLCASTER: int    = 0x2          # Spellcaster
RACE_FAIRY: int          = 0x4          # Fairy
RACE_FIEND: int          = 0x8          # Fiend
RACE_ZOMBIE: int         = 0x10         # Zombie
RACE_MACHINE: int        = 0x20         # Machine
RACE_AQUA: int           = 0x40         # Aqua
RACE_PYRO: int           = 0x80         # Pyro
RACE_ROCK: int           = 0x100        # Rock
RACE_WINGEDBEAST: int    = 0x200        # Winged Beast
RACE_PLANT: int          = 0x400        # Plant
RACE_INSECT: int         = 0x800        # Insect
RACE_THUNDER: int        = 0x1000       # Thunder
RACE_DRAGON: int         = 0x2000       # Dragon
RACE_BEAST: int          = 0x4000       # Beast
RACE_BEASTWARRIOR: int   = 0x8000       # Beast-Warrior
RACE_DINOSAUR: int       = 0x10000      # Dinosaur
RACE_FISH: int           = 0x20000      # Fish
RACE_SEASERPENT: int     = 0x40000      # Sea Serpent
RACE_REPTILE: int        = 0x80000      # Reptile
RACE_PSYCHIC: int        = 0x100000     # Psychic
RACE_DIVINEBEAST: int    = 0x200000     # Divine-Beast
RACE_CREATORGOD: int     = 0x400000     # Creator God
RACE_WYRM: int           = 0x800000     # Wyrm
RACE_CYBERSE: int        = 0x1000000    # Cyberse
RACE_ILLUSION: int       = 0x2000000    # Illusion (Series 12)

RACE_MAP: Dict[str, int] = {
    'warrior': RACE_WARRIOR,
    'spellcaster': RACE_SPELLCASTER,
    'fairy': RACE_FAIRY,
    'fiend': RACE_FIEND,
    'zombie': RACE_ZOMBIE,
    'machine': RACE_MACHINE,
    'aqua': RACE_AQUA,
    'pyro': RACE_PYRO,
    'rock': RACE_ROCK,
    'wingedbeast': RACE_WINGEDBEAST,
    'winged beast': RACE_WINGEDBEAST,
    'winged-beast': RACE_WINGEDBEAST,
    'plant': RACE_PLANT,
    'insect': RACE_INSECT,
    'thunder': RACE_THUNDER,
    'dragon': RACE_DRAGON,
    'beast': RACE_BEAST,
    'beastwarrior': RACE_BEASTWARRIOR,
    'beast-warrior': RACE_BEASTWARRIOR,
    'beast warrior': RACE_BEASTWARRIOR,
    'dinosaur': RACE_DINOSAUR,
    'fish': RACE_FISH,
    'seaserpent': RACE_SEASERPENT,
    'sea serpent': RACE_SEASERPENT,
    'sea-serpent': RACE_SEASERPENT,
    'reptile': RACE_REPTILE,
    'psychic': RACE_PSYCHIC,
    'divinebeast': RACE_DIVINEBEAST,
    'divine-beast': RACE_DIVINEBEAST,
    'divine beast': RACE_DIVINEBEAST,
    'creatorgod': RACE_CREATORGOD,
    'creator god': RACE_CREATORGOD,
    'wyrm': RACE_WYRM,
    'cyberse': RACE_CYBERSE,
    'illusion': RACE_ILLUSION
}

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.5: Link Arrow Bitmasks (Octal values in datas.def)
# -----------------------------------------------------------------------------
LINK_B: int   = 0o001    # Bottom
LINK_BL: int  = 0o002    # Bottom-Left
LINK_BR: int  = 0o004    # Bottom-Right
LINK_L: int   = 0o010    # Left
LINK_R: int   = 0o040    # Right
LINK_T: int   = 0o100    # Top
LINK_TL: int  = 0o200    # Top-Left
LINK_TR: int  = 0o400    # Top-Right

LINK_ARROW_MAP: Dict[str, int] = {
    'B': LINK_B, 'BOTTOM': LINK_B,
    'BL': LINK_BL, 'BOTTOM-LEFT': LINK_BL, 'BOTTOM_LEFT': LINK_BL,
    'BR': LINK_BR, 'BOTTOM-RIGHT': LINK_BR, 'BOTTOM_RIGHT': LINK_BR,
    'L': LINK_L, 'LEFT': LINK_L,
    'R': LINK_R, 'RIGHT': LINK_R,
    'T': LINK_T, 'TOP': LINK_T,
    'TL': LINK_TL, 'TOP-LEFT': LINK_TL, 'TOP_LEFT': LINK_TL,
    'TR': LINK_TR, 'TOP-RIGHT': LINK_TR, 'TOP_RIGHT': LINK_TR
}

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.6: Duelingbook Identifier Code Mappings
# -----------------------------------------------------------------------------
DB_CARD_TYPES: Dict[int, str] = {
    1: 'Monster',
    2: 'Spell',
    3: 'Trap'
}

DB_MONSTER_COLORS: Dict[int, str] = {
    1: 'Normal',
    2: 'Effect',
    3: 'Ritual',
    4: 'Fusion',
    5: 'Synchro',
    6: 'Xyz',
    7: 'Pendulum',
    8: 'Link'
}

DB_SPELL_PROPERTIES: Dict[int, str] = {
    1: 'Normal',
    2: 'Quick-Play',
    3: 'Continuous',
    4: 'Equip',
    5: 'Field',
    6: 'Ritual'
}

DB_TRAP_PROPERTIES: Dict[int, str] = {
    1: 'Normal',
    2: 'Continuous',
    3: 'Counter'
}

DB_ATTRIBUTES: Dict[int, str] = {
    1: 'EARTH',
    2: 'WATER',
    3: 'FIRE',
    4: 'WIND',
    5: 'LIGHT',
    6: 'DARK',
    7: 'DIVINE'
}

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.7: Official Master Rule Construction Limits
# -----------------------------------------------------------------------------
STANDARD_MIN_MAIN_DECK: int = 40       # Official tournament minimum Main Deck cards
STANDARD_MAX_MAIN_DECK: int = 60       # Official tournament maximum Main Deck cards
STANDARD_MAX_EXTRA_DECK: int = 15      # Official tournament maximum Extra Deck cards
STANDARD_MAX_SIDE_DECK: int = 15       # Official tournament maximum Side Deck cards
MAX_COPIES_PER_CARD: int = 3           # Official maximum copies of any card by name
MAX_USER_DECK_SLOTS: int = 20          # Maximum saved named deck slots per user

# Aliases for platform and bot services
STANDARD_MAIN_DECK_MIN: int = STANDARD_MIN_MAIN_DECK
STANDARD_MAIN_DECK_MAX: int = STANDARD_MAX_MAIN_DECK
STANDARD_EXTRA_DECK_MAX: int = STANDARD_MAX_EXTRA_DECK
STANDARD_SIDE_DECK_MAX: int = STANDARD_MAX_SIDE_DECK
STANDARD_CARD_COPY_LIMIT: int = MAX_COPIES_PER_CARD
INITIAL_HAND_SIZE: int = 5
STARTING_LIFE_POINTS: int = 8000
MONSTER_ZONES_COUNT: int = 5
SPELL_TRAP_ZONES_COUNT: int = 5

MIN_HAND_SIZE: int = 0                 # Hand minimum (player has 0 cards in hand)
DEFAULT_END_PHASE_HAND_LIMIT: int = 6  # Standard Master Rule End Phase discard threshold
HIEROGLYPH_HAND_LIMIT: int = 7         # Card-modified limit (Hieroglyph Lithograph)
NO_HAND_LIMIT: Optional[int] = None    # Card-modified limit (Infinite Cards)
MAX_HAND_SIZE: int = 7                 # Standard modified ceiling
DEFAULT_OPENING_HAND_P1: int = 5       # Turn 1 (Going First: 5 cards, no draw phase)
DEFAULT_OPENING_HAND_P2: int = 6       # Turn 2 (Going Second: 5 + 1 draw phase card)

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.8: Official Game State Zones
# -----------------------------------------------------------------------------
ZONE_MAIN_DECK: str = "MAIN_DECK"                     # Main Deck (Face-down draw pile)
ZONE_EXTRA_DECK: str = "EXTRA_DECK"                   # Extra Deck (Face-down, or face-up Pendulums)
ZONE_HAND: str = "HAND"                               # In-hand cards (Private knowledge)
ZONE_FIELD_SPELL: str = "FIELD_SPELL"                 # Field Zone (Dedicated Field Spell slot)
ZONE_GRAVEYARD: str = "GRAVEYARD"                     # Graveyard / GY (Public resource pile)
ZONE_BANISHMENT: str = "BANISHMENT"                   # Banished Pile (Face-up or Face-down)
ZONE_EXTRA_MONSTER: str = "EXTRA_MONSTER_ZONE"         # Extra Monster Zone (EMZ, Left / Right)
ZONE_PENDULUM: str = "PENDULUM_ZONE"                  # Pendulum Zone (PZ, Left / Right scales)
ZONE_MAIN_MONSTER: str = "MAIN_MONSTER_ZONE"           # Main Monster Zones 1-5
ZONE_SPELL_TRAP: str = "SPELL_TRAP_ZONE"               # Spell & Trap Zones 1-5

BANLIST_LIMITS: Dict[str, int] = {
    "Forbidden": 0,
    "Limited": 1,
    "Semi-Limited": 2,
    "Unlimited": 3
}

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.9: Official Card Rarities & Colors
# -----------------------------------------------------------------------------
RARITY_COMMON: str                   = 'Common'
RARITY_RARE: str                     = 'Rare'
RARITY_SUPER_RARE: str               = 'Super Rare'
RARITY_ULTRA_RARE: str               = 'Ultra Rare'
RARITY_SECRET_RARE: str              = 'Secret Rare'
RARITY_ULTIMATE_RARE: str            = 'Ultimate Rare'
RARITY_GHOST_RARE: str               = 'Ghost Rare'
RARITY_STARLIGHT_RARE: str           = 'Starlight Rare'
RARITY_COLLECTOR_RARE: str           = 'Collector\'s Rare'
RARITY_QUARTER_CENTURY_SECRET_RARE: str = 'Quarter Century Secret Rare'

OFFICIAL_RARITIES: List[str] = [
    RARITY_COMMON,
    RARITY_RARE,
    RARITY_SUPER_RARE,
    RARITY_ULTRA_RARE,
    RARITY_SECRET_RARE,
    RARITY_ULTIMATE_RARE,
    RARITY_GHOST_RARE,
    RARITY_STARLIGHT_RARE,
    RARITY_COLLECTOR_RARE,
    RARITY_QUARTER_CENTURY_SECRET_RARE,
]

RARITY_SHORT_CODES: Dict[str, str] = {
    'C': RARITY_COMMON,
    'R': RARITY_RARE,
    'SR': RARITY_SUPER_RARE,
    'UR': RARITY_ULTRA_RARE,
    'SCR': RARITY_SECRET_RARE,
    'UTR': RARITY_ULTIMATE_RARE,
    'GR': RARITY_GHOST_RARE,
    'STR': RARITY_STARLIGHT_RARE,
    'CR': RARITY_COLLECTOR_RARE,
    'QCSR': RARITY_QUARTER_CENTURY_SECRET_RARE,
}

RARITY_COLOR_CODES: Dict[str, int] = {
    RARITY_COMMON: 0xBDC3C7,                    # Silver / Grey
    RARITY_RARE: 0x95A5A6,                      # Silver foil title
    RARITY_SUPER_RARE: 0x3498DB,                # Foil holofoil art (Blue)
    RARITY_ULTRA_RARE: 0xF1C40F,                # Gold foil title + holo art (Gold)
    RARITY_SECRET_RARE: 0x9B59B6,               # Silver rainbow foil + cross-hatch (Prismatic/Purple)
    RARITY_ULTIMATE_RARE: 0xE67E22,             # Embossed relief (Orange)
    RARITY_GHOST_RARE: 0xECF0F1,                # Holographic 3D pale (Silver-White)
    RARITY_STARLIGHT_RARE: 0x1ABC9C,            # Starlight prismatic foil (Cyan)
    RARITY_COLLECTOR_RARE: 0xE74C3C,            # Textured border/art (Crimson)
    RARITY_QUARTER_CENTURY_SECRET_RARE: 0xF39C12 # 25th Anniversary gold/prismatic
}

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.10: Card Rules & Rarity Validation Helpers
# -----------------------------------------------------------------------------
def is_official_rarity(rarity_str: str) -> bool:
    """Checks whether a given rarity matches an official Yu-Gi-Oh! rarity."""
    if not rarity_str:
        return False
    norm = rarity_str.strip().title()
    return norm in OFFICIAL_RARITIES or rarity_str.strip().upper() in RARITY_SHORT_CODES

def has_field_awareness(card_subtype: str, effect_text: str) -> bool:
    """Determines if a card interacts with or requires a Field Spell."""
    sub = (card_subtype or "").lower()
    text = (effect_text or "").lower()
    if "field" in sub:
        return True
    field_keywords = [
        "field spell", "field card", "while you control a field spell",
        "control a face-up “lespookie” field spell", "control a “lespookie” field spell",
        "control a field spell", "planet kustomazi", "temple of the great kasutamaiza",
        "lespookie haunted mansion", "lespookie street, cursed lane"
    ]
    return any(k in text for k in field_keywords)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    # Passcode Boundaries
    "CUSTOM_PASSCODE_MIN",
    "CUSTOM_PASSCODE_MAX",
    "OFFICIAL_PASSCODE_MAX",
    # Types
    "TYPE_MONSTER",
    "TYPE_SPELL",
    "TYPE_TRAP",
    "TYPE_NORMAL",
    "TYPE_EFFECT",
    "TYPE_FUSION",
    "TYPE_RITUAL",
    "TYPE_TRAPMONSTER",
    "TYPE_SPIRIT",
    "TYPE_UNION",
    "TYPE_DUAL",
    "TYPE_TUNER",
    "TYPE_SYNCHRO",
    "TYPE_TOKEN",
    "TYPE_QUICKPLAY",
    "TYPE_CONTINUOUS",
    "TYPE_EQUIP",
    "TYPE_FIELD",
    "TYPE_COUNTER",
    "TYPE_FLIP",
    "TYPE_TOON",
    "TYPE_XYZ",
    "TYPE_PENDULUM",
    "TYPE_SPECIAL",
    "TYPE_SPSUMMON",
    "TYPE_LINK",
    # Attributes
    "ATTRIBUTE_EARTH",
    "ATTRIBUTE_WATER",
    "ATTRIBUTE_FIRE",
    "ATTRIBUTE_WIND",
    "ATTRIBUTE_LIGHT",
    "ATTRIBUTE_DARK",
    "ATTRIBUTE_DIVINE",
    "ATTRIBUTE_MAP",
    # Races
    "RACE_WARRIOR",
    "RACE_SPELLCASTER",
    "RACE_FAIRY",
    "RACE_FIEND",
    "RACE_ZOMBIE",
    "RACE_MACHINE",
    "RACE_AQUA",
    "RACE_PYRO",
    "RACE_ROCK",
    "RACE_WINGEDBEAST",
    "RACE_PLANT",
    "RACE_INSECT",
    "RACE_THUNDER",
    "RACE_DRAGON",
    "RACE_BEAST",
    "RACE_BEASTWARRIOR",
    "RACE_DINOSAUR",
    "RACE_FISH",
    "RACE_SEASERPENT",
    "RACE_REPTILE",
    "RACE_PSYCHIC",
    "RACE_DIVINEBEAST",
    "RACE_CREATORGOD",
    "RACE_WYRM",
    "RACE_CYBERSE",
    "RACE_ILLUSION",
    "RACE_MAP",
    # Link Arrows
    "LINK_B",
    "LINK_BL",
    "LINK_BR",
    "LINK_L",
    "LINK_R",
    "LINK_T",
    "LINK_TL",
    "LINK_TR",
    "LINK_ARROW_MAP",
    # Duelingbook Mappings
    "DB_CARD_TYPES",
    "DB_MONSTER_COLORS",
    "DB_SPELL_PROPERTIES",
    "DB_TRAP_PROPERTIES",
    "DB_ATTRIBUTES",
    # Master Rule Deck Limits
    "STANDARD_MIN_MAIN_DECK",
    "STANDARD_MAX_MAIN_DECK",
    "STANDARD_MAX_EXTRA_DECK",
    "STANDARD_MAX_SIDE_DECK",
    "MAX_COPIES_PER_CARD",
    "MAX_USER_DECK_SLOTS",
    "STANDARD_MAIN_DECK_MIN",
    "STANDARD_MAIN_DECK_MAX",
    "STANDARD_EXTRA_DECK_MAX",
    "STANDARD_SIDE_DECK_MAX",
    "STANDARD_CARD_COPY_LIMIT",
    "INITIAL_HAND_SIZE",
    "STARTING_LIFE_POINTS",
    "MONSTER_ZONES_COUNT",
    "SPELL_TRAP_ZONES_COUNT",
    "MIN_HAND_SIZE",
    "DEFAULT_END_PHASE_HAND_LIMIT",
    "HIEROGLYPH_HAND_LIMIT",
    "NO_HAND_LIMIT",
    "MAX_HAND_SIZE",
    "DEFAULT_OPENING_HAND_P1",
    "DEFAULT_OPENING_HAND_P2",
    # Zones
    "ZONE_MAIN_DECK",
    "ZONE_EXTRA_DECK",
    "ZONE_HAND",
    "ZONE_FIELD_SPELL",
    "ZONE_GRAVEYARD",
    "ZONE_BANISHMENT",
    "ZONE_EXTRA_MONSTER",
    "ZONE_PENDULUM",
    "ZONE_MAIN_MONSTER",
    "ZONE_SPELL_TRAP",
    "BANLIST_LIMITS",
    # Rarities
    "RARITY_COMMON",
    "RARITY_RARE",
    "RARITY_SUPER_RARE",
    "RARITY_ULTRA_RARE",
    "RARITY_SECRET_RARE",
    "RARITY_ULTIMATE_RARE",
    "RARITY_GHOST_RARE",
    "RARITY_STARLIGHT_RARE",
    "RARITY_COLLECTOR_RARE",
    "RARITY_QUARTER_CENTURY_SECRET_RARE",
    "OFFICIAL_RARITIES",
    "RARITY_SHORT_CODES",
    "RARITY_COLOR_CODES",
    # Helpers
    "is_official_rarity",
    "has_field_awareness",
]
