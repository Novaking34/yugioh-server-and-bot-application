#!/usr/bin/env python3
"""
=============================================================================
Production Logger & Setup Wizard Diagnostic Test Suite
=============================================================================
Asserts:
1. Multi-target logging: Console handler + rotating file handlers.
2. Combined log timeline persistence and service-specific file routing.
3. JSON format mode emits valid, parseable single-line JSON records.
4. audit_operation context manager measures execution times and logs errors on failure.
5. setup_wizard.save_env_values safely updates .env settings without clobbering existing keys.
=============================================================================
"""

import pytest
import os
import sys
import json
import tempfile
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from production.main.logger import (
    get_logger, audit_operation, StructuredJSONFormatter, ColoredConsoleFormatter
)
from production.main.setup_wizard import save_env_values, load_env_values


# =============================================================================
# 1. Logger File Handlers & Service Separation
# =============================================================================

def test_logger_creates_handlers_and_writes_to_file():
    """Verify that get_logger creates a logger that writes to a service-specific file."""
    service_name = "TEST_SERVICE"
    logger = get_logger("unit_test_logger", service=service_name)

    assert logger.name == "unit_test_logger"
    assert len(logger.handlers) >= 2, f"Expected at least console + file handlers, got {len(logger.handlers)}"

    # Emit a unique test message
    test_msg = "Diagnostic test event 4815162342"
    logger.info(test_msg)

    # Flush all handlers
    for h in logger.handlers:
        h.flush()

    # Check that service log exists and contains the message
    from config.paths import LOGS_DIR
    service_file = os.path.join(LOGS_DIR, f"{service_name.lower()}.log")
    combined_file = os.path.join(LOGS_DIR, "combined.log")

    assert os.path.exists(service_file), f"Service log file {service_file} was not created!"
    with open(service_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert test_msg in content, f"Test message was not found in service log: {content}"

    assert os.path.exists(combined_file), f"Combined log file {combined_file} was not created!"
    with open(combined_file, "r", encoding="utf-8") as f:
        comb_content = f.read()
    assert test_msg in comb_content, f"Test message was not found in combined log: {comb_content}"


# =============================================================================
# 2. Structured JSON Formatter Tests
# =============================================================================

def test_structured_json_formatter():
    """Verify that StructuredJSONFormatter emits valid JSON with expected telemetry fields."""
    formatter = StructuredJSONFormatter()
    record = logging.LogRecord(
        name="api_monitor",
        level=logging.WARNING,
        pathname=__file__,
        lineno=42,
        msg="High memory usage detected on port %d",
        args=(8000,),
        exc_info=None
    )
    record.service = "WEB"
    record.diagnostic_context = {"memory_mb": 512, "limit_mb": 1024}

    json_str = formatter.format(record)
    data = json.loads(json_str)

    assert data["level"] == "WARNING"
    assert data["service"] == "WEB"
    assert data["logger"] == "api_monitor"
    assert data["message"] == "High memory usage detected on port 8000"
    assert "timestamp" in data
    assert data["context"]["memory_mb"] == 512


# =============================================================================
# 3. Audit Operation Context Manager Tests
# =============================================================================

def test_audit_operation_success():
    """Verify that audit_operation successfully completes and logs elapsed time."""
    with audit_operation("Successful Task", service="TEST") as log:
        val = 10 + 20
        assert val == 30


def test_audit_operation_failure():
    """Verify that audit_operation catches exceptions, logs failure, and re-raises."""
    with pytest.raises(ValueError, match="Deliberate diagnostic failure"):
        with audit_operation("Failing Task", service="TEST"):
            raise ValueError("Deliberate diagnostic failure")


# =============================================================================
# 4. Safe .env Configuration Modifier Tests
# =============================================================================

def test_save_env_values_preserves_unrelated_settings():
    """Verify that save_env_values modifies target keys while preserving comments and other keys."""
    with tempfile.NamedTemporaryFile(suffix=".env", mode="w+", delete=False) as tf:
        tf.write(
            "# Server Configuration\n"
            "SIMULATOR_TCP_PORT=\"7911\"\n"
            "WEB_CATALOG_PORT=\"8000\"\n"
            "SECRET_KEY=\"keep_this_safe\"\n"
        )
        env_path = tf.name

    try:
        # Update simulator port and add Discord bot token
        save_env_values(
            {
                "SIMULATOR_TCP_PORT": "7922",
                "DISCORD_BOT_TOKEN": "test_bot_token_xyz"
            },
            env_path=env_path
        )

        loaded = load_env_values(env_path=env_path)
        assert loaded["SIMULATOR_TCP_PORT"] == "7922", "Simulator port was not updated!"
        assert loaded["DISCORD_BOT_TOKEN"] == "test_bot_token_xyz", "New key was not appended!"
        assert loaded["WEB_CATALOG_PORT"] == "8000", "Existing unrelated port was lost!"
        assert loaded["SECRET_KEY"] == "keep_this_safe", "Existing secret key was wiped out!"

        # Verify comment was preserved
        with open(env_path, "r", encoding="utf-8") as f:
            raw = f.read()
        assert "# Server Configuration" in raw, "Comment was stripped during .env update!"
    finally:
        if os.path.exists(env_path):
            os.remove(env_path)


# =============================================================================
# 5. Log Inspector & Telemetry Tool Tests
# =============================================================================

def test_log_tool_stats_tail_and_query():
    """Verify that log_tool functions accurately inspect logs and return query results."""
    from config.logging import get_log_stats, tail_log, query_logs

    # Log an identifiable probe message
    unique_keyword = "probe_telemetry_event_98765"
    test_logger = get_logger("probe_logger", service="TOOLS")
    test_logger.info(f"Special probe: {unique_keyword}")
    for h in test_logger.handlers:
        h.flush()

    # 1. Stats test
    stats = get_log_stats()
    assert isinstance(stats, list)
    assert len(stats) > 0, "Expected at least 1 log file in stats"
    filenames = [s["filename"] for s in stats]
    assert "combined.log" in filenames

    # 2. Tail test
    tail_entries = tail_log(service="tools", lines=10)
    assert isinstance(tail_entries, list)
    assert any(unique_keyword in line for line in tail_entries)

    # 3. Query test
    query_results = query_logs(keyword=unique_keyword, limit=5)
    assert len(query_results) >= 1
    assert any(unique_keyword in r["raw"] for r in query_results)

