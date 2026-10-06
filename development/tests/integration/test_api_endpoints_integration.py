#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.integration.test_api_endpoints_integration
Architecture: Hybrid Systems Engineering (Integration Testing Subsystem)
Domain: Web Portal / FastAPI HTTP Endpoints Integration
Description:
    Integration test suite verifying the live FastAPI web portal routes,
    status responses, catalog listing, search queries, and database connectivity.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import pytest
from fastapi.testclient import TestClient

from production.main.web.api_server import app


# =============================================================================
# BLOCK 3: BODY BLOCK (Integration Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Live API Route Responses
# -----------------------------------------------------------------------------
def test_api_status_and_health_integration():
    """Verifies that /api/status and /api/health return 200 OK."""
    client = TestClient(app)
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data

    resp_health = client.get("/api/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] in ("healthy", "degraded")


def test_api_cards_and_decks_listing_integration():
    """Verifies that /api/cards and /api/decks return populated data."""
    client = TestClient(app)

    # 1. Cards listing
    resp_cards = client.get("/api/cards")
    assert resp_cards.status_code == 200
    cards_data = resp_cards.json()
    assert isinstance(cards_data, list)
    assert len(cards_data) > 0

    # 2. Decks listing
    resp_decks = client.get("/api/decks")
    assert resp_decks.status_code == 200
    decks_data = resp_decks.json()
    assert isinstance(decks_data, list)
    assert len(decks_data) > 0


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_api_status_and_health_integration",
    "test_api_cards_and_decks_listing_integration",
]
