# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: discord_bot.services.deck.visual.canvas
Description:
    Visual deck canvas renderer using Pillow (PIL). Generates official
    DuelingBook / EDOPro-style 10-column card grids, tournament headers,
    legality banners, and high-resolution composite images.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw

from ..foundation.constants import (
    STANDARD_MIN_MAIN_DECK,
    STANDARD_MAX_MAIN_DECK,
    STANDARD_MAX_EXTRA_DECK,
    STANDARD_MAX_SIDE_DECK
)

try:
    from config.paths import PICS_DIR, DECKS_DIR
except ImportError:
    PICS_DIR = None
    DECKS_DIR = None

# =============================================================================
# BLOCK 3: BODY BLOCK (Visual Deck Canvas Rendering Engine)
# =============================================================================


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Repository Root Discovery & Asset Resolution
# -----------------------------------------------------------------------------

def _find_repo_root() -> str:
    """Traverses upward until reaching the repository root containing data/expansions or manage.py."""
    curr = os.path.abspath(os.path.dirname(__file__))
    while curr and os.path.dirname(curr) != curr:
        if os.path.exists(os.path.join(curr, "data", "expansions", "pics")) or os.path.exists(os.path.join(curr, "manage.py")):
            return curr
        curr = os.path.dirname(curr)
    # Fallback: 6 levels up from visual/canvas.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Core 10-Column Visual Canvas Renderer
# -----------------------------------------------------------------------------

def render_deck_canvas(
    deck_title: str,
    main_cards: List[Dict[str, Any]],
    extra_cards: List[Dict[str, Any]],
    side_cards: List[Dict[str, Any]],
    is_legal: bool,
    output_path: Optional[str] = None,
    pics_dir: Optional[str] = None
) -> str:
    """
    Renders a full DuelingBook / EDOPro style visual deck canvas:
    - Main Deck grid (10 cards per row)
    - Extra Deck row (up to 15 cards)
    - Side Deck row (up to 15 cards)
    - Visual legality banner & card counts
    Saves image to disk and returns its absolute path.
    """
    expanded_main: List[Dict[str, Any]] = []
    for c in main_cards:
        expanded_main.extend([c] * c.get("quantity", 1))

    expanded_extra: List[Dict[str, Any]] = []
    for c in extra_cards:
        expanded_extra.extend([c] * c.get("quantity", 1))

    expanded_side: List[Dict[str, Any]] = []
    for c in side_cards:
        expanded_side.extend([c] * c.get("quantity", 1))

    card_w, card_h = 75, 105
    pad_x, pad_y = 6, 8
    cols = 10
    margin_x = 24

    main_rows = max(1, (len(expanded_main) + cols - 1) // cols) if expanded_main else 1
    extra_rows = max(1, (len(expanded_extra) + cols - 1) // cols) if expanded_extra else 0
    side_rows = max(1, (len(expanded_side) + cols - 1) // cols) if expanded_side else 0

    canvas_w = (margin_x * 2) + (cols * card_w) + ((cols - 1) * pad_x)

    header_h = 70
    main_section_h = 35 + (main_rows * (card_h + pad_y))
    extra_section_h = (35 + (extra_rows * (card_h + pad_y))) if extra_rows > 0 else 0
    side_section_h = (35 + (side_rows * (card_h + pad_y))) if side_rows > 0 else 0
    canvas_h = header_h + main_section_h + extra_section_h + side_section_h + 30

    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(18, 20, 26))
    draw = ImageDraw.Draw(canvas)

    # 1. Header Bar with Legality Status
    legality_text = "LEGAL (MR5)" if is_legal else "ILLEGAL / FORMAT VIOLATION"
    badge_bg = (34, 139, 34) if is_legal else (178, 34, 34)

    draw.rectangle([(margin_x, 15), (canvas_w - margin_x, 55)], fill=(28, 32, 42))
    draw.rectangle([(canvas_w - margin_x - 170, 20), (canvas_w - margin_x - 10, 50)], fill=badge_bg)
    draw.text((margin_x + 15, 25), deck_title, fill=(255, 215, 0))
    draw.text((canvas_w - margin_x - 160, 28), legality_text, fill=(255, 255, 255))

    root_dir = _find_repo_root()
    if not pics_dir:
        pics_dir = PICS_DIR if PICS_DIR and os.path.exists(PICS_DIR) else os.path.join(root_dir, "data", "expansions", "pics")

    curr_y = header_h + 10

    def draw_section(title: str, cards_list: List[Dict[str, Any]], start_y: int) -> int:
        draw.text((margin_x, start_y), title, fill=(200, 205, 215))
        y_offset = start_y + 25

        for idx, c in enumerate(cards_list):
            col = idx % cols
            row = idx // cols
            cx = margin_x + (col * (card_w + pad_x))
            cy = y_offset + (row * (card_h + pad_y))

            cid = c.get("id")
            img_path = os.path.join(pics_dir, f"{cid}.jpg") if cid else ""

            if img_path and os.path.exists(img_path):
                try:
                    card_pic = Image.open(img_path).resize((card_w, card_h), Image.Resampling.LANCZOS)
                    canvas.paste(card_pic, (cx, cy))
                except Exception:
                    draw.rectangle([(cx, cy), (cx + card_w, cy + card_h)], fill=(45, 50, 60), outline=(80, 90, 105))
                    draw.text((cx + 5, cy + 10), str(cid or "?"), fill=(255, 255, 255))
            else:
                draw.rectangle([(cx, cy), (cx + card_w, cy + card_h)], fill=(45, 50, 60), outline=(80, 90, 105))
                draw.text((cx + 5, cy + 10), str(cid or "?"), fill=(255, 255, 255))

        rows_count = max(1, (len(cards_list) + cols - 1) // cols) if cards_list else 0
        return y_offset + (rows_count * (card_h + pad_y)) + 15

    # Main Deck
    main_title = f"MAIN DECK ({len(expanded_main)} / {STANDARD_MAX_MAIN_DECK}) - Min: {STANDARD_MIN_MAIN_DECK}"
    curr_y = draw_section(main_title, expanded_main, curr_y)

    # Extra Deck
    if expanded_extra or extra_rows > 0:
        extra_title = f"EXTRA DECK ({len(expanded_extra)} / {STANDARD_MAX_EXTRA_DECK})"
        curr_y = draw_section(extra_title, expanded_extra, curr_y)

    # Side Deck
    if expanded_side or side_rows > 0:
        side_title = f"SIDE DECK ({len(expanded_side)} / {STANDARD_MAX_SIDE_DECK})"
        curr_y = draw_section(side_title, expanded_side, curr_y)

    if not output_path:
        renders_dir = os.path.join(DECKS_DIR, "renders") if DECKS_DIR else os.path.join(root_dir, "data", "decks", "renders")
        os.makedirs(renders_dir, exist_ok=True)
        safe_title = "".join(ch if ch.isalnum() else "_" for ch in deck_title).strip("_")
        target_file = os.path.join(renders_dir, f"deck_{safe_title}.png")
    else:
        target_file = output_path
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)

    canvas.save(target_file, "PNG")
    return os.path.abspath(target_file)


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Player Active Deck Canvas Renderer
# -----------------------------------------------------------------------------

async def render_player_deck_canvas(
    db_path: str,
    user_id: str,
    deck_title: Optional[str] = None,
    output_path: Optional[str] = None
) -> Optional[str]:
    """Retrieves player deck partition and renders it as an official visual canvas."""
    from ..domain.storage import partition_player_deck
    partition = await partition_player_deck(db_path, user_id)
    d_name = deck_title or f"Player {user_id}'s Deck"

    root_dir = _find_repo_root()
    pics_dir = PICS_DIR if PICS_DIR and os.path.exists(PICS_DIR) else os.path.join(root_dir, "data", "expansions", "pics")
    renders_dir = os.path.join(DECKS_DIR, "renders") if DECKS_DIR else os.path.join(root_dir, "data", "decks", "renders")
    os.makedirs(renders_dir, exist_ok=True)

    target_file = output_path or os.path.join(renders_dir, f"deck_{user_id}.png")

    return render_deck_canvas(
        deck_title=d_name,
        main_cards=partition["main_deck"],
        extra_cards=partition["extra_deck"],
        side_cards=partition["side_deck"],
        is_legal=partition["is_legal"],
        output_path=target_file,
        pics_dir=pics_dir
    )


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Story Character Deck Canvas Renderer
# -----------------------------------------------------------------------------

async def render_character_deck_canvas(
    db_path: str,
    deck_id: int,
    output_path: Optional[str] = None
) -> Optional[str]:
    """Retrieves character story deck and renders it as an official visual canvas."""
    from ..domain.story import fetch_character_deck_by_id
    deck = await fetch_character_deck_by_id(db_path, deck_id)
    if not deck:
        return None

    cards = deck.get("cards", [])
    main_cards = [c for c in cards if (c.get("section") or "").upper() == "MAIN"]
    extra_cards = [c for c in cards if (c.get("section") or "").upper() == "EXTRA"]
    side_cards = [c for c in cards if (c.get("section") or "").upper() == "SIDE"]

    d_name = f"{deck['name']} ({deck.get('duelist_name') or 'Story'})"

    root_dir = _find_repo_root()
    pics_dir = PICS_DIR if PICS_DIR and os.path.exists(PICS_DIR) else os.path.join(root_dir, "data", "expansions", "pics")
    renders_dir = os.path.join(DECKS_DIR, "renders") if DECKS_DIR else os.path.join(root_dir, "data", "decks", "renders")
    os.makedirs(renders_dir, exist_ok=True)

    target_file = output_path or os.path.join(renders_dir, f"story_deck_{deck_id}.png")

    return render_deck_canvas(
        deck_title=d_name,
        main_cards=main_cards,
        extra_cards=extra_cards,
        side_cards=side_cards,
        is_legal=deck["is_legal"],
        output_path=target_file,
        pics_dir=pics_dir
    )


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Exports & Translation Unit Manifest)
# =============================================================================

__all__ = [
    "render_deck_canvas",
    "render_player_deck_canvas",
    "render_character_deck_canvas",
]

