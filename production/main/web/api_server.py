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
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from typing import Optional, List, Dict, Any
import os
import sys
import io
import zipfile

# Resolve base directories
try:
    from config.paths import (
        BASE_DIR, STORY_DB_PATH, TEMPLATES_DIR, TOOLS_DIR,
        CDB_OUTPUT_PATH, DECKS_DIR, EXPANSIONS_DIR, SCRIPTS_DIR
    )
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    STORY_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ygo_story.db")
    TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    TOOLS_DIR = os.path.join(BASE_DIR, "development", "tools")
    CDB_OUTPUT_PATH = os.path.join(BASE_DIR, "production", "shared", "expansions", "custom_cards.cdb")
    DECKS_DIR = os.path.join(BASE_DIR, "production", "shared", "decks")
    EXPANSIONS_DIR = os.path.join(BASE_DIR, "production", "shared", "expansions")
    SCRIPTS_DIR = os.path.join(EXPANSIONS_DIR, "scripts")
    STORY_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ygo_story.db")
    TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    TOOLS_DIR = os.path.join(BASE_DIR, "development", "tools")
    CDB_OUTPUT_PATH = os.path.join(BASE_DIR, "production", "shared", "expansions", "custom_cards.cdb")
    DECKS_DIR = os.path.join(BASE_DIR, "production", "shared", "decks")
    EXPANSIONS_DIR = os.path.join(BASE_DIR, "production", "shared", "expansions")

DB_PATH = STORY_DB_PATH

# Import modular database helpers and Pydantic models
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import get_db, db_session
from models import CardInput, StatusResponse

# Import Duelingbook card importer tool
if TOOLS_DIR not in sys.path:
    sys.path.append(TOOLS_DIR)
try:
    from duelingbook_importer import import_card_data
except ImportError:
    import_card_data = None

# Initialize FastAPI application
app = FastAPI(
    title="Yu-Gi-Oh! Story & Custom Card Engine API",
    description="Synchronizes Duelingbook custom cards with SQLite lore database and ocgcore simulator.",
    version="1.2.0"
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


# =============================================================================
# 5. SHARED CLIENT ASSET ENDPOINTS (For remote players / clients)
# =============================================================================

@app.get("/api/shared/cdb", summary="Download compiled custom_cards.cdb")
def download_cdb():
    """Serves the latest compiled CDB expansion database for players/clients."""
    if os.path.exists(CDB_OUTPUT_PATH):
        return FileResponse(
            path=CDB_OUTPUT_PATH,
            filename="custom_cards.cdb",
            media_type="application/octet-stream"
        )
    raise HTTPException(status_code=404, detail="custom_cards.cdb not yet generated.")


@app.get("/api/shared/decks", summary="List downloadable .ydk deck files")
def list_shared_decks() -> List[Dict[str, Any]]:
    """Returns all available .ydk deck files in the shared decks directory."""
    if not os.path.exists(DECKS_DIR):
        return []
    deck_files = []
    for f in os.listdir(DECKS_DIR):
        if f.endswith(".ydk"):
            fp = os.path.join(DECKS_DIR, f)
            deck_files.append({
                "filename": f,
                "size_bytes": os.path.getsize(fp),
                "download_url": f"/api/shared/decks/{f}"
            })
    return deck_files


@app.get("/api/shared/manifest", summary="Retrieve expansion package manifest for client synchronization")
def get_shared_manifest() -> Dict[str, Any]:
    """Provides metadata for player clients to synchronize custom cards and scripts over the network."""
    scripts_list = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")] if os.path.exists(SCRIPTS_DIR) else []
    deck_files = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")] if os.path.exists(DECKS_DIR) else []

    return {
        "version": "1.2.0",
        "has_cdb": os.path.exists(CDB_OUTPUT_PATH),
        "cdb_size_bytes": os.path.getsize(CDB_OUTPUT_PATH) if os.path.exists(CDB_OUTPUT_PATH) else 0,
        "cdb_download_url": "/api/shared/cdb",
        "scripts_count": len(scripts_list),
        "scripts_zip_url": "/api/shared/scripts_zip",
        "decks_count": len(deck_files),
        "decks_download_url": "/api/shared/decks"
    }


@app.get("/api/shared/scripts_zip", summary="Download all Lua effect scripts as a zip archive")
def download_scripts_zip():
    """Bundles all Lua effect scripts into an in-memory zip archive for player clients."""
    if not os.path.exists(SCRIPTS_DIR):
        raise HTTPException(status_code=404, detail="Scripts directory not found.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for fname in os.listdir(SCRIPTS_DIR):
            if fname.endswith(".lua"):
                fpath = os.path.join(SCRIPTS_DIR, fname)
                zip_file.write(fpath, arcname=fname)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=scripts.zip"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)


