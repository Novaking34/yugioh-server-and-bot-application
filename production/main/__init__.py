"""
=============================================================================
Yu-Gi-Oh! Platform - Host Server Production Main Package
=============================================================================
Orchestrates the core host server runtime:
- `logger`: Centralized multi-destination rotating log subsystem.
- `app`: Native desktop Platform Manager GUI.
- `setup_wizard`: Interactive configuration bootstrap wizard.
- `web`: FastAPI Card Catalog, Deck API, and Lore Portal.
- `discord_bot`: The Great Kasutamaiza story and duel moderation bot.
- `simulator`: YGOPro duel engine container configurations and scripts.
=============================================================================
"""

from .logger import get_logger, audit_operation, log_diagnostic_snapshot

__all__ = [
    "get_logger",
    "audit_operation",
    "log_diagnostic_snapshot",
]
