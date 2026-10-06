"""
=============================================================================
Yu-Gi-Oh! Platform - Database Schema & Data Migrations
=============================================================================
Contains SQLite database schemas, initialization scripts, and seeders:
- `schema.sql`: Central DDL definition for cards, stats, lore arcs, and decks.
- `seed_databases`: Authoritative two-tier database seeder pipeline.
=============================================================================
"""

import os

DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(DATABASE_DIR, "schema.sql")

from .seed_databases import seed_all_databases, initialize_database

__all__ = ["SCHEMA_FILE", "seed_all_databases", "initialize_database", "DATABASE_DIR"]
