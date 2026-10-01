#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Story & Custom Card Catalog API Server & Web Dashboard
=============================================================================
Provides a REST API and real-time Web Dashboard for browsing custom cards,
viewing story lore sagas, querying character decks, and receiving card
submissions from Duelingbook exports.

Run directly:
    uvicorn story_database.api_server:app --host 0.0.0.0 --port 8000 --reload
Or via master CLI:
    ./manage.sh web
=============================================================================
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from typing import Optional, List, Dict, Any
import os
import sys

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
TEMPLATES_DIR = os.path.join(BASE_DIR, "story_database", "templates")

# Import modular database helpers and Pydantic models
sys.path.append(os.path.join(BASE_DIR, "story_database"))
from database import get_db, db_session
from models import CardInput, StatusResponse

# Import Duelingbook card importer tool
sys.path.append(os.path.join(BASE_DIR, "tools"))
try:
    from duelingbook_importer import import_card_data
except ImportError:
    import_card_data = None

# Initialize FastAPI application
app = FastAPI(
    title="Yu-Gi-Oh! Story & Custom Card Engine API",
    description="Synchronizes Duelingbook custom cards with SQLite lore database and ocgcore simulator.",
    version="1.1.0"
)


# =============================================================================
# 1. WEB DASHBOARD ROUTE
# =============================================================================

@app.get("/", response_class=HTMLResponse, summary="Web Catalog Dashboard")
def serve_dashboard():
    """Serves the interactive web dashboard for browsing custom cards and lore."""
    template_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Error: Dashboard template not found.</h2>", status_code=500)


# =============================================================================
# 2. CARD CATALOG ENDPOINTS
# =============================================================================

@app.get("/api/cards", summary="Search and filter custom cards")
def list_cards(
    q: Optional[str] = Query(None, description="Fuzzy search query across name, effect, or lore"),
    card_type: Optional[str] = Query(None, description="Filter by Monster, Spell, or Trap")
) -> List[Dict[str, Any]]:
    """
    Returns custom cards registered in the database, with optional filtering
    by keywords or card category.
    """
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT c.*, f.name AS faction_name, ch.name AS character_name
        FROM custom_cards c
        LEFT JOIN factions f ON c.faction_id = f.id
        LEFT JOIN characters ch ON c.signature_character_id = ch.id
        WHERE 1=1
    """
    params = []

    if q:
        query += " AND (c.name LIKE ? OR c.effect_text LIKE ? OR c.lore_text LIKE ?)"
        wildcard = f"%{q}%"
        params.extend([wildcard, wildcard, wildcard])

    if card_type:
        query += " AND c.card_type = ?"
        params.append(card_type)

    query += " ORDER BY c.id ASC"
    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


@app.get("/api/cards/{card_id}", summary="Get card by passcode")
def get_card(card_id: int) -> Dict[str, Any]:
    """Retrieves full details of a specific card by its 8-digit passcode."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, f.name AS faction_name, ch.name AS character_name
        FROM custom_cards c
        LEFT JOIN factions f ON c.faction_id = f.id
        LEFT JOIN characters ch ON c.signature_character_id = ch.id
        WHERE c.id = ?
    """, (card_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found.")
    return dict(row)


@app.post("/api/cards", response_model=StatusResponse, summary="Register a custom card")
def create_card(card: CardInput):
    """
    Registers a new custom card, automatically syncing with the live duel simulator CDB
    and generating its Lua effect script scaffold.
    """
    if not import_card_data:
        raise HTTPException(status_code=500, detail="Duelingbook importer module not available.")

    payload = card.model_dump(by_alias=True)
    try:
        cid = import_card_data(payload, sync_simulator=True)
        return StatusResponse(
            status="success",
            id=cid,
            message=f"Card '{card.name}' registered & synced to simulator!"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import card: {str(e)}")


# =============================================================================
# 3. STORY LORE & SAGA ENDPOINTS
# =============================================================================

@app.get("/api/lore", summary="Retrieve all lore arcs, factions, and character dossiers")
def get_lore() -> Dict[str, Any]:
    """Returns narrative chronicles including Sagas, Factions, Characters, and Duel Logs."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM lore_arcs ORDER BY id ASC")
    arcs = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM factions ORDER BY id ASC")
    factions = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM characters ORDER BY id ASC")
    characters = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM duel_logs ORDER BY id DESC")
    duels = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "arcs": arcs,
        "factions": factions,
        "characters": characters,
        "duel_logs": duels
    }


# =============================================================================
# 4. DECKLIST ENDPOINTS
# =============================================================================

@app.get("/api/decks", summary="Retrieve story decks")
def get_decks() -> List[Dict[str, Any]]:
    """Returns all pre-constructed story character decks."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.*, c.name AS character_name
        FROM decks d
        LEFT JOIN characters c ON d.character_id = c.id
        ORDER BY d.id ASC
    """)
    decks = [dict(r) for r in cur.fetchall()]
    conn.close()
    return decks


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
