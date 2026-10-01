#!/usr/bin/env python3
"""
=============================================================================
Story Database Connection & Utility Helpers
=============================================================================
Manages SQLite database connections with row factory configuration,
safe context managers, and path resolution for `ygo_story.db`.
=============================================================================
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "story_database", "ygo_story.db")


def get_db() -> sqlite3.Connection:
    """
    Returns a configured SQLite database connection with row factory
    enabled for dict-like attribute access on query results.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
