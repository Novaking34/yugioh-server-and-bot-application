# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tools.constants
Description:
    Backward-compatibility bridge re-exporting canonical game rules,
    bitmasks, rarities, and limits from the centralized configuration subsystem:
        config.game_rules
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.game_rules import *
import config.game_rules as _rules

# =============================================================================
# BLOCK 3: BODY BLOCK (Re-exports & Compatibility Facade)
# =============================================================================

# All bitmasks, attributes, races, links, rarities, and deck boundaries are
# canonically defined in config.game_rules.

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Namespace Control & Exports)
# =============================================================================

__all__ = _rules.__all__
