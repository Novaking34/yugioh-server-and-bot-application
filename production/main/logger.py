#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: production.main.logger
Architecture: Production Host Service Observability Bridge
Domain: Logging Interface & Backward-Compatibility Facade
Description:
    Authoritative forwarder re-exporting the centralized platform logging subsystem
    from `config.logging` into the production host namespace.
    
    Guarantees backward compatibility for existing production services:
    - Web Catalog & REST API (production/main/web/)
    - Discord Story & Duel Bot (production/main/discord_bot/)
    - Platform GUI & Setup Wizard (production/main/gui/)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.logging import (
    get_logger,
    audit_operation,
    record_audit_event,
    log_diagnostic_snapshot,
    ColoredConsoleFormatter,
    StructuredJSONFormatter,
    ContextEnrichmentFilter,
    COMBINED_LOG_PATH,
    ERRORS_LOG_PATH,
    AUDIT_LOG_PATH,
    get_logging_paths,
)


# =============================================================================
# BLOCK 3: BODY BLOCK (Bridge Interfaces & Invariants)
# =============================================================================
# Re-exported directly from config.logging to maintain a single source of truth.


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    "get_logger",
    "audit_operation",
    "record_audit_event",
    "log_diagnostic_snapshot",
    "ColoredConsoleFormatter",
    "StructuredJSONFormatter",
    "ContextEnrichmentFilter",
    "COMBINED_LOG_PATH",
    "ERRORS_LOG_PATH",
    "AUDIT_LOG_PATH",
    "get_logging_paths",
]
