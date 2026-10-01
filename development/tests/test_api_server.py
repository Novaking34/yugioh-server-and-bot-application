#!/usr/bin/env python3
"""
Unit and integration tests for story_database/api_server.py FastAPI endpoints.
"""

import pytest
import sys
import os
from starlette.testclient import TestClient

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "production", "main", "web"))

from api_server import app

client = TestClient(app)


def test_dashboard_endpoint():
    """Verify web catalog dashboard HTML response."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Yu-Gi-Oh!" in response.text


def test_list_cards_endpoint():
    """Verify card catalog API returns card entries."""
    response = client.get("/api/cards")
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list)
    if cards:
        first = cards[0]
        assert "id" in first
        assert "name" in first
        assert "card_type" in first


def test_card_search_query():
    """Verify search filter by keyword."""
    response = client.get("/api/cards?q=Starforged")
    assert response.status_code == 200
    cards = response.json()
    assert isinstance(cards, list)
    for c in cards:
        match = (
            "starforged" in c["name"].lower() or
            "starforged" in (c["effect_text"] or "").lower() or
            "starforged" in (c["lore_text"] or "").lower()
        )
        assert match


def test_lore_endpoint():
    """Verify lore chronicle endpoint."""
    response = client.get("/api/lore")
    assert response.status_code == 200
    data = response.json()
    assert "arcs" in data
    assert "factions" in data
    assert "characters" in data
    assert "duel_logs" in data


def test_decks_endpoint():
    """Verify story decks endpoint."""
    response = client.get("/api/decks")
    assert response.status_code == 200
    decks = response.json()
    assert isinstance(decks, list)
