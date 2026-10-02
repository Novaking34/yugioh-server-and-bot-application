#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Centralized Production Logging Subsystem
=============================================================================
Provides a structured, thread-safe, multi-destination logging architecture
for all host runtime services:
- Web Catalog & REST API (`WEB`)
- Live Duel Simulator container orchestrator (`SIMULATOR`)
- Discord Story & Duel Bot (`BOT`)
- Desktop GUI Control Panel (`GUI`)
- Platform Setup Wizard (`WIZARD`)
- Diagnostic & Debugging Suite (`DIAG`)

Features:
1. Multi-Target Logging: Colorized stdout + rotating log files in `logs/`.
2. Machine-Readable JSON Mode: Structured logs for log forwarders and aggregators.
3. Diagnostic Hook: Automatically records failpoints from `PlatformDiagnostics`.
4. Audit Context Manager: Measures execution times and logs operation outcomes.
5. Disk Protection: Size-based rotation (10MB max, 5 backups) preventing disk exhaustion.
=============================================================================
"""

import sys
import os
import time
import json
import logging
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import LOGS_DIR

# ANSI Terminal Color Escape Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
COLOR_DEBUG = "\033[36m"     # Cyan
COLOR_INFO = "\033[32m"      # Green
COLOR_WARNING = "\033[33m"   # Yellow
COLOR_ERROR = "\033[31m"     # Red
COLOR_CRITICAL = "\033[1;31m"# Bold Red
COLOR_SERVICE = "\033[35m"   # Magenta
COLOR_TIME = "\033[90m"      # Dark Gray


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

        if self.use_colors:
            lvl_color = self.LEVEL_COLORS.get(record.levelno, RESET)
            lvl_str = f"{lvl_color}{record.levelname:<7}{RESET}"
            svc_str = f"{COLOR_SERVICE}[{service}]{RESET}"
            msg_str = f"{record.getMessage()}"
            if record.levelno >= logging.ERROR:
                msg_str = f"{lvl_color}{msg_str}{RESET}"
            formatted = f"{COLOR_TIME}{time_str}{RESET} {lvl_str} {svc_str} {record.name}: {msg_str}"
        else:
            formatted = f"{time_str} [{record.levelname:<7}] [{service}] {record.name}: {record.getMessage()}"

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

        # Include custom diagnostic fields if provided
        extra_fields = getattr(record, "diagnostic_context", None)
        if extra_fields and isinstance(extra_fields, dict):
            log_entry["context"] = extra_fields

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_logger(name: str, service: str = "SYSTEM") -> logging.Logger:
    """
    Retrieves or configures a structured logger with console and rotating file handlers.

    Args:
        name (str): Identifier for the logger (usually __name__).
        service (str): Service classification ('WEB', 'BOT', 'SIMULATOR', 'GUI', 'WIZARD', 'DIAG').

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # If already configured with our handlers, just update the default service filter
    if getattr(logger, "_is_configured", False):
        return logger

    # Resolve configured log level from environment
    env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, env_level, logging.INFO)
    logger.setLevel(level)

    # Determine formatting mode (text vs json)
    use_json = os.environ.get("LOG_FORMAT", "text").lower() == "json"

    # Ensure log directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    if use_json:
        console_handler.setFormatter(StructuredJSONFormatter())
    else:
        console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)

    # 2. Service-Specific Rotating File Handler
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
            # Plain formatting without ANSI escape codes for disk files
            plain_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)-7s] [%(service)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            service_file_handler.setFormatter(plain_formatter)
        logger.addHandler(service_file_handler)
    except (OSError, PermissionError):
        pass  # Fall back to console logging if disk is read-only

    # 3. Master Combined Rotating File Handler
    combined_log_path = os.path.join(LOGS_DIR, "combined.log")
    try:
        combined_file_handler = RotatingFileHandler(
            combined_log_path, maxBytes=15 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        combined_file_handler.setLevel(level)
        if use_json:
            combined_file_handler.setFormatter(StructuredJSONFormatter())
        else:
            combined_file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)-7s] [%(service)s] %(name)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
        logger.addHandler(combined_file_handler)
    except (OSError, PermissionError):
        pass

    # Inject service attribute on all log records via a filter
    class ServiceFilter(logging.Filter):
        def filter(self, record):
            if not hasattr(record, "service"):
                record.service = service
            return True

    logger.addFilter(ServiceFilter())
    logger._is_configured = True
    logger.propagate = False

    return logger


@contextmanager
def audit_operation(operation_name: str, service: str = "SYSTEM", logger: Optional[logging.Logger] = None):
    """
    Context manager to measure execution time, log initiation, and report failpoints on exception.

    Usage:
        with audit_operation("Sync Expansions", service="SIMULATOR"):
            build_cdb()
    """
    log = logger or get_logger(operation_name, service=service)
    start_time = time.perf_counter()
    log.info(f"▶ Initiating operation: '{operation_name}'...")
    try:
        yield log
        elapsed = time.perf_counter() - start_time
        log.info(f"✔ Completed operation: '{operation_name}' ({elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        log.error(f"✘ FAILED operation: '{operation_name}' after {elapsed:.3f}s: {e}", exc_info=True)
        raise


def log_diagnostic_snapshot(diag_result, service: str = "DIAG", logger: Optional[logging.Logger] = None):
    """
    Logs a DiagnosticResult instance from debug_diagnostics.py into the logger stream.
    """
    log = logger or get_logger("diagnostics", service=service)
    status = diag_result.status
    name = diag_result.name

    if status == "PASS":
        log.info(f"[PASS] {name}: {diag_result.checked_count} items audited successfully.")
    elif status == "WARN":
        log.warning(f"[WARN] {name}: {len(diag_result.warnings)} warnings detected:")
        for w in diag_result.warnings:
            log.warning(f"  ▲ {w}")
    else:
        log.error(f"[FAIL] {name}: {len(diag_result.failpoints)} failpoints detected:")
        for fp in diag_result.failpoints:
            log.error(f"  ✘ {fp}")
        for s in diag_result.suggestions:
            log.info(f"  💡 Remediation: {s}")


if __name__ == "__main__":
    test_log = get_logger("logger_test", service="TEST")
    test_log.debug("This is a debug message.")
    test_log.info("Production logger initialized successfully.")
    test_log.warning("This is a warning check.")
    test_log.error("This is an error check.")

    with audit_operation("Sample Task", service="TEST"):
        time.sleep(0.05)
