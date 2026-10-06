#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Package: packages.server.dns
Architecture: Hybrid Systems Engineering (Server Infrastructure & Deployment)
Subsystem: DNS Zone Management
"""

from .zone_manager import (
    DNSZoneRecord,
    DEFAULT_ZONE_FILE_PATH,
    render_zone_content,
    validate_zone_content,
    sync_zone_file_from_settings,
    load_zone_file,
)

__all__ = [
    "DNSZoneRecord",
    "DEFAULT_ZONE_FILE_PATH",
    "render_zone_content",
    "validate_zone_content",
    "sync_zone_file_from_settings",
    "load_zone_file",
]
