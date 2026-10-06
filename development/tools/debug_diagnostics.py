#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: development.tools.debug_diagnostics
Description:
    Diagnostic Debugging Tool and System Integrity Auditor for development pipelines.
    Bridges and re-exports authoritative diagnostic audits from config.debugger.diagnostics:
    1. SQLite Story Database integrity (PRAGMA integrity_check, foreign keys, all 14 tables, FTS5).
    2. Card metadata bitmasks (passcodes, types, attributes, races, Link compass, Pendulum scales).
    3. Binary CDB compilation parity (matching record counts, datas/texts table consistency).
    4. Lua script syntax & ocgcore conventions (GetID(), initial_effect, luac bytecode validation).
    5. Character story deck (.ydk) format and passcode resolution.
    6. Card artwork availability and image health verification.

Usage:
    python3 development/tools/debug_diagnostics.py [--all] [--db] [--cards] [--cdb] [--lua] [--decks] [--json]
    ./manage.sh diagnose
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional

# Ensure repository root is in sys.path and prevent stdlib shadowing
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_TOOLS_DIR = _CURR_DIR
_DEV_DIR = os.path.dirname(_TOOLS_DIR)
_ROOT_DIR = os.path.dirname(_DEV_DIR)
if sys.path and sys.path[0] == os.path.join(_ROOT_DIR, "config"):
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

# Import authoritative diagnostic classes and report formatters
from config.debugger.diagnostics import (
    DiagnosticResult,
    PlatformDiagnostics,
    print_diagnostic_report,
    take_debug_snapshot,
)

# Re-export constants for backwards compatibility with tests and callers
from config.paths import STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, DECKS_DIR
from config.game_rules import (
    TYPE_MONSTER, TYPE_NORMAL, TYPE_EFFECT, TYPE_FUSION, TYPE_RITUAL,
    TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK, TYPE_TUNER,
    TYPE_SPELL, TYPE_TRAP,
    ATTRIBUTE_EARTH, ATTRIBUTE_WATER, ATTRIBUTE_FIRE, ATTRIBUTE_WIND,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, ATTRIBUTE_DIVINE, ATTRIBUTE_MAP,
    RACE_MAP,
    LINK_B, LINK_BL, LINK_BR, LINK_L, LINK_R, LINK_T, LINK_TL, LINK_TR,
    LINK_ARROW_MAP
)

# ANSI terminal formatting
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

# =============================================================================
# BLOCK 3: BODY BLOCK (CLI Interface & Dispatch Logic)
# =============================================================================

def main() -> int:
    """CLI entrypoint for development diagnostic audits."""
    parser = argparse.ArgumentParser(description="Yu-Gi-Oh! Simulator & Story Platform Diagnostic Auditor")
    parser.add_argument("--all", action="store_true", default=False, help="Run all diagnostic suites")
    parser.add_argument("--db", action="store_true", help="Audit database and schema integrity only")
    parser.add_argument("--cards", action="store_true", help="Audit card metadata and bitmasks only")
    parser.add_argument("--cdb", action="store_true", help="Audit CDB compilation and parity only")
    parser.add_argument("--lua", action="store_true", help="Audit Lua effect scripts and syntax only")
    parser.add_argument("--decks", action="store_true", help="Audit character decks only")
    parser.add_argument("--json", action="store_true", help="Output results as JSON for programmatic tools")

    args = parser.parse_args()

    diag = PlatformDiagnostics()
    specific_requested = any([args.db, args.cards, args.cdb, args.lua, args.decks])

    results: Dict[str, DiagnosticResult] = {}

    if not specific_requested or args.all or args.db:
        results["database"] = diag.audit_database()
    if not specific_requested or args.all or args.cards:
        results["cards"] = diag.audit_card_bitmasks()
    if not specific_requested or args.all or args.cdb:
        results["cdb"] = diag.audit_cdb_parity()
    if not specific_requested or args.all or args.lua:
        results["lua"] = diag.audit_lua_scripts()
    if not specific_requested or args.all or args.decks:
        results["decks"] = diag.audit_decks()

    if args.json:
        payload = {k: v.to_dict() for k, v in results.items()}
        print(json.dumps(payload, indent=2))
        return 1 if any(v.status == "FAIL" for v in results.values()) else 0

    return print_diagnostic_report(results)


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    "DiagnosticResult",
    "PlatformDiagnostics",
    "print_diagnostic_report",
    "take_debug_snapshot",
    "main",
]

if __name__ == "__main__":
    sys.exit(main())
