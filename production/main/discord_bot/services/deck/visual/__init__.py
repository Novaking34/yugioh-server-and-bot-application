# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: discord_bot.services.deck.visual
Description:
    Visual & Tactical Presentation Layer:
    - analytics: Tactical deck profiling & Master Rule 5 legality
    - canvas: Pillow visual canvas rendering (10-column DuelingBook layout)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

# =============================================================================
# BLOCK 3: BODY BLOCK (Presentation Layer Re-Exports)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Tactical Analytics & Legality Engine
# -----------------------------------------------------------------------------
from .analytics import (
    analyze_deck_structure,
    validate_deck_legality,
)

# -----------------------------------------------------------------------------
# Sub-Block 3.2: Visual Canvas Renderer
# -----------------------------------------------------------------------------
from .canvas import (
    render_deck_canvas,
    render_player_deck_canvas,
    render_character_deck_canvas,
)

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================
__all__ = [
    "analyze_deck_structure",
    "validate_deck_legality",
    "render_deck_canvas",
    "render_player_deck_canvas",
    "render_character_deck_canvas",
]
