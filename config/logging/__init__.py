# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.logging
Architecture: Centralized Multi-Sink Observability & Telemetry Subsystem
Domain: Logging Engine, Distributed Tracing Correlation, Audit Trails & Log Inspector
Description:
    Authoritative centralized logging package for the Yu-Gi-Oh! platform.
    Provides unified, thread-safe, multi-destination log routing across all
    services (FastAPI web catalog, Discord bot, ocgcore live simulator, tools).

Sinks Provided:
    1. Interactive Console (stdout with ANSI color formatting & trace IDs)
    2. Service-Specific Logs (logs/<service>.log, e.g. web.log, bot.log)
    3. Master Combined Timeline (logs/combined.log)
    4. Dedicated High-Severity Error Sink (logs/errors.log)
    5. Immutable Structured Audit Ledger (logs/audit.jsonl)

Invariants:
    - Thread-safe initialization protected by a re-entrant lock.
    - Zero interference with Python standard library `logging` module.
    - Automatic injection of active ContextVar `trace_id` into all log records.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys

# Ensure repository root is in sys.path and prevent package shadowing
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_CONFIG_DIR)
if sys.path and sys.path[0] == _CONFIG_DIR:
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from .logger import (
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
)

from .log_tool import (
    get_log_stats,
    tail_log,
    query_logs,
    query_audit_logs,
    clean_logs,
)


# =============================================================================
# BLOCK 3: BODY BLOCK (Conveniences & Subsystem Properties)
# =============================================================================

def get_logging_paths() -> dict:
    """Returns absolute paths to all authoritative platform log sinks."""
    return {
        "combined": COMBINED_LOG_PATH,
        "errors": ERRORS_LOG_PATH,
        "audit": AUDIT_LOG_PATH,
    }


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    # Core Logging Engine
    "get_logger",
    "audit_operation",
    "record_audit_event",
    "log_diagnostic_snapshot",
    "ColoredConsoleFormatter",
    "StructuredJSONFormatter",
    "ContextEnrichmentFilter",
    # Authoritative Sink Paths
    "COMBINED_LOG_PATH",
    "ERRORS_LOG_PATH",
    "AUDIT_LOG_PATH",
    "get_logging_paths",
    # Telemetry & Audit CLI Utilities
    "get_log_stats",
    "tail_log",
    "query_logs",
    "query_audit_logs",
    "clean_logs",
]
