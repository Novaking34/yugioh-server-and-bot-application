# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.debugger
Description:
    Centralized Diagnostic Debugging and Distributed Execution Tracing Subsystem.
    Provides deep observability, slow query detection, automated post-mortem crash
    snapshots, and full 14-table database integrity auditing across the platform.

Architecture & Capabilities:
    1. Execution Tracing (config.debugger.tracer):
       - Context-local correlation IDs (UUID4) propagated across async tasks and threads.
       - Performance latency timing via context manager (trace_span).
       - Slow SQL query interceptor traps against configurable thresholds.
    2. System Diagnostics (config.debugger.diagnostics):
       - Full 14-table relational integrity checks and FTS5 search index synchronization.
       - Card metadata bitmask assertions (types, attributes, races, Link compass, Pendulum scales).
       - CDB binary database 1:1 parity and record count audits.
       - Lua effect script syntax validation and ocgcore convention checks.
       - Story character deck format and passcode resolution.
       - Local card artwork availability and byte health verification.
       - Automated post-mortem crash snapshots (logs/debug_snapshots/).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

from typing import Optional

from config.debugger.tracer import (
    get_current_trace_id,
    set_trace_id,
    new_trace_id,
    trace_span,
    measure_slow_query,
)

from config.debugger.diagnostics import (
    DiagnosticResult,
    PlatformDiagnostics,
    take_debug_snapshot,
    prune_debug_snapshots,
    print_diagnostic_report,
)

# =============================================================================
# BLOCK 3: BODY BLOCK (Subsystem Conveniences & Orchestration)
# =============================================================================

def run_diagnostics(
    verbose: bool = True,
    include_tests: bool = False,
    tier: Optional[str] = None,
    data_mode: str = "live"
) -> int:
    """
    Convenience orchestrator to run all platform diagnostic audits
    and print the standardized terminal report. Returns 0 on success, 1 on failure.
    
    Args:
        verbose (bool): Whether to format and print terminal report to stdout.
        include_tests (bool): If True, also executes the automated test suite.
        tier (Optional[str]): Target test taxonomy tier ('unit', 'integration', 'functional').
        data_mode (str): Data source strategy ('live', 'sample', or 'both').
        
    Returns:
        int: 0 if all diagnostics pass, 1 if any failpoints are detected.
    """
    diag = PlatformDiagnostics()
    results = diag.run_all(include_tests=include_tests, tier=tier, data_mode=data_mode)
    if verbose:
        return print_diagnostic_report(results)
    return 1 if any(r.status == "FAIL" for r in results) else 0


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    # Execution Tracing & Correlation
    "get_current_trace_id",
    "set_trace_id",
    "new_trace_id",
    "trace_span",
    "measure_slow_query",
    # System Diagnostics & Audits
    "DiagnosticResult",
    "PlatformDiagnostics",
    "take_debug_snapshot",
    "prune_debug_snapshots",
    "print_diagnostic_report",
    "run_diagnostics",
]
