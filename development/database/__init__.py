"""
=============================================================================
Yu-Gi-Oh! Platform - Database Schema & Data Migrations
=============================================================================
Contains SQLite database schemas, initialization scripts, and seeders:
- `schema.sql`: Central DDL definition for cards, stats, lore arcs, and decks.
- `seed_story_data`: Population script for bootstrapping initial cards and lore.
=============================================================================
"""

import os

DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(DATABASE_DIR, "schema.sql")

from .seed_story_data import initialize_database

__all__ = ["SCHEMA_FILE", "initialize_database", "DATABASE_DIR"]
