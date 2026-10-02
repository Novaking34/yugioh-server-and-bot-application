"""
=============================================================================
Yu-Gi-Oh! Platform - Centralized Platform Logging Package
=============================================================================
Exports:
- `get_logger`: Retrieve or create structured, multi-target logger.
- `audit_operation`: Context manager measuring elapsed time and logging failures.
- `log_diagnostic_snapshot`: Log DiagnosticResult instances into log stream.
- `ColoredConsoleFormatter`: ANSI terminal log formatter.
- `StructuredJSONFormatter`: Single-line JSON log formatter for telemetry.
=============================================================================
"""

from .logger import (
    get_logger,
    audit_operation,
    log_diagnostic_snapshot,
    ColoredConsoleFormatter,
    StructuredJSONFormatter,
)
from .log_tool import (
    get_log_stats,
    tail_log,
    query_logs,
    clean_logs,
)

__all__ = [
    "get_logger",
    "audit_operation",
    "log_diagnostic_snapshot",
    "ColoredConsoleFormatter",
    "StructuredJSONFormatter",
    "get_log_stats",
    "tail_log",
    "query_logs",
    "clean_logs",
]
