#!/usr/bin/env python3
"""
=============================================================================
Authoritative & Telemetry Database Connection & Utility Helpers
=============================================================================
Manages SQLite database connections with row factory configuration,
safe context managers, and two-tier path resolution for content.db and telemetry.db.
=============================================================================
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

try:
    from config.paths import CONTENT_DB_PATH, TELEMETRY_DB_PATH, BASE_DIR
    DB_PATH = CONTENT_DB_PATH
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    CONTENT_DB_PATH = os.path.join(BASE_DIR, "data", "authoritative", "content.db")
    TELEMETRY_DB_PATH = os.path.join(BASE_DIR, "data", "telemetry", "telemetry.db")
    DB_PATH = CONTENT_DB_PATH


def get_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Returns a configured SQLite database connection with row factory
    enabled for dict-like attribute access on query results.
    Automatically attaches complementary tier if available.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if (db_path == CONTENT_DB_PATH or db_path.endswith("content.db")) and os.path.exists(TELEMETRY_DB_PATH):
        try:
            conn.execute(f"ATTACH DATABASE '{TELEMETRY_DB_PATH}' AS telemetry")
        except sqlite3.OperationalError:
            pass
    elif (db_path == TELEMETRY_DB_PATH or db_path.endswith("telemetry.db")) and os.path.exists(CONTENT_DB_PATH):
        try:
            conn.execute(f"ATTACH DATABASE '{CONTENT_DB_PATH}' AS content")
        except sqlite3.OperationalError:
            pass
    return conn


def get_content_db() -> sqlite3.Connection:
    """Returns a configured connection to the authoritative content database."""
    return get_db(CONTENT_DB_PATH)


def get_telemetry_db() -> sqlite3.Connection:
    """Returns a configured connection to the dynamic telemetry database."""
    return get_db(TELEMETRY_DB_PATH)


@contextmanager
def db_session() -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager that yields a database cursor, automatically commits
    on success, rolls back on exception, and closes the connection.
    
    Usage:
        with db_session() as cur:
            cur.execute("SELECT * FROM custom_cards")
            results = cur.fetchall()
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


__all__ = [
    "get_db",
    "get_content_db",
    "get_telemetry_db",
    "db_session",
    "DB_PATH",
    "CONTENT_DB_PATH",
    "TELEMETRY_DB_PATH",
]
