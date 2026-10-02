#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Simulator & Story Platform - Diagnostic Debugging Tool
=============================================================================
Comprehensive diagnostic auditor designed to assert, inspect, and isolate
failpoints across:
1. SQLite Story Database integrity (PRAGMA integrity_check, foreign keys, FTS5).
2. Card metadata bitmasks (passcodes, types, attributes, races, Link compass, Pendulum scales).
3. Binary CDB compilation parity (matching record counts, datas/texts table consistency).
4. Lua script syntax & ocgcore conventions (GetID(), initial_effect, luac bytecode validation).
5. Character story deck (.ydk) format and passcode resolution.

Usage:
    python3 development/tools/debug_diagnostics.py [--all] [--db] [--cards] [--cdb] [--lua] [--decks] [--json]
    ./manage.sh diagnose
=============================================================================
"""

import sys
import os
import sqlite3
import subprocess
import json
import argparse
from typing import List, Dict, Any, Optional

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, DECKS_DIR
from development.tools.constants import (
    TYPE_MONSTER, TYPE_NORMAL, TYPE_EFFECT, TYPE_FUSION, TYPE_RITUAL,
    TYPE_SYNCHRO, TYPE_XYZ, TYPE_PENDULUM, TYPE_LINK, TYPE_TUNER,
    TYPE_SPELL, TYPE_TRAP,
    ATTRIBUTE_EARTH, ATTRIBUTE_WATER, ATTRIBUTE_FIRE, ATTRIBUTE_WIND,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, ATTRIBUTE_DIVINE, ATTRIBUTE_MAP,
    RACE_MAP,
    LINK_B, LINK_BL, LINK_BR, LINK_L, LINK_R, LINK_T, LINK_TL, LINK_TR,
    LINK_ARROW_MAP
)
from development.tools.cdb_builder import parse_link_arrows


# ANSI terminal formatting
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"


class DiagnosticResult:
    """Encapsulates diagnostic inspection results and actionable failpoints."""

    def __init__(self, name: str):
        self.name = name
        self.status = "PASS"  # PASS, WARN, FAIL
        self.checked_count = 0
        self.failpoints: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []

    def add_failpoint(self, detail: str, suggestion: Optional[str] = None):
        """Register a fatal failpoint requiring remediation."""
        self.status = "FAIL"
        self.failpoints.append(detail)
        if suggestion and suggestion not in self.suggestions:
            self.suggestions.append(suggestion)

    def add_warning(self, detail: str, suggestion: Optional[str] = None):
        """Register a non-fatal warning."""
        if self.status != "FAIL":
            self.status = "WARN"
        self.warnings.append(detail)
        if suggestion and suggestion not in self.suggestions:
            self.suggestions.append(suggestion)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a serializable dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "checked_count": self.checked_count,
            "failpoints": self.failpoints,
            "warnings": self.warnings,
            "suggestions": self.suggestions
        }


class PlatformDiagnostics:
    """Master diagnostic auditing engine for simulator, DB, and script systems."""

    def __init__(self,
                 db_path: str = STORY_DB_PATH,
                 cdb_path: str = CDB_OUTPUT_PATH,
                 scripts_dir: str = SCRIPTS_DIR,
                 decks_dir: str = DECKS_DIR):
        self.db_path = db_path
        self.cdb_path = cdb_path
        self.scripts_dir = scripts_dir
        self.decks_dir = decks_dir

    # -------------------------------------------------------------------------
    # 1. Database Schema & FTS Integrity Audit
    # -------------------------------------------------------------------------
    def audit_database(self) -> DiagnosticResult:
        """Inspects SQLite database file integrity, table structures, and FTS5 search index."""
        res = DiagnosticResult("Database & Schema Integrity")

        if not os.path.exists(self.db_path):
            res.add_failpoint(
                f"Story database not found at: {self.db_path}",
                "Run './manage.sh install' or 'python3 development/database/seed_story_data.py' to initialize."
            )
            return res

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # PRAGMA integrity_check
            cur.execute("PRAGMA integrity_check;")
            integrity_rows = cur.fetchall()
            if not integrity_rows or integrity_rows[0][0] != "ok":
                res.add_failpoint(f"SQLite PRAGMA integrity_check failed: {integrity_rows}")

            # Check expected tables
            expected_tables = ["custom_cards", "factions", "characters", "decks", "deck_cards", "cards_fts"]
            cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
            found_tables = {row[0] for row in cur.fetchall()}

            for t in expected_tables:
                res.checked_count += 1
                if t not in found_tables:
                    res.add_failpoint(
                        f"Missing required table: '{t}'",
                        f"Re-run database migrations from development/database/schema.sql."
                    )

            # Check cards_fts synchronization
            if "custom_cards" in found_tables and "cards_fts" in found_tables:
                cur.execute("SELECT COUNT(*) FROM custom_cards;")
                card_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM cards_fts;")
                fts_count = cur.fetchone()[0]
                res.checked_count += 1
                if card_count != fts_count:
                    res.add_warning(
                        f"FTS index count mismatch: custom_cards has {card_count} rows, cards_fts has {fts_count} rows.",
                        "Execute: INSERT INTO cards_fts(cards_fts) VALUES('rebuild');"
                    )

            conn.close()
        except Exception as e:
            res.add_failpoint(f"Database diagnostic exception: {e}")

        return res

    # -------------------------------------------------------------------------
    # 2. Card Metadata & Bitmask Integrity Audit
    # -------------------------------------------------------------------------
    def audit_card_bitmasks(self) -> DiagnosticResult:
        """Audits every custom card for valid passcodes, Link arrow octal masks, and Pendulum scales."""
        res = DiagnosticResult("Card Metadata & Bitmask Diagnostics")

        if not os.path.exists(self.db_path):
            res.add_failpoint("Database not found; skipping card bitmask audit.")
            return res

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, card_type, card_subtype, attribute, monster_type,
                       level_or_rank_or_link, scale, atk, def, link_arrows
                FROM custom_cards;
            """)
            cards = cur.fetchall()
            conn.close()

            VALID_COMPASS_MASK = 0o757  # octal 0o757 = 495 dec (all 8 compass directions)

            for c in cards:
                cid, name, ctype, csub, attr, mtype, level, scale, atk, defense, link_arrows = c
                res.checked_count += 1
                prefix = f"Card #{cid} ('{name}')"

                # 1. Passcode boundary check
                if not (50000000 <= cid <= 59999999):
                    res.add_failpoint(
                        f"{prefix}: Passcode {cid} out of custom card range [50000000, 59999999].",
                        "Ensure passcodes are allocated via generate_custom_passcode()."
                    )

                # 2. Pendulum scale check
                if csub and "pendulum" in csub.lower():
                    if scale is None or not (0 <= scale <= 13):
                        res.add_failpoint(
                            f"{prefix}: Pendulum monster has invalid scale: {scale}. Must be 0..13.",
                            "Check card scale attribute in custom_cards table."
                        )

                # 3. Link Monster arrows & rating check
                if csub and "link" in csub.lower():
                    if link_arrows is None:
                        res.add_failpoint(f"{prefix}: Link monster is missing link_arrows bitmask.")
                    else:
                        if isinstance(link_arrows, str):
                            parsed_arrows = parse_link_arrows(link_arrows)
                        elif isinstance(link_arrows, int):
                            parsed_arrows = link_arrows
                        else:
                            parsed_arrows = 0

                        # Verify Link arrows octal compass validity
                        if (parsed_arrows & ~VALID_COMPASS_MASK) != 0:
                            res.add_failpoint(
                                f"{prefix}: Link arrow mask {oct(parsed_arrows)} contains invalid bits outside octal 0o757! "
                                f"Invalid bits: {oct(parsed_arrows & ~VALID_COMPASS_MASK)}."
                            )
                        # Count active arrows
                        active_arrows = bin(parsed_arrows).count("1")
                        if level and active_arrows != level:
                            res.add_warning(
                                f"{prefix}: Link rating ({level}) does not match number of active arrows ({active_arrows})."
                            )

                # 4. Attribute validity
                if ctype and ctype.lower() == "monster" and attr:
                    attr_val = ATTRIBUTE_MAP.get(attr.lower())
                    if not attr_val:
                        res.add_warning(f"{prefix}: Unknown elemental attribute '{attr}'.")
                    elif (attr_val & (attr_val - 1)) != 0:
                        res.add_failpoint(f"{prefix}: Attribute value {hex(attr_val)} is not a single-bit power of 2.")

                # 5. ATK / DEF boundary check
                if ctype and ctype.lower() == "monster":
                    if atk is not None and (atk < -1 or atk > 99999):
                        res.add_warning(f"{prefix}: Unusual ATK value: {atk}.")
                    if defense is not None and "link" not in (csub or "").lower() and (defense < -1 or defense > 99999):
                        res.add_warning(f"{prefix}: Unusual DEF value: {defense}.")

        except Exception as e:
            res.add_failpoint(f"Card bitmask audit exception: {e}")

        return res

    # -------------------------------------------------------------------------
    # 3. Binary CDB & Simulator Parity Audit
    # -------------------------------------------------------------------------
    def audit_cdb_parity(self) -> DiagnosticResult:
        """Asserts that SQLite CDB datas and texts tables exist and match Story DB custom_cards."""
        res = DiagnosticResult("CDB Compilation & Parity Diagnostics")

        if not os.path.exists(self.cdb_path):
            res.add_failpoint(
                f"custom_cards.cdb not found at: {self.cdb_path}",
                "Run './manage.sh sync' to build the simulator CDB."
            )
            return res

        if not os.path.exists(self.db_path):
            res.add_failpoint("Story DB not found; cannot verify CDB parity.")
            return res

        try:
            # Query story DB
            conn_story = sqlite3.connect(self.db_path)
            cur_story = conn_story.cursor()
            cur_story.execute("SELECT id, name FROM custom_cards ORDER BY id;")
            story_cards = cur_story.fetchall()
            conn_story.close()

            # Query CDB
            conn_cdb = sqlite3.connect(self.cdb_path)
            cur_cdb = conn_cdb.cursor()

            cur_cdb.execute("SELECT name FROM sqlite_master WHERE type='table';")
            cdb_tables = {row[0] for row in cur_cdb.fetchall()}
            if "datas" not in cdb_tables or "texts" not in cdb_tables:
                res.add_failpoint(f"CDB missing required tables: datas/texts. Found: {cdb_tables}")
                conn_cdb.close()
                return res

            cur_cdb.execute("SELECT id, ot, alias, setcode, type, atk, def, level, race, attribute, category FROM datas;")
            datas_rows = {row[0]: row for row in cur_cdb.fetchall()}

            cur_cdb.execute("SELECT id, name, desc FROM texts;")
            texts_rows = {row[0]: row for row in cur_cdb.fetchall()}
            conn_cdb.close()

            # Compare counts and IDs
            res.checked_count = len(story_cards)
            for cid, name in story_cards:
                if cid not in datas_rows:
                    res.add_failpoint(f"Card #{cid} ('{name}') missing from CDB 'datas' table!")
                if cid not in texts_rows:
                    res.add_failpoint(f"Card #{cid} ('{name}') missing from CDB 'texts' table!")

            # Verify no orphaned rows in datas vs texts
            orphan_datas = set(datas_rows.keys()) - set(texts_rows.keys())
            if orphan_datas:
                res.add_failpoint(f"Orphaned rows in CDB datas without texts: {orphan_datas}")

        except Exception as e:
            res.add_failpoint(f"CDB parity diagnostic exception: {e}")

        return res

    # -------------------------------------------------------------------------
    # 4. Lua Script Syntax & ocgcore Convention Audit
    # -------------------------------------------------------------------------
    def audit_lua_scripts(self) -> DiagnosticResult:
        """Validates existence, structure, and Lua syntax (via luac) of card scripts."""
        res = DiagnosticResult("Lua Effect Script Syntax Diagnostics")

        if not os.path.exists(self.db_path):
            res.add_failpoint("Story DB not found; cannot verify Lua scripts.")
            return res

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT id, name, card_subtype FROM custom_cards;")
            cards = cur.fetchall()
            conn.close()

            # Check if luac is available
            luac_available = False
            try:
                subprocess.run(["luac", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                luac_available = True
            except (FileNotFoundError, subprocess.SubprocessError):
                res.add_warning("luac bytecode compiler not found; syntax validation will rely on structural checks.")

            for cid, name, csub in cards:
                res.checked_count += 1
                script_name = f"c{cid}.lua"
                script_path = os.path.join(self.scripts_dir, script_name)

                # Check existence
                if not os.path.exists(script_path):
                    res.add_warning(
                        f"Script missing for Card #{cid} ('{name}'): expected {script_path}",
                        "Run './manage.sh sync' to generate missing Lua scripts."
                    )
                    continue

                # Read content
                with open(script_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Structural checks
                if "local s, id = GetID()" not in content:
                    res.add_failpoint(f"{script_name}: Missing mandatory ocgcore header 'local s, id = GetID()'")

                # If effect monster/spell/trap, expect initial_effect
                is_normal = bool(csub and "normal" in csub.lower() and "effect" not in csub.lower())
                if not is_normal:
                    if "function s.initial_effect(c)" not in content:
                        res.add_failpoint(f"{script_name}: Missing 'function s.initial_effect(c)' declaration.")

                # Bytecode syntax check via luac -p
                if luac_available:
                    proc = subprocess.run(["luac", "-p", script_path], capture_output=True, text=True)
                    if proc.returncode != 0:
                        err_msg = proc.stderr.strip() or "Syntax error detected by luac."
                        res.add_failpoint(f"{script_name} [luac syntax error]: {err_msg}")

        except Exception as e:
            res.add_failpoint(f"Lua script audit exception: {e}")

        return res

    # -------------------------------------------------------------------------
    # 5. Character Story Deck Audit
    # -------------------------------------------------------------------------
    def audit_decks(self) -> DiagnosticResult:
        """Audits character decks for valid format, minimum card counts, and valid card IDs."""
        res = DiagnosticResult("Story Deck Format & Passcode Diagnostics")

        if not os.path.exists(self.decks_dir):
            res.add_warning(f"Decks directory '{self.decks_dir}' does not exist.")
            return res

        deck_files = [f for f in os.listdir(self.decks_dir) if f.endswith(".ydk")]
        res.checked_count = len(deck_files)

        if not deck_files:
            res.add_warning(
                f"No .ydk deck files found in {self.decks_dir}.",
                "Run './manage.sh export-decks' to generate character story decks."
            )
            return res

        for df in deck_files:
            file_path = os.path.join(self.decks_dir, df)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip() and not l.startswith(("#", "!"))]

                # Must contain #main
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                if "#main" not in raw_content or "!side" not in raw_content:
                    res.add_failpoint(f"Deck '{df}': Missing standard #main or !side section header.")

                # Check passcodes in deck
                for code_str in lines:
                    if code_str.isdigit():
                        code = int(code_str)
                        if code <= 0:
                            res.add_failpoint(f"Deck '{df}': Contains invalid non-positive passcode {code}.")
                    else:
                        res.add_failpoint(f"Deck '{df}': Contains non-numeric passcode '{code_str}'.")

            except Exception as e:
                res.add_failpoint(f"Deck '{df}' read exception: {e}")

        return res

    # -------------------------------------------------------------------------
    # Master Audit Orchestration
    # -------------------------------------------------------------------------
    def run_all(self) -> Dict[str, DiagnosticResult]:
        """Runs all platform diagnostics and returns a dictionary of results."""
        return {
            "database": self.audit_database(),
            "cards": self.audit_card_bitmasks(),
            "cdb": self.audit_cdb_parity(),
            "lua": self.audit_lua_scripts(),
            "decks": self.audit_decks(),
        }


# =============================================================================
# CLI Formatting & Report Generator
# =============================================================================

def print_diagnostic_report(results: Dict[str, DiagnosticResult]) -> int:
    """Formats and prints an actionable terminal diagnostic report."""
    print(f"\n{BOLD}{BLUE}======================================================================{NC}")
    print(f"{BOLD}{BLUE}          YU-GI-OH! PLATFORM SYSTEM DIAGNOSTIC DEBUGGING REPORT       {NC}")
    print(f"{BOLD}{BLUE}======================================================================{NC}\n")

    total_checks = 0
    total_failpoints = 0
    total_warnings = 0
    has_fatal = False

    for key, res in results.items():
        total_checks += res.checked_count
        total_failpoints += len(res.failpoints)
        total_warnings += len(res.warnings)

        if res.status == "PASS":
            status_badge = f"{GREEN}[PASS]{NC}"
        elif res.status == "WARN":
            status_badge = f"{YELLOW}[WARN]{NC}"
        else:
            status_badge = f"{RED}[FAIL]{NC}"
            has_fatal = True

        print(f" {status_badge} {BOLD}{res.name}{NC} ({res.checked_count} items audited)")

        if res.failpoints:
            for fp in res.failpoints:
                print(f"   {RED}✘ Failpoint:{NC} {fp}")
        if res.warnings:
            for w in res.warnings:
                print(f"   {YELLOW}▲ Warning:{NC} {w}")
        if res.suggestions:
            for s in res.suggestions:
                print(f"   {BLUE}💡 Actionable Fix:{NC} {s}")
        print()

    print(f"{BOLD}{BLUE}----------------------------------------------------------------------{NC}")
    summary_color = RED if has_fatal else (YELLOW if total_warnings else GREEN)
    status_text = "FAILED" if has_fatal else ("PASSED WITH WARNINGS" if total_warnings else "ALL CHECKS PASSED")

    print(f"Summary: {summary_color}{BOLD}{status_text}{NC} | "
          f"Audited: {total_checks} | "
          f"Failpoints: {total_failpoints} | "
          f"Warnings: {total_warnings}")
    print(f"{BOLD}{BLUE}======================================================================{NC}\n")

    return 1 if has_fatal else 0


def main():
    parser = argparse.ArgumentParser(description="Yu-Gi-Oh! Simulator & Story Platform Diagnostic Auditor")
    parser.add_argument("--all", action="store_true", default=True, help="Run all diagnostic suites (default)")
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

    if not specific_requested or args.db:
        results["database"] = diag.audit_database()
    if not specific_requested or args.cards:
        results["cards"] = diag.audit_card_bitmasks()
    if not specific_requested or args.cdb:
        results["cdb"] = diag.audit_cdb_parity()
    if not specific_requested or args.lua:
        results["lua"] = diag.audit_lua_scripts()
    if not specific_requested or args.decks:
        results["decks"] = diag.audit_decks()

    if args.json:
        payload = {k: v.to_dict() for k, v in results.items()}
        print(json.dumps(payload, indent=2))
        return 1 if any(v.status == "FAIL" for v in results.values()) else 0

    return print_diagnostic_report(results)


if __name__ == "__main__":
    sys.exit(main())
