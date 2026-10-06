#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.unit.server.test_dns_zone
Architecture: Hybrid Systems Engineering (Unit Testing Subsystem)
Domain: Server Infrastructure & Cloud Deployment / DNS Zone Management
Description:
    Unit test suite for the DNS Zone Management subsystem:
    1. Validates authoritative RFC 1035 zone file existence and structure.
    2. Tests dynamic zone file rendering across diverse domain and IP configurations.
    3. Asserts syntax and semantic validation catches missing headers or malformed IPs.
    4. Verifies settings-driven zone file synchronization.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import pytest
from pathlib import Path

from config.paths import DNS_ZONE_FILE_PATH, DNS_CONFIG_DIR, SERVER_PACKAGE_DIR
from packages.server.dns.zone_manager import (
    DNSZoneRecord,
    DEFAULT_ZONE_FILE_PATH,
    render_zone_content,
    validate_zone_content,
    sync_zone_file_from_settings,
    load_zone_file,
)
from config.settings import settings


# =============================================================================
# BLOCK 3: BODY BLOCK (Unit Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Authoritative Zone File Integrity
# -----------------------------------------------------------------------------
def test_authoritative_zone_file_integrity():
    """Verify that the packaged zone file exists, matches paths, and passes validation."""
    assert os.path.exists(DNS_ZONE_FILE_PATH)
    assert DNS_ZONE_FILE_PATH == DEFAULT_ZONE_FILE_PATH
    assert os.path.dirname(DNS_ZONE_FILE_PATH) == os.path.join(SERVER_PACKAGE_DIR, "dns")

    content = load_zone_file()
    assert len(content.strip()) > 0

    is_valid, errors = validate_zone_content(content)
    assert is_valid, f"Authoritative zone file validation failed: {errors}"
    assert len(errors) == 0


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Dynamic Zone Rendering
# -----------------------------------------------------------------------------
def test_render_zone_content_custom_parameters():
    """Verify that render_zone_content generates valid BIND RFC 1035 content."""
    origin = "custom-duels.org"
    tunnel = "11111111-2222-3333-4444-555555555555"
    ip = "192.168.1.100"
    duckdns = "custom-duels.duckdns.org"

    rendered = render_zone_content(
        origin=origin,
        ttl=1800,
        tunnel_id=tunnel,
        direct_ip=ip,
        duckdns_domain=duckdns,
    )

    # Directive checks
    assert f"$ORIGIN {origin}." in rendered
    assert "$TTL 1800" in rendered

    # Web Catalog CNAME checks
    assert f"@       IN  CNAME   {tunnel}.cfargotunnel.com." in rendered
    assert f"www     IN  CNAME   {tunnel}.cfargotunnel.com." in rendered

    # Game Simulator A record checks
    assert f"play    IN  A       {ip}" in rendered
    assert f"sim     IN  A       {ip}" in rendered

    # Validate output
    is_valid, errors = validate_zone_content(rendered)
    assert is_valid, f"Rendered content failed validation: {errors}"


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Validator Failpoint Detection
# -----------------------------------------------------------------------------
def test_validate_zone_content_detects_missing_origin():
    """Verify that missing $ORIGIN directive is rejected."""
    bad_content = "$TTL 3600\n@ IN CNAME tunnel.cfargotunnel.com.\nwww IN CNAME tunnel.cfargotunnel.com.\nplay IN A 1.2.3.4\nsim IN A 1.2.3.4\n"
    is_valid, errors = validate_zone_content(bad_content)
    assert not is_valid
    assert any("Missing mandatory $ORIGIN" in e for e in errors)


def test_validate_zone_content_detects_missing_ttl():
    """Verify that missing or invalid $TTL directive is rejected."""
    bad_content = "$ORIGIN example.com.\n@ IN CNAME tunnel.cfargotunnel.com.\nwww IN CNAME tunnel.cfargotunnel.com.\nplay IN A 1.2.3.4\nsim IN A 1.2.3.4\n"
    is_valid, errors = validate_zone_content(bad_content)
    assert not is_valid
    assert any("Missing mandatory $TTL" in e for e in errors)


def test_validate_zone_content_detects_malformed_ip():
    """Verify that out-of-bounds or invalid IP addresses in A records are caught."""
    bad_content = (
        "$ORIGIN example.com.\n$TTL 3600\n"
        "@ IN CNAME tunnel.cfargotunnel.com.\nwww IN CNAME tunnel.cfargotunnel.com.\n"
        "play IN A 999.300.200.100\nsim IN A 1.2.3.4\n"
    )
    is_valid, errors = validate_zone_content(bad_content)
    assert not is_valid
    assert any("IPv4 octet out of bounds" in e for e in errors)


def test_validate_zone_content_detects_malformed_tunnel():
    """Verify that malformed Cloudflare tunnel CNAME targets are caught."""
    bad_content = (
        "$ORIGIN example.com.\n$TTL 3600\n"
        "@ IN CNAME invalid_target!@#.cfargotunnel.com.\nwww IN CNAME tunnel.cfargotunnel.com.\n"
        "play IN A 1.2.3.4\nsim IN A 1.2.3.4\n"
    )
    is_valid, errors = validate_zone_content(bad_content)
    assert not is_valid
    assert any("Malformed Cloudflare Argo Tunnel target" in e for e in errors)


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Settings-Driven Synchronization
# -----------------------------------------------------------------------------
def test_sync_zone_file_from_settings(tmp_path: Path):
    """Verify that sync_zone_file_from_settings writes a valid file matching active settings."""
    target_zone = tmp_path / "test_synced.zone"
    success = sync_zone_file_from_settings(str(target_zone))

    assert success is True
    assert target_zone.exists()

    content = target_zone.read_text(encoding="utf-8")
    assert f"$ORIGIN {settings.network.public_domain}." in content
    assert f"@       IN  CNAME   {settings.cloudflare.tunnel_id}.cfargotunnel.com." in content

    is_valid, errors = validate_zone_content(content)
    assert is_valid, f"Synced file failed validation: {errors}"


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest)
# =============================================================================

__all__ = [
    "test_authoritative_zone_file_integrity",
    "test_render_zone_content_custom_parameters",
    "test_validate_zone_content_detects_missing_origin",
    "test_validate_zone_content_detects_missing_ttl",
    "test_validate_zone_content_detects_malformed_ip",
    "test_validate_zone_content_detects_malformed_tunnel",
    "test_sync_zone_file_from_settings",
]
