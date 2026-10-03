#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator (ocgcore / YGOPro / EDOPro) Constant Definitions
=============================================================================
This module centralizes all bitmasks, flags, and enumerations used by the
YGOPro core duel engine (ocgcore) and SQLite CDB database files.

Card parameters such as Card Type, Attribute, Race/Type, and Link Arrows
are stored as bitwise integer flags in the SQLite `datas` table.
Using bitwise OR (|) allows a single card to possess multiple properties
(for example, TYPE_MONSTER | TYPE_EFFECT | TYPE_XYZ).
=============================================================================
"""

# =============================================================================
# 1. CARD TYPES (datas.type bitmask)
# =============================================================================
# Represents the card category, summoning mechanic, and spell/trap speed.
TYPE_MONSTER        = 0x1          # 1: General Monster card
TYPE_SPELL          = 0x2          # 2: Spell / Magic card
TYPE_TRAP           = 0x4          # 4: Trap card
TYPE_NORMAL         = 0x10         # 16: Normal Monster or Normal Spell/Trap
TYPE_EFFECT         = 0x20         # 32: Effect Monster
TYPE_FUSION         = 0x40         # 64: Fusion Monster (Extra Deck)
TYPE_RITUAL         = 0x80         # 128: Ritual Monster or Ritual Spell
TYPE_TRAPMONSTER    = 0x100        # 256: Trap card that treats itself as a monster
TYPE_SPIRIT         = 0x200        # 512: Spirit Monster
TYPE_UNION          = 0x400        # 1024: Union Monster
TYPE_DUAL           = 0x800        # 2048: Gemini / Dual Monster
TYPE_TUNER          = 0x1000       # 4096: Tuner Monster (used for Synchro)
TYPE_SYNCHRO        = 0x2000       # 8192: Synchro Monster (Extra Deck)
TYPE_TOKEN          = 0x4000       # 16384: Token Monster
TYPE_QUICKPLAY      = 0x10000      # 65536: Quick-Play Spell Card
TYPE_CONTINUOUS     = 0x20000      # 131072: Continuous Spell or Continuous Trap
TYPE_EQUIP          = 0x40000      # 262144: Equip Spell Card
TYPE_FIELD          = 0x80000      # 524288: Field Spell Card
TYPE_COUNTER        = 0x100000     # 1048576: Counter Trap Card
TYPE_FLIP           = 0x200000     # 2097152: Flip Effect Monster
TYPE_TOON           = 0x400000     # 4194304: Toon Monster
TYPE_XYZ            = 0x800000     # 8388608: Xyz Monster (Extra Deck)
TYPE_PENDULUM       = 0x1000000    # 16777216: Pendulum Monster
TYPE_SPECIAL        = 0x2000000    # 33554432: Special Summon-only Monster
TYPE_LINK           = 0x4000000    # 67108864: Link Monster (Extra Deck)

# =============================================================================
# 2. CARD ATTRIBUTES (datas.attribute bitmask)
# =============================================================================
# Yu-Gi-Oh elemental attributes. Stored as distinct powers of 2.
ATTRIBUTE_EARTH     = 0x01         # 1: Earth attribute
ATTRIBUTE_WATER     = 0x02         # 2: Water attribute
ATTRIBUTE_FIRE      = 0x04         # 4: Fire attribute
ATTRIBUTE_WIND      = 0x08         # 8: Wind attribute
ATTRIBUTE_LIGHT     = 0x10         # 16: Light attribute
ATTRIBUTE_DARK      = 0x20         # 32: Dark attribute
ATTRIBUTE_DIVINE    = 0x40         # 64: Divine attribute (Egyptian Gods)

# =============================================================================
# 3. MONSTER RACES / TYPES (datas.race bitmask)
# =============================================================================
# Yu-Gi-Oh monster species/class.
RACE_WARRIOR        = 0x1          # Warrior
RACE_SPELLCASTER    = 0x2          # Spellcaster
RACE_FAIRY          = 0x4          # Fairy
RACE_FIEND          = 0x8          # Fiend
RACE_ZOMBIE         = 0x10         # Zombie
RACE_MACHINE        = 0x20         # Machine
RACE_AQUA           = 0x40         # Aqua
RACE_PYRO           = 0x80         # Pyro
RACE_ROCK           = 0x100        # Rock
RACE_WINGEDBEAST    = 0x200        # Winged Beast
RACE_PLANT          = 0x400        # Plant
RACE_INSECT         = 0x800        # Insect
RACE_THUNDER        = 0x1000       # Thunder
RACE_DRAGON         = 0x2000       # Dragon
RACE_BEAST          = 0x4000       # Beast
RACE_BEASTWARRIOR   = 0x8000       # Beast-Warrior
RACE_DINOSAUR       = 0x10000      # Dinosaur
RACE_FISH           = 0x20000      # Fish
RACE_SEASERPENT     = 0x40000      # Sea Serpent
RACE_REPTILE        = 0x80000      # Reptile
RACE_PSYCHIC        = 0x100000     # Psychic
RACE_DIVINEBEAST    = 0x200000     # Divine-Beast
RACE_CREATORGOD     = 0x400000     # Creator God
RACE_WYRM           = 0x800000     # Wyrm
RACE_CYBERSE        = 0x1000000    # Cyberse
RACE_ILLUSION       = 0x2000000    # Illusion (introduced in Series 12)

# =============================================================================
# 4. LINK ARROWS BITMASKS (Stored in datas.def for Link Monsters)
# =============================================================================
# In YGOPro's ocgcore, Link Monsters do not possess a DEF value.
# Instead, the DEF integer column stores an octal bitmask representing
# the 8 compass directions of active Link arrows pointing from the card:
#
#   TL (Top-Left: 0o200)       T (Top: 0o100)       TR (Top-Right: 0o400)
#   L  (Left:     0o010)             [CARD]          R  (Right:     0o040)
#   BL (Bot-Left: 0o002)       B (Bottom: 0o001)    BR (Bot-Right: 0o004)
# =============================================================================
LINK_B   = 0o001    # Bottom
LINK_BL  = 0o002    # Bottom-Left
LINK_BR  = 0o004    # Bottom-Right
LINK_L   = 0o010    # Left
LINK_R   = 0o040    # Right
LINK_T   = 0o100    # Top
LINK_TL  = 0o200    # Top-Left
LINK_TR  = 0o400    # Top-Right

# Mapping table connecting string abbreviations and common names to bit values
LINK_ARROW_MAP = {
    'B': LINK_B, 'BOTTOM': LINK_B,
    'BL': LINK_BL, 'BOTTOM-LEFT': LINK_BL, 'BOTTOM_LEFT': LINK_BL,
    'BR': LINK_BR, 'BOTTOM-RIGHT': LINK_BR, 'BOTTOM_RIGHT': LINK_BR,
    'L': LINK_L, 'LEFT': LINK_L,
    'R': LINK_R, 'RIGHT': LINK_R,
    'T': LINK_T, 'TOP': LINK_T,
    'TL': LINK_TL, 'TOP-LEFT': LINK_TL, 'TOP_LEFT': LINK_TL,
    'TR': LINK_TR, 'TOP-RIGHT': LINK_TR, 'TOP_RIGHT': LINK_TR
}

# =============================================================================
# 5. STRING LOOKUP MAPPINGS
# =============================================================================
# Mapping lowercase attribute names to their ocgcore integer bitmasks
ATTRIBUTE_MAP = {
    'earth': ATTRIBUTE_EARTH,
    'water': ATTRIBUTE_WATER,
    'fire': ATTRIBUTE_FIRE,
    'wind': ATTRIBUTE_WIND,
    'light': ATTRIBUTE_LIGHT,
    'dark': ATTRIBUTE_DARK,
    'divine': ATTRIBUTE_DIVINE
}

# Mapping lowercase monster race/type names to their ocgcore integer bitmasks
RACE_MAP = {
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

# =============================================================================
# 6. DUELINGBOOK IDENTIFIER MAPPINGS
# =============================================================================
# Duelingbook exports integer codes for card types, monster frames, and spell/trap properties
DB_CARD_TYPES = {
    1: 'Monster',
    2: 'Spell',
    3: 'Trap'
}

DB_MONSTER_COLORS = {
    1: 'Normal',
    2: 'Effect',
    3: 'Ritual',
    4: 'Fusion',
    5: 'Synchro',
    6: 'Xyz',
    7: 'Pendulum',
    8: 'Link'
}

DB_SPELL_PROPERTIES = {
    1: 'Normal',
    2: 'Quick-Play',
    3: 'Continuous',
    4: 'Equip',
    5: 'Field',
    6: 'Ritual'
}

DB_TRAP_PROPERTIES = {
    1: 'Normal',
    2: 'Continuous',
    3: 'Counter'
}

DB_ATTRIBUTES = {
    1: 'EARTH',
    2: 'WATER',
    3: 'FIRE',
    4: 'WIND',
    5: 'LIGHT',
    6: 'DARK',
    7: 'DIVINE'
}

# =============================================================================
# 7. OFFICIAL YU-GI-OH! CARD RARITIES
# =============================================================================
# Standard core booster and tournament rarities used in Yu-Gi-Oh! TCG/OCG.
RARITY_COMMON                   = 'Common'
RARITY_RARE                     = 'Rare'
RARITY_SUPER_RARE               = 'Super Rare'
RARITY_ULTRA_RARE               = 'Ultra Rare'
RARITY_SECRET_RARE              = 'Secret Rare'
RARITY_ULTIMATE_RARE            = 'Ultimate Rare'
RARITY_GHOST_RARE               = 'Ghost Rare'
RARITY_STARLIGHT_RARE           = 'Starlight Rare'
RARITY_COLLECTOR_RARE           = 'Collector\'s Rare'
RARITY_QUARTER_CENTURY_SECRET_RARE = 'Quarter Century Secret Rare'

OFFICIAL_RARITIES = [
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

RARITY_SHORT_CODES = {
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

RARITY_COLOR_CODES = {
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

def is_official_rarity(rarity_str: str) -> bool:
    """Checks whether a given rarity matches an official Yu-Gi-Oh! rarity."""
    if not rarity_str:
        return False
    norm = rarity_str.strip().title()
    return norm in OFFICIAL_RARITIES or rarity_str.strip().upper() in RARITY_SHORT_CODES

def has_field_awareness(card_subtype: str, effect_text: str) -> bool:
    """
    Determines if a card has Field Awareness (either is a Field Spell or explicitly
    mentions, requires, tutors, or interacts with a Field Spell).
    """
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

