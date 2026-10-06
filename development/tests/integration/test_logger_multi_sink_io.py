#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tests.integration.test_logger_multi_sink_io
Architecture: Hybrid Systems Engineering (Integration Testing Subsystem)
Domain: Logging & Telemetry / File Sinks & Audit Ledger IO
Description:
    Integration test suite verifying the production logging multi-sink architecture,
    file rotation handlers, and immutable audit trail persistence in `audit.jsonl`.
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import json
import logging
import pytest

from config.logging import get_logger, audit_operation, query_audit_logs
from config.paths import LOGS_DIR


# =============================================================================
# BLOCK 3: BODY BLOCK (Integration Tests)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Multi-Sink File Persistence
# -----------------------------------------------------------------------------
def test_logger_multi_sink_file_persistence():
    """Verifies that get_logger writes to disk and creates appropriate log files."""
    test_logger = get_logger("integration_test_service")
    assert test_logger is not None

    test_message = "Integration test message payload"
    test_logger.info(test_message)

    # Check combined.log
    combined_log_path = os.path.join(LOGS_DIR, "combined.log")
    assert os.path.exists(combined_log_path)
    with open(combined_log_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert test_message in content


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Audit Ledger IO Persistence & Querying
# -----------------------------------------------------------------------------
def test_audit_ledger_io_persistence_and_querying():
    """Verifies that audit_operation appends structured JSON lines and can be queried."""
    unique_action = "Integration Test Unique Operation"
    with audit_operation(unique_action, service="TEST"):
        val = 1 + 1
        assert val == 2

    audit_file = os.path.join(LOGS_DIR, "audit.jsonl")
    assert os.path.exists(audit_file)

    # Query ledger
    records = query_audit_logs(operation=unique_action, limit=10)
    assert len(records) >= 1
    latest = records[0]
    assert latest["operation"] == unique_action
    assert latest["status"] == "SUCCESS"


# =============================================================================
# BLOCK 4: CLOSING BLOCK
# =============================================================================
__all__ = [
    "test_logger_multi_sink_file_persistence",
    "test_audit_ledger_io_persistence_and_querying",
]
