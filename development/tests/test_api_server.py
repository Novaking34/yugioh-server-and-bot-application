#!/usr/bin/env python3
"""
=============================================================================
FastAPI Web Catalog & REST API Diagnostic Test Suite
=============================================================================
Asserts:
1. HTML web catalog and lore chronicle dashboard responses.
2. REST API endpoints for card listing, filtering, and single-card lookups.
3. Resilience against hostile search queries and SQL injection strings.
4. Correct 404 responses on non-existent card and deck queries.
5. Client expansion manifest format and binary CDB download headers.
=============================================================================
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "production", "main", "web"))

from api_server import app

client = TestClient(app)


# =============================================================================
# 1. Web Dashboard & Static HTML Tests
# =============================================================================

def test_dashboard_endpoint():
    """Verify web catalog dashboard HTML response and content headers."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert "text/html" in response.headers.get("content-type", "")
    assert "Yu-Gi-Oh!" in response.text


# =============================================================================
# 2. Card Catalog & Search API Tests
# =============================================================================

def test_list_cards_endpoint():
    """Verify card catalog API returns a valid list of card dictionaries."""
    response = client.get("/api/cards")
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list), f"Expected list of cards, got {type(cards)}"

    if cards:
        sample = cards[0]
        required_fields = ["id", "name", "card_type"]
        for field in required_fields:
            assert field in sample, f"Card object missing mandatory field '{field}'!"


def test_card_search_query_filtering():
    """Verify case-insensitive search queries filter results accurately."""
    response = client.get("/api/cards?q=Starforged")
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list)

    for c in cards:
        match = (
            "starforged" in c["name"].lower() or
            "starforged" in (c.get("effect_text") or "").lower() or
            "starforged" in (c.get("lore_snippet") or "").lower()
        )
        assert match, f"Search result '{c['name']}' did not match keyword 'Starforged'!"


def test_card_search_sql_injection_defense():
    """Verify that SQL injection strings in search queries are safely parameterized."""
    hostile_queries = [
        "' OR 1=1 --",
        "'; DROP TABLE custom_cards; --",
        '" OR "a"="a',
        "<script>alert(1)</script>"
    ]
    for hq in hostile_queries:
        response = client.get(f"/api/cards?q={hq}")
        assert response.status_code == 200, f"Hostile query '{hq}' caused HTTP error {response.status_code}!"
        # In SQLite parameterized search, hostile injection strings should find 0 or safe matches
        assert isinstance(response.json(), list)


def test_single_card_endpoint_failpoint():
    """Verify that requesting a non-existent card ID returns a clean 404 response."""
    non_existent_id = 99999999
    response = client.get(f"/api/cards/{non_existent_id}")
    assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}"
    error_data = response.json()
    assert "detail" in error_data, "404 response missing 'detail' message!"


# =============================================================================
# 3. Lore & Story Worldbuilding Endpoint Tests
# =============================================================================

def test_lore_endpoint_structure():
    """Verify that /api/lore serves all overarching worldbuilding datasets."""
    response = client.get("/api/lore")
    assert response.status_code == 200
    data = response.json()

    expected_keys = ["arcs", "factions", "characters", "duel_logs"]
    for k in expected_keys:
        assert k in data, f"Lore endpoint response missing '{k}' key!"
        assert isinstance(data[k], list), f"Expected list for '{k}', got {type(data[k])}"


# =============================================================================
# 4. Decks & Simulator Synchronization Endpoint Tests
# =============================================================================

def test_decks_endpoint():
    """Verify story decks catalog endpoint."""
    response = client.get("/api/decks")
    assert response.status_code == 200
    decks = response.json()
    assert isinstance(decks, list)


def test_deck_download_failpoint():
    """Verify that downloading a non-existent deck ID returns an informative 404."""
    non_existent_deck = 88888
    response = client.get(f"/api/decks/{non_existent_deck}/download")
    assert response.status_code == 404


def test_shared_manifest_endpoint():
    """Verify client expansion sync manifest schema and essential keys."""
    response = client.get("/api/shared/manifest")
    assert response.status_code == 200
    data = response.json()

    manifest_keys = ["version", "has_cdb", "scripts_count", "scripts_zip_url"]
    for key in manifest_keys:
        assert key in data, f"Sync manifest missing key '{key}'!"


def test_shared_cdb_endpoint():
    """Verify downloading custom_cards.cdb binary payload."""
    response = client.get("/api/shared/cdb")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        assert "application/octet-stream" in content_type or "application/x-sqlite3" in content_type
