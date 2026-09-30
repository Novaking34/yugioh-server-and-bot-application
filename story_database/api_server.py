#!/usr/bin/env python3
"""
Yu-Gi-Oh Story & Custom Card Catalog API Server & Web Dashboard
Run with: uvicorn api_server:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")
sys.path.append(os.path.join(BASE_DIR, "tools"))
from duelingbook_importer import import_card_data

app = FastAPI(title="Yu-Gi-Oh Story & Custom Card Engine", version="1.0.0")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class CardInput(BaseModel):
    name: str
    card_type: str
    card_subtype: Optional[str] = "Normal"
    attribute: Optional[str] = None
    monster_type: Optional[str] = None
    level_or_rank_or_link: Optional[int] = None
    scale: Optional[int] = None
    atk: Optional[int] = None
    def_: Optional[int] = None
    link_arrows: Optional[str] = None
    effect_text: str
    pendulum_effect: Optional[str] = None
    duelingbook_id: Optional[str] = None
    duelingbook_url: Optional[str] = None
    image_url: Optional[str] = None
    creator_name: Optional[str] = "Custom Designer"
    lore_text: Optional[str] = None
    faction_id: Optional[int] = None
    story_significance: Optional[str] = "Custom Card"

@app.get("/api/cards")
def list_cards(q: Optional[str] = None, card_type: Optional[str] = None):
    conn = get_db()
    cur = conn.cursor()
    query = """
        SELECT c.*, f.name as faction_name, ch.name as character_name
        FROM custom_cards c
        LEFT JOIN factions f ON c.faction_id = f.id
        LEFT JOIN characters ch ON c.signature_character_id = ch.id
        WHERE 1=1
    """
    params = []
    if q:
        query += " AND (c.name LIKE ? OR c.effect_text LIKE ? OR c.lore_text LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if card_type:
        query += " AND c.card_type = ?"
        params.append(card_type)
        
    query += " ORDER BY c.id ASC"
    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/cards/{card_id}")
def get_card(card_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, f.name as faction_name, ch.name as character_name
        FROM custom_cards c
        LEFT JOIN factions f ON c.faction_id = f.id
        LEFT JOIN characters ch ON c.signature_character_id = ch.id
        WHERE c.id = ?
    """, (card_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Card not found")
    return dict(row)

@app.post("/api/cards")
def create_card(card: CardInput):
    data = card.dict()
    if "def_" in data:
        data["def"] = data.pop("def_")
    try:
        cid = import_card_data(data)
        return {"status": "success", "id": cid, "message": f"Card '{card.name}' registered & synced to simulator!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/lore")
def get_lore():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lore_arcs")
    arcs = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM factions")
    factions = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM characters")
    chars = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM duel_logs ORDER BY id DESC")
    duels = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"arcs": arcs, "factions": factions, "characters": chars, "duel_logs": duels}

@app.get("/api/decks")
def get_decks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.*, c.name as character_name
        FROM decks d
        LEFT JOIN characters c ON d.character_id = c.id
    """)
    decks = [dict(r) for r in cur.fetchall()]
    conn.close()
    return decks

@app.get("/", response_class=HTMLResponse)
def dashboard_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yu-Gi-Oh Custom Card Catalog & Story Engine</title>
    <style>
        :root {
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --accent: #58a6ff;
            --gold: #d29922;
            --card-monster: #c97434;
            --card-spell: #1d9e74;
            --card-trap: #bc3576;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 24px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        h1 { color: #f0f6fc; font-size: 24px; }
        .badge {
            background: #238636;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .search-bar {
            width: 100%;
            max-width: 450px;
            padding: 10px 14px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: #fff;
            font-size: 14px;
            margin-bottom: 24px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            border-color: var(--accent);
        }
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        .card-thumb {
            width: 60px;
            height: 60px;
            border-radius: 6px;
            object-fit: cover;
            border: 1px solid var(--border);
            background: #21262d;
        }
        .card-title {
            font-size: 16px;
            font-weight: bold;
            color: #f0f6fc;
        }
        .tag {
            display: inline-block;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 4px;
        }
        .tag-monster { background: var(--card-monster); color: white; }
        .tag-spell { background: var(--card-spell); color: white; }
        .tag-trap { background: var(--card-trap); color: white; }
        .stats-box {
            background: #090d13;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            margin-bottom: 12px;
            color: #8b949e;
        }
        .stats-box span { color: #f0f6fc; font-weight: 600; }
        .effect-box {
            font-size: 13px;
            background: #0d1117;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid var(--accent);
            margin-bottom: 12px;
            white-space: pre-wrap;
        }
        .lore-box {
            font-size: 12px;
            font-style: italic;
            color: #8b949e;
            border-top: 1px dashed var(--border);
            padding-top: 8px;
            margin-top: auto;
        }
        .db-link {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-top: 10px;
            color: var(--accent);
            text-decoration: none;
            font-size: 12px;
            font-weight: bold;
        }
        .db-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>🌌 Yu-Gi-Oh Story & Custom Card Engine</h1>
            <p style="color: #8b949e; font-size: 13px; margin-top: 4px;">Synchronized with Duelingbook & Live Duel Simulator</p>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <span class="badge">Simulator Port: 7911</span>
            <span class="badge" style="background: #1f6feb;">Discord Bot Ready</span>
        </div>
    </header>

    <input type="text" id="searchInput" class="search-bar" placeholder="🔍 Search cards by name, effect, or lore..." oninput="filterCards()">

    <div class="grid" id="cardsGrid">
        <p style="color: #8b949e;">Loading custom cards...</p>
    </div>

    <script>
        let allCards = [];
        async function loadCards() {
            const res = await fetch('/api/cards');
            allCards = await res.json();
            renderCards(allCards);
        }

        function renderCards(cards) {
            const grid = document.getElementById('cardsGrid');
            if (cards.length === 0) {
                grid.innerHTML = '<p style="color: #8b949e;">No matching cards found.</p>';
                return;
            }
            grid.innerHTML = cards.map(c => {
                const tagClass = 'tag-' + (c.card_type ? c.card_type.toLowerCase() : 'monster');
                const thumb = c.image_url || 'https://via.placeholder.com/60/21262d/8b949e?text=YGO';
                let stats = '';
                if (c.card_type === 'Monster') {
                    stats = `<span>${c.attribute || ''}</span> • <span>${c.monster_type || ''}</span> | Level/Rank/Link: <span>${c.level_or_rank_or_link || 0}</span> | ATK: <span>${c.atk}</span> / DEF: <span>${c.def !== null ? c.def : 'LINK'}</span>`;
                } else {
                    stats = `<span>${c.card_subtype} ${c.card_type}</span>`;
                }

                return `
                <div class="card">
                    <div>
                        <div class="card-header">
                            <img src="${thumb}" class="card-thumb" onerror="this.src='https://via.placeholder.com/60/21262d/8b949e?text=YGO'">
                            <div>
                                <div class="card-title">${c.name}</div>
                                <span class="tag ${tagClass}">${c.card_subtype} ${c.card_type}</span>
                            </div>
                        </div>
                        <div class="stats-box">${stats}</div>
                        <div class="effect-box">${c.effect_text}</div>
                    </div>
                    <div>
                        <div class="lore-box">"${c.lore_text || 'No lore recorded.'}"</div>
                        <a href="${c.duelingbook_url || '#'}" target="_blank" class="db-link">🔗 View on Duelingbook ↗</a>
                    </div>
                </div>
                `;
            }).join('');
        }

        function filterCards() {
            const q = document.getElementById('searchInput').value.toLowerCase();
            const filtered = allCards.filter(c => 
                (c.name && c.name.toLowerCase().includes(q)) ||
                (c.effect_text && c.effect_text.toLowerCase().includes(q)) ||
                (c.lore_text && c.lore_text.toLowerCase().includes(q))
            );
            renderCards(filtered);
        }

        loadCards();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
