# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.debugger.tracer
Description:
    Authoritative Diagnostic Tracing, Correlation ID Engine & Performance Traps.
    Provides execution context propagation across asynchronous Discord tasks,
    ASGI HTTP web requests, and background database / compilation pipelines:
    - Thread-safe and task-local ContextVar correlation IDs (`trace_id`)
    - Contextual timing spans measuring microsecond latencies
    - Automatic slow-query traps flagging SQL operations exceeding configured thresholds
    - Seamless telemetry coupling with `config.logging`
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import time
import uuid
import logging
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator

# Ensure repository root is in sys.path
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_CONFIG_DIR)
if sys.path and sys.path[0] == _CONFIG_DIR:
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from config.settings import settings
from config.logging import get_logger

# =============================================================================
# BLOCK 3: BODY BLOCK (Tracing & Correlation Engine)
# =============================================================================

# ContextVar storing active correlation ID for the current async task / thread
_ACTIVE_TRACE_ID: ContextVar[Optional[str]] = ContextVar("active_trace_id", default=None)


# -----------------------------------------------------------------------------
# Sub-Block 3.1: Correlation ID Resolution & Propagation
# -----------------------------------------------------------------------------
def get_current_trace_id() -> str:
    """Retrieve the current task-local correlation trace ID, or create one if absent."""
    tid = _ACTIVE_TRACE_ID.get()
    if not tid:
        tid = f"trc-{uuid.uuid4().hex[:12]}"
        _ACTIVE_TRACE_ID.set(tid)
    return tid


def set_trace_id(custom_id: Optional[str] = None) -> str:
    """Explicitly assign or generate a new correlation trace ID for the active scope."""
    tid = custom_id or f"trc-{uuid.uuid4().hex[:12]}"
    _ACTIVE_TRACE_ID.set(tid)
    return tid


def new_trace_id() -> str:
    """Generate a clean 12-character hexadecimal correlation trace ID."""
    return f"trc-{uuid.uuid4().hex[:12]}"


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Execution Timing Spans & Performance Telemetry
# -----------------------------------------------------------------------------
@contextmanager
def trace_span(
    span_name: str,
    service: str = "SYSTEM",
    logger: Optional[logging.Logger] = None,
    custom_trace_id: Optional[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """Context manager measuring execution time with correlation ID and slow-operation warnings.

    Usage:
        with trace_span("Render Deck Canvas", service="BOT") as span:
            canvas.render(...)
            span["card_count"] = 40
    """
    tid = custom_trace_id or get_current_trace_id()
    _ACTIVE_TRACE_ID.set(tid)
    log = logger or get_logger(span_name, service=service)
    start_time = time.perf_counter()

    span_data: Dict[str, Any] = {
        "span_name": span_name,
        "trace_id": tid,
        "service": service,
        "start_time": start_time,
    }

    log.debug(f"[{tid}] ⏱ Begin span: '{span_name}'")
    try:
        yield span_data
        duration = time.perf_counter() - start_time
        span_data["duration_seconds"] = duration
        span_data["duration_ms"] = round(duration * 1000.0, 2)

        # Flag slow operations exceeding configured debug threshold
        threshold_ms = settings.debug.slow_query_ms
        if span_data["duration_ms"] > threshold_ms:
            log.warning(
                f"[{tid}] ⚠ SLOW SPAN: '{span_name}' took {span_data['duration_ms']:.2f}ms "
                f"(threshold: {threshold_ms:.1f}ms)"
            )
        else:
            log.debug(f"[{tid}] ✔ Finished span: '{span_name}' ({span_data['duration_ms']:.2f}ms)")
    except Exception as e:
        duration = time.perf_counter() - start_time
        span_data["duration_seconds"] = duration
        span_data["duration_ms"] = round(duration * 1000.0, 2)
        span_data["error"] = str(e)
        log.error(f"[{tid}] ✘ Span '{span_name}' failed after {span_data['duration_ms']:.2f}ms: {e}", exc_info=True)
        raise


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Database Slow-Query Trap
# -----------------------------------------------------------------------------
def measure_slow_query(
    sql_statement: str,
    duration_ms: float,
    service: str = "DB",
    logger: Optional[logging.Logger] = None
) -> None:
    """Evaluates SQL query duration against DebugConfig threshold and emits warning on breach."""
    threshold = settings.debug.slow_query_ms
    if duration_ms > threshold:
        tid = get_current_trace_id()
        log = logger or get_logger("sql_slow_query", service=service)
        clean_sql = " ".join(sql_statement.strip().split())
        if len(clean_sql) > 200:
            clean_sql = clean_sql[:197] + "..."
        log.warning(
            f"[{tid}] ⚠ SLOW QUERY ({duration_ms:.2f}ms > {threshold:.1f}ms): {clean_sql}"
        )


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    "get_current_trace_id",
    "set_trace_id",
    "new_trace_id",
    "trace_span",
    "measure_slow_query",
]

if __name__ == "__main__":
    test_id = set_trace_id()
    print(f"Tracer initialized with active ID: {test_id}")
    with trace_span("Self Test Span", service="DEBUG"):
        time.sleep(0.01)
