"""
=============================================================================
Yu-Gi-Oh! Platform - Card Compilation & Development Tools
=============================================================================
Provides data pipelines and conversion utilities:
- `cdb_builder`: Compiles custom cards into ocgcore binary SQLite .cdb files.
- `constants`: Centralized bitmasks, card types, races, attributes, and link arrows.
- `duelingbook_importer`: Imports and parses Duelingbook JSON card definitions.
- `export_deck`: Exports character story and player decks to standard .ydk format.
- `lua_generator`: Analyzes card effects and generates syntactically valid Lua scripts.
=============================================================================
"""

from .constants import (
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_NORMAL, TYPE_EFFECT,
    TYPE_FUSION, TYPE_RITUAL, TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK,
    TYPE_TUNER, TYPE_QUICKPLAY, TYPE_CONTINUOUS, TYPE_EQUIP, TYPE_FIELD, TYPE_COUNTER,
    ATTRIBUTE_EARTH, ATTRIBUTE_WATER, ATTRIBUTE_FIRE, ATTRIBUTE_WIND,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, ATTRIBUTE_DIVINE,
    RACE_WARRIOR, RACE_SPELLCASTER, RACE_FAIRY, RACE_FIEND, RACE_DRAGON,
    RACE_MACHINE, RACE_CYBERSE, RACE_ILLUSION,
    LINK_B, LINK_BL, LINK_BR, LINK_L, LINK_R, LINK_T, LINK_TL, LINK_TR,
    ATTRIBUTE_MAP, RACE_MAP, LINK_ARROW_MAP
)

from .cdb_builder import build_cdb, parse_card_type
from .export_deck import export_deck, export_all_decks, export_player_deck
from .duelingbook_importer import import_from_json_file, import_card_dict
from .lua_generator import generate_lua_for_card, generate_all_scripts

__all__ = [
    "build_cdb",
    "parse_card_type",
    "export_deck",
    "export_all_decks",
    "export_player_deck",
    "import_from_json_file",
    "import_card_dict",
    "generate_lua_for_card",
    "generate_all_scripts",
    "TYPE_MONSTER", "TYPE_SPELL", "TYPE_TRAP", "TYPE_NORMAL", "TYPE_EFFECT",
    "TYPE_FUSION", "TYPE_RITUAL", "TYPE_SYNCHRO", "TYPE_XYZ", "TYPE_PENDULUM", "TYPE_LINK",
    "TYPE_TUNER", "TYPE_QUICKPLAY", "TYPE_CONTINUOUS", "TYPE_EQUIP", "TYPE_FIELD", "TYPE_COUNTER",
    "ATTRIBUTE_EARTH", "ATTRIBUTE_WATER", "ATTRIBUTE_FIRE", "ATTRIBUTE_WIND",
    "ATTRIBUTE_LIGHT", "ATTRIBUTE_DARK", "ATTRIBUTE_DIVINE",
    "RACE_WARRIOR", "RACE_SPELLCASTER", "RACE_FAIRY", "RACE_FIEND", "RACE_DRAGON",
    "RACE_MACHINE", "RACE_CYBERSE", "RACE_ILLUSION",
    "LINK_B", "LINK_BL", "LINK_BR", "LINK_L", "LINK_R", "LINK_T", "LINK_TL", "LINK_TR",
    "ATTRIBUTE_MAP", "RACE_MAP", "LINK_ARROW_MAP"
]
