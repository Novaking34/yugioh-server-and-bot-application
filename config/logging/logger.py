# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.logging.logger
Architecture: Cross-Subsystem Observability & Telemetry Infrastructure
Domain: Structured Multi-Sink Logging, Audit Ledgers & Distributed Tracing
Description:
    Authoritative Centralized Multi-Target Platform Logging Engine.
    Provides structured, thread-safe, multi-destination logging across all platform
    subsystems (Production Services, Development Tools, Distribution Packages, CLI).
    
Features:
    1. Multi-Sink Logging Architecture:
       - ANSI-Colorized Interactive Console Stream (stdout)
       - Service-Specific Rotating File Handlers (logs/<service>.log)
       - Chronological Combined Platform Event Timeline (logs/combined.log)
       - Centralized High-Severity Error Log (logs/errors.log, WARN/ERROR/CRITICAL)
       - Append-Only Operational Audit Ledger (logs/audit.jsonl)
    2. Dynamic Distributed Trace Correlation:
       - Automatically captures and injects active ContextVar trace_id into every
         log record without requiring callers to pass context explicitly.
    3. Machine-Readable JSON Mode:
       - Standard single-line JSON format for cloud observability collectors.
    4. Diagnostic Snapshot Integration:
       - Formats and emits 14-table diagnostic check results and failpoints.
    5. Operation Audit Boundary:
       - Context manager tracking execution duration, trace correlation, and failures.
    6. Disk Saturation Safeguards:
       - Size-based file rotation and backup retention to protect storage.

Invariants:
    - Thread-safe initialization protected by a re-entrant lock.
    - Zero stdout blocking in non-interactive/daemon environments.
    - Log directory and files created idempotently with permissive permissions.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import sys
import os
import time
import json
import logging
import threading
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

# Ensure repository root is in sys.path and prevent package shadowing
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_CONFIG_DIR)
if sys.path and sys.path[0] == _CONFIG_DIR:
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from config.paths import (
    LOGS_DIR,
    COMBINED_LOG_PATH,
    ERRORS_LOG_PATH,
    AUDIT_LOG_PATH,
)

# Global re-entrant lock for thread-safe logger configuration
_LOGGER_LOCK = threading.RLock()

# ANSI Terminal Color Escape Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
COLOR_DEBUG = "\033[36m"      # Cyan
COLOR_INFO = "\033[32m"       # Green
COLOR_WARNING = "\033[33m"    # Yellow
COLOR_ERROR = "\033[31m"      # Red
COLOR_CRITICAL = "\033[1;31m" # Bold Red
COLOR_SERVICE = "\033[35m"    # Magenta
COLOR_TIME = "\033[90m"       # Dark Gray
COLOR_TRACE = "\033[34m"      # Blue


# =============================================================================
# BLOCK 3: BODY BLOCK (Logging Formatters, Handlers & Audit Managers)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Console, Plain & JSON Telemetry Formatters
# -----------------------------------------------------------------------------
class ColoredConsoleFormatter(logging.Formatter):
    """Formats log records for interactive terminal consoles with ANSI colors."""

    LEVEL_COLORS = {
        logging.DEBUG: COLOR_DEBUG,
        logging.INFO: COLOR_INFO,
        logging.WARNING: COLOR_WARNING,
        logging.ERROR: COLOR_ERROR,
        logging.CRITICAL: COLOR_CRITICAL,
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        # Disable colors if stdout is not an interactive terminal or on unsupported environments
        self.use_colors = use_colors and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        service = getattr(record, "service", "SYSTEM")
        time_str = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        trace_id = getattr(record, "trace_id", None)

        if self.use_colors:
            lvl_color = self.LEVEL_COLORS.get(record.levelno, RESET)
            lvl_str = f"{lvl_color}{record.levelname:<7}{RESET}"
            svc_str = f"{COLOR_SERVICE}[{service}]{RESET}"
            trace_str = f" {COLOR_TRACE}[{trace_id}]{RESET}" if trace_id else ""
            msg_str = f"{record.getMessage()}"
            if record.levelno >= logging.ERROR:
                msg_str = f"{lvl_color}{msg_str}{RESET}"
            formatted = f"{COLOR_TIME}{time_str}{RESET} {lvl_str} {svc_str}{trace_str} {record.name}: {msg_str}"
        else:
            trace_str = f" [{trace_id}]" if trace_id else ""
            formatted = f"{time_str} [{record.levelname:<7}] [{service}]{trace_str} {record.name}: {record.getMessage()}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        return formatted


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for structured telemetry."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "service": getattr(record, "service", "SYSTEM"),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        # Include trace correlation identifier if available
        trace_id = getattr(record, "trace_id", None)
        if trace_id:
            log_entry["trace_id"] = trace_id

        # Include custom diagnostic fields if provided
        extra_fields = getattr(record, "diagnostic_context", None)
        if extra_fields and isinstance(extra_fields, dict):
            log_entry["context"] = extra_fields

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Context & Trace Correlation Filter
# -----------------------------------------------------------------------------
class ContextEnrichmentFilter(logging.Filter):
    """Injects default service identity and active distributed trace_id into log records."""

    def __init__(self, service: str = "SYSTEM"):
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "service"):
            record.service = self.service

        # Automatically bind active correlation ID from debugger tracer if not explicit
        if not getattr(record, "trace_id", None):
            try:
                from config.debugger.tracer import get_current_trace_id
                record.trace_id = get_current_trace_id()
            except (ImportError, Exception):
                record.trace_id = None
        return True


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Logger Configuration Factory & Multi-Sink Engine
# -----------------------------------------------------------------------------
def get_logger(name: str, service: str = "SYSTEM") -> logging.Logger:
    """Retrieves or configures a structured logger with console, service, combined, and error sinks.

    Args:
        name (str): Identifier for the logger (usually __name__).
        service (str): Service classification ('WEB', 'BOT', 'SIMULATOR', 'CDB', 'TOOLS', etc.)

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Fast-path: return existing logger if already initialized
    if getattr(logger, "_is_configured", False):
        return logger

    with _LOGGER_LOCK:
        # Re-check under lock to avoid race conditions during concurrent initialization
        if getattr(logger, "_is_configured", False):
            return logger

        # Resolve configured log level from settings or environment
        env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        try:
            from config.settings import settings
            env_level = settings.platform.log_level.upper()
        except Exception:
            pass

        level = getattr(logging, env_level, logging.INFO)
        logger.setLevel(level)

        # Determine formatting mode (text vs json)
        use_json = os.environ.get("LOG_FORMAT", "text").lower() == "json"

        # Ensure runtime log directory exists idempotently
        os.makedirs(LOGS_DIR, exist_ok=True)

        # Plain text formatter for disk files (avoids polluting disk with ANSI escape codes)
        plain_file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-7s] [%(service)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 1. Sink 1: Interactive Console Handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        if use_json:
            console_handler.setFormatter(StructuredJSONFormatter())
        else:
            console_handler.setFormatter(ColoredConsoleFormatter())
        logger.addHandler(console_handler)

        # 2. Sink 2: Service-Specific Rotating File Handler (logs/<service>.log)
        service_clean = service.lower().replace(" ", "_")
        service_log_path = os.path.join(LOGS_DIR, f"{service_clean}.log")
        try:
            service_file_handler = RotatingFileHandler(
                service_log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            service_file_handler.setLevel(level)
            if use_json:
                service_file_handler.setFormatter(StructuredJSONFormatter())
            else:
                service_file_handler.setFormatter(plain_file_formatter)
            logger.addHandler(service_file_handler)
        except (OSError, PermissionError):
            pass

        # 3. Sink 3: Master Combined Rotating File Handler (logs/combined.log)
        try:
            combined_file_handler = RotatingFileHandler(
                COMBINED_LOG_PATH, maxBytes=15 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            combined_file_handler.setLevel(level)
            if use_json:
                combined_file_handler.setFormatter(StructuredJSONFormatter())
            else:
                combined_file_handler.setFormatter(plain_file_formatter)
            logger.addHandler(combined_file_handler)
        except (OSError, PermissionError):
            pass

        # 4. Sink 4: Dedicated High-Severity Error Log (logs/errors.log)
        try:
            errors_file_handler = RotatingFileHandler(
                ERRORS_LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            errors_file_handler.setLevel(logging.WARNING)  # Captures WARNING, ERROR, CRITICAL
            if use_json:
                errors_file_handler.setFormatter(StructuredJSONFormatter())
            else:
                errors_file_handler.setFormatter(plain_file_formatter)
            logger.addHandler(errors_file_handler)
        except (OSError, PermissionError):
            pass

        # Attach context enrichment filter to automatically tag records with service and trace_id
        logger.addFilter(ContextEnrichmentFilter(service=service))
        logger._is_configured = True
        logger.propagate = False

        return logger


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Authoritative Audit Operation Context Manager & Ledger
# -----------------------------------------------------------------------------
def record_audit_event(
    operation: str,
    service: str,
    status: str,
    elapsed_sec: float,
    trace_id: Optional[str] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Appends an immutable structured audit event to logs/audit.jsonl.

    Args:
        operation (str): Name of the operational mutation.
        service (str): Originating subsystem name.
        status (str): Operational status ('SUCCESS' or 'FAILED').
        elapsed_sec (float): Duration of operation in seconds.
        trace_id (Optional[str]): Active distributed correlation trace ID.
        error (Optional[str]): Error message if status is 'FAILED'.
        metadata (Optional[Dict[str, Any]]): Arbitrary contextual payloads.
    """
    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "operation": operation,
        "service": service,
        "status": status,
        "elapsed_sec": round(elapsed_sec, 4),
        "trace_id": trace_id,
    }
    if error:
        event["error"] = error
    if metadata:
        event["metadata"] = metadata

    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except (OSError, PermissionError):
        pass


@contextmanager
def audit_operation(
    operation_name: str,
    service: str = "SYSTEM",
    logger: Optional[logging.Logger] = None,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Context manager to measure execution time, log initiation, and record audit ledger events.

    Usage:
        with audit_operation("Sync Expansions", service="SIMULATOR"):
            build_cdb()
    """
    # Resolve active correlation trace ID
    if not trace_id:
        try:
            from config.debugger.tracer import get_current_trace_id
            active_trace = get_current_trace_id()
        except Exception:
            active_trace = None
    else:
        active_trace = trace_id

    log = logger or get_logger(operation_name, service=service)
    start_time = time.perf_counter()
    prefix = f"[{active_trace}] " if active_trace else ""

    log.info(f"{prefix}▶ Initiating operation: '{operation_name}'...")
    try:
        yield log
        elapsed = time.perf_counter() - start_time
        log.info(f"{prefix}✔ Completed operation: '{operation_name}' ({elapsed:.3f}s)")
        record_audit_event(
            operation=operation_name,
            service=service,
            status="SUCCESS",
            elapsed_sec=elapsed,
            trace_id=active_trace,
            metadata=metadata
        )
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        log.error(f"{prefix}✘ FAILED operation: '{operation_name}' after {elapsed:.3f}s: {e}", exc_info=True)
        record_audit_event(
            operation=operation_name,
            service=service,
            status="FAILED",
            elapsed_sec=elapsed,
            trace_id=active_trace,
            error=str(e),
            metadata=metadata
        )
        raise


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Diagnostic Snapshot Logging Hook
# -----------------------------------------------------------------------------
def log_diagnostic_snapshot(diag_result: Any, service: str = "DIAG", logger: Optional[logging.Logger] = None) -> None:
    """Logs a DiagnosticResult instance from the platform debugger into the logger stream."""
    log = logger or get_logger("diagnostics", service=service)
    status = getattr(diag_result, "status", "UNKNOWN")
    name = getattr(diag_result, "name", "DiagnosticCheck")

    if status == "PASS":
        checked = getattr(diag_result, "checked_count", 0)
        log.info(f"[PASS] {name}: {checked} items audited successfully.")
    elif status == "WARN":
        warnings = getattr(diag_result, "warnings", [])
        log.warning(f"[WARN] {name}: {len(warnings)} warnings detected:")
        for w in warnings:
            log.warning(f"  ▲ {w}")
    else:
        failpoints = getattr(diag_result, "failpoints", [])
        log.error(f"[FAIL] {name}: {len(failpoints)} failpoints detected:")
        for fp in failpoints:
            log.error(f"  ✘ {fp}")
        suggestions = getattr(diag_result, "suggestions", [])
        for s in suggestions:
            log.info(f"  💡 Remediation: {s}")


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    "ColoredConsoleFormatter",
    "StructuredJSONFormatter",
    "ContextEnrichmentFilter",
    "get_logger",
    "audit_operation",
    "record_audit_event",
    "log_diagnostic_snapshot",
    "COMBINED_LOG_PATH",
    "ERRORS_LOG_PATH",
    "AUDIT_LOG_PATH",
]

if __name__ == "__main__":
    test_log = get_logger("config_logger_test", service="CONFIG")
    test_log.info("Centralized config logging subsystem initialized.")
    with audit_operation("Self Test", service="CONFIG"):
        time.sleep(0.02)
