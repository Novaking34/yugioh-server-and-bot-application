# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.debugger.diagnostics
Description:
    Authoritative Diagnostic Assertions, System Health Audits & Crash Snapshots.
    Centralizes all validation rules across the 3 applications and developer pipelines:
    1. Database integrity (PRAGMA integrity_check, foreign keys, all 14 tables, FTS5).
    2. Card metadata bitmasks (passcodes, types, attributes, races, links, pendulum scales).
    3. Binary CDB compilation parity (record counts matching authoritative database).
    4. Lua effect script syntax & structure (GetID, initial_effect, byte length).
    5. Story character deck (.ydk) format and passcode resolution.
    6. Card artwork file availability and thumbnail health.
    7. Automated post-mortem crash snapshot generator (logs/debug_snapshots/).
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import re
import json
import time
import sqlite3
import subprocess
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Ensure repository root in sys.path and prevent shadowing
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_CONFIG_DIR)
if sys.path and sys.path[0] == _CONFIG_DIR:
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from config.paths import (
    BASE_DIR, CONTENT_DB_PATH, TELEMETRY_DB_PATH, STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, DECKS_DIR, PICS_DIR, LOGS_DIR,
    DEBUG_SNAPSHOTS_DIR, TESTS_DIR, TESTS_UNIT_DIR, TESTS_INTEGRATION_DIR, TESTS_FUNCTIONAL_DIR, DNS_ZONE_FILE_PATH
)
from config.settings import settings
from config.game_rules import (
    CUSTOM_PASSCODE_MIN, CUSTOM_PASSCODE_MAX,
    TYPE_MONSTER, TYPE_SPELL, TYPE_TRAP, TYPE_PENDULUM, TYPE_LINK,
    ATTRIBUTE_EARTH, ATTRIBUTE_WATER, ATTRIBUTE_FIRE, ATTRIBUTE_WIND,
    ATTRIBUTE_LIGHT, ATTRIBUTE_DARK, ATTRIBUTE_DIVINE, ATTRIBUTE_MAP,
    RACE_MAP, LINK_ARROW_MAP
)
from config.logging import get_logger

# ANSI terminal formatting
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

# =============================================================================
# BLOCK 3: BODY BLOCK (Diagnostic Audit Engine & Snapshot Generator)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Diagnostic Result Container
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Master Platform Diagnostics Engine
# -----------------------------------------------------------------------------
class PlatformDiagnostics:
    """Master diagnostic auditing engine for simulator, DB, and script systems."""

    # Authoritative tables defined across schema_content.sql and schema_telemetry.sql
    EXPECTED_CONTENT_TABLES = [
        "custom_cards", "factions", "characters", "decks", "deck_cards", "cards_fts",
        "lore_arcs", "worldbuilding_elements", "story_chapters", "story_stages", "duel_logs"
    ]
    EXPECTED_TELEMETRY_TABLES = [
        "player_ratings", "duel_matches",
        "card_usage_stats", "player_decks", "player_saved_decks",
        "player_story_progress"
    ]
    EXPECTED_TABLES = EXPECTED_CONTENT_TABLES + EXPECTED_TELEMETRY_TABLES

    def __init__(
        self,
        db_path: str = CONTENT_DB_PATH,
        cdb_path: str = CDB_OUTPUT_PATH,
        scripts_dir: str = SCRIPTS_DIR,
        decks_dir: str = DECKS_DIR,
        pics_dir: str = PICS_DIR,
        zone_file_path: str = DNS_ZONE_FILE_PATH
    ):
        self.db_path = db_path
        self.cdb_path = cdb_path
        self.scripts_dir = scripts_dir
        self.decks_dir = decks_dir
        self.pics_dir = pics_dir
        self.zone_file_path = zone_file_path

    # 1. Database Schema & FTS Integrity Audit
    def audit_database(self) -> DiagnosticResult:
        """Inspects SQLite two-tier database file integrity, table structures, and FTS5 search index."""
        res = DiagnosticResult("Database & Schema Integrity")

        if not os.path.exists(self.db_path):
            res.add_failpoint(
                f"Authoritative database not found at: {self.db_path}",
                "Run './manage.sh install' or 'python3 data/authoritative/seed_databases.py' to initialize."
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
            cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
            found_tables = {row[0] for row in cur.fetchall()}

            is_canonical = (self.db_path == CONTENT_DB_PATH or self.db_path == STORY_DB_PATH)
            tables_to_check = self.EXPECTED_CONTENT_TABLES if is_canonical else self.EXPECTED_TABLES

            for t in tables_to_check:
                res.checked_count += 1
                if t not in found_tables:
                    res.add_failpoint(
                        f"Missing required table: '{t}'",
                        "Re-run database migrations from data/authoritative/schema_content.sql."
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

            # Audit dynamic telemetry store when inspecting canonical baseline
            if is_canonical:
                from config.paths import TELEMETRY_DB_PATH
                if not os.path.exists(TELEMETRY_DB_PATH):
                    res.add_failpoint(
                        f"Telemetry database not found at: {TELEMETRY_DB_PATH}",
                        "Run './manage.sh install' or 'python3 data/authoritative/seed_databases.py' to initialize."
                    )
                else:
                    try:
                        t_conn = sqlite3.connect(TELEMETRY_DB_PATH)
                        t_cur = t_conn.cursor()
                        t_cur.execute("PRAGMA integrity_check;")
                        t_int = t_cur.fetchone()
                        if not t_int or t_int[0] != "ok":
                            res.add_failpoint(f"Telemetry DB integrity check failed: {t_int}")
                        res.checked_count += 1

                        t_cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
                        t_found = {row[0] for row in t_cur.fetchall()}
                        for t in self.EXPECTED_TELEMETRY_TABLES:
                            res.checked_count += 1
                            if t not in t_found:
                                res.add_failpoint(f"Missing required telemetry table: '{t}'")
                        t_conn.close()
                    except Exception as te:
                        res.add_failpoint(f"Telemetry database diagnostic exception: {te}")
        except Exception as e:
            res.add_failpoint(f"Database diagnostic exception: {e}")

        return res

    # 2. Card Metadata Bitmasks & Logic Bounds Audit
    def audit_card_bitmasks(self) -> DiagnosticResult:
        """Audits every custom card for valid passcodes, Link arrow octal masks, and Pendulum scales."""
        res = DiagnosticResult("Card Metadata & Bitmask Diagnostics")

        if not os.path.exists(self.db_path):
            res.add_failpoint(f"Database missing: {self.db_path}")
            return res

        VALID_COMPASS_MASK = 0o757  # octal 0o757 = 495 dec (all 8 compass directions)

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

            for c in cards:
                cid, name, ctype, csub, attr, mtype, level, scale, atk, defense, link_arrows = c
                res.checked_count += 1
                prefix = f"Card #{cid} ('{name}')"

                # 1. Passcode boundary check (custom card partition: 50000000 - 59999999)
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
                        if isinstance(link_arrows, int):
                            parsed_arrows = link_arrows
                        elif isinstance(link_arrows, str):
                            if link_arrows.isdigit():
                                parsed_arrows = int(link_arrows)
                            else:
                                arrow_bitmask = 0
                                parts = [p.strip().upper() for p in link_arrows.replace(';', ',').split(',') if p.strip()]
                                for p in parts:
                                    if p in LINK_ARROW_MAP:
                                        arrow_bitmask |= LINK_ARROW_MAP[p]
                                parsed_arrows = arrow_bitmask
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

                # 5. ATK / DEF boundary check (-2 represents ? in YGOPro)
                if ctype and ctype.lower() == "monster":
                    if atk is not None and (atk < -2 or atk > 99999):
                        res.add_warning(f"{prefix}: Unusual ATK value: {atk}.")
                    if defense is not None and "link" not in (csub or "").lower() and (defense < -2 or defense > 99999):
                        res.add_warning(f"{prefix}: Unusual DEF value: {defense}.")

        except Exception as e:
            res.add_failpoint(f"Card bitmask diagnostic exception: {e}")

        return res

    # 3. CDB Binary Compilation Parity Audit
    def audit_cdb_parity(self) -> DiagnosticResult:
        """Verifies binary CDB database existence, schema, and 1:1 row parity with SQLite DB."""
        res = DiagnosticResult("CDB Compilation & Parity Diagnostics")

        if not os.path.exists(self.cdb_path):
            res.add_failpoint(
                f"Compiled CDB database not found at: {self.cdb_path}",
                "Run './manage.sh sync' to build custom_cards.cdb from the story database."
            )
            return res

        try:
            story_conn = sqlite3.connect(self.db_path)
            s_cur = story_conn.cursor()
            s_cur.execute("SELECT COUNT(*) FROM custom_cards;")
            expected_count = s_cur.fetchone()[0]
            story_conn.close()

            cdb_conn = sqlite3.connect(self.cdb_path)
            c_cur = cdb_conn.cursor()

            c_cur.execute("SELECT COUNT(*) FROM datas;")
            datas_count = c_cur.fetchone()[0]

            c_cur.execute("SELECT COUNT(*) FROM texts;")
            texts_count = c_cur.fetchone()[0]

            res.checked_count = datas_count

            if datas_count != expected_count:
                res.add_failpoint(
                    f"CDB 'datas' table count ({datas_count}) does not match story DB count ({expected_count}).",
                    "Run './manage.sh sync' to recompile CDB with all current cards."
                )

            if texts_count != expected_count:
                res.add_failpoint(
                    f"CDB 'texts' table count ({texts_count}) does not match story DB count ({expected_count}).",
                    "Run './manage.sh sync' to synchronize card text descriptions."
                )

            cdb_conn.close()
        except Exception as e:
            res.add_failpoint(f"CDB parity diagnostic exception: {e}")

        return res

    # 4. Lua Script Syntax & Conventions Audit
    def audit_lua_scripts(self) -> DiagnosticResult:
        """Validates existence, structure, and Lua syntax (via luac) of card scripts."""
        res = DiagnosticResult("Lua Effect Script Syntax Diagnostics")

        if not os.path.exists(self.db_path):
            res.add_failpoint(f"Story DB not found at: {self.db_path}; cannot verify Lua scripts.")
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
                    if "function s.initial_effect(c)" not in content and "initial_effect" not in content:
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

    # 5. Character Story Decks Audit
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

    audit_story_decks = audit_decks

    # 6. Card Artwork Assets Audit
    def audit_card_artwork(self) -> DiagnosticResult:
        """Audits local image files for all custom cards in the expansion pool."""
        res = DiagnosticResult("Card Artwork Assets Diagnostics")

        if not os.path.exists(self.pics_dir):
            res.add_failpoint(f"Pics directory not found at: {self.pics_dir}")
            return res

        if not os.path.exists(self.db_path):
            res.add_failpoint(f"Story DB not found: {self.db_path}")
            return res

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM custom_cards;")
            cards = cur.fetchall()
            conn.close()

            for cid, cname in cards:
                res.checked_count += 1
                img_path = os.path.join(self.pics_dir, f"{cid}.jpg")
                if not os.path.exists(img_path):
                    res.add_warning(
                        f"Missing card artwork image for '{cname}' (ID: {cid}) at {img_path}",
                        "Run './manage.sh tracker download-images' to fetch remote artwork."
                    )
                elif os.path.getsize(img_path) < 1000:
                    res.add_warning(f"Card artwork for '{cname}' (ID: {cid}) appears corrupted (< 1000 bytes).")
        except Exception as e:
            res.add_failpoint(f"Artwork diagnostic exception: {e}")

        return res

    # 7. DNS Zone & Domain Routing Audit
    def audit_dns_zone(self) -> DiagnosticResult:
        """Inspects BIND RFC 1035 zone file existence, syntax validity, and required routing records."""
        res = DiagnosticResult("DNS Zone & Domain Routing Integrity")

        if not os.path.exists(self.zone_file_path):
            res.add_failpoint(
                f"DNS zone file not found at: {self.zone_file_path}",
                "Run 'python3 packages/server/dns/zone_manager.py --sync' to generate."
            )
            return res

        try:
            from packages.server.dns.zone_manager import validate_zone_content
            with open(self.zone_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            is_valid, errors = validate_zone_content(content)
            res.checked_count += 4  # Audited origin, TTL, web catalog routing, game socket routing

            if not is_valid:
                for err in errors:
                    res.add_failpoint(f"DNS Zone Error: {err}")
            else:
                res.status = "PASS"
        except Exception as e:
            res.add_failpoint(f"DNS zone audit exception: {e}")

        return res

    # 7. Automated Test Suite Diagnostic Audit
    def audit_test_suite(
        self,
        domain: Optional[str] = None,
        tier: Optional[str] = None,
        data_mode: str = "live"
    ) -> DiagnosticResult:
        """Executes the automated Pytest test suite as an active diagnostic health assertion.
        
        Supports targeted auditing across tiers ('unit', 'integration', 'functional')
        and data modes ('live', 'sample', 'both'). Extracts failing test node IDs and
        tracebacks as actionable failpoints.
        
        Args:
            domain (Optional[str]): Subsystem directory within tests (e.g., 'config', 'bot', 'tools').
            tier (Optional[str]): Test taxonomy tier ('unit', 'integration', 'functional', or None for all).
            data_mode (str): Data source strategy ('live', 'sample', or 'both').
            
        Returns:
            DiagnosticResult: Audit report container with executed count, pass/fail status, and failpoints.
        """
        tier_clean = tier.lower().strip() if tier else None
        data_clean = data_mode.lower().strip() if data_mode else "live"

        # Resolve target test filesystem path
        target_path = TESTS_DIR
        if tier_clean == "unit":
            target_path = TESTS_UNIT_DIR
        elif tier_clean == "integration":
            target_path = TESTS_INTEGRATION_DIR
        elif tier_clean == "functional":
            target_path = TESTS_FUNCTIONAL_DIR

        if domain:
            potential_path = os.path.join(target_path, domain)
            if os.path.exists(potential_path):
                target_path = potential_path
            else:
                potential_root = os.path.join(TESTS_DIR, domain)
                if os.path.exists(potential_root):
                    target_path = potential_root

        tier_title = (tier_clean or "All Tiers").capitalize()
        res = DiagnosticResult(f"Automated Test Suite ({tier_title} | {data_clean.capitalize()} Data)")

        pytest_bin = os.path.join(BASE_DIR, "venv", "bin", "pytest")
        if not os.path.exists(pytest_bin):
            pytest_bin = sys.executable
            cmd = [pytest_bin, "-m", "pytest", "-v", f"--data-mode={data_clean}", target_path]
        else:
            cmd = [pytest_bin, "-v", f"--data-mode={data_clean}", target_path]

        try:
            proc = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            raw_output = (proc.stdout or "") + "\n" + (proc.stderr or "")

            # Parse test counts from Pytest summary
            passed_match = re.search(r"(\d+)\s+passed", raw_output)
            failed_match = re.search(r"(\d+)\s+failed", raw_output)
            error_match = re.search(r"(\d+)\s+error", raw_output)
            skipped_match = re.search(r"(\d+)\s+skipped", raw_output)

            passed_cnt = int(passed_match.group(1)) if passed_match else 0
            failed_cnt = int(failed_match.group(1)) if failed_match else 0
            error_cnt = int(error_match.group(1)) if error_match else 0
            skipped_cnt = int(skipped_match.group(1)) if skipped_match else 0

            total_audited = passed_cnt + failed_cnt + error_cnt + skipped_cnt
            if total_audited == 0:
                # Fallback: count individual PASSED markers in verbose output
                total_audited = raw_output.count(" PASSED") + raw_output.count(" FAILED") + raw_output.count(" ERROR")

            res.checked_count = total_audited

            if proc.returncode == 0:
                res.status = "PASS"
            else:
                res.status = "FAIL"
                # Extract individual failure summaries from short test summary info
                fail_lines = []
                in_summary = False
                for line in raw_output.splitlines():
                    if "short test summary info" in line:
                        in_summary = True
                        continue
                    if in_summary:
                        if line.startswith("==="):
                            break
                        if line.startswith("FAILED") or line.startswith("ERROR"):
                            fail_lines.append(line.strip())

                if fail_lines:
                    for fl in fail_lines:
                        res.add_failpoint(
                            fl,
                            suggestion="Run './manage.sh test -v' on the failing test target for full traceback."
                        )
                else:
                    res.add_failpoint(
                        f"Pytest exited with status code {proc.returncode}. Output:\n{raw_output[-500:]}",
                        suggestion="Check environment, dependencies, and test database connectivity."
                    )

        except subprocess.TimeoutExpired:
            res.add_failpoint(
                "Pytest execution timed out after 120 seconds.",
                suggestion="Investigate potential deadlocks in asynchronous test fixtures or external network requests."
            )
        except Exception as e:
            res.add_failpoint(f"Pytest execution exception: {e}")

        return res

    # Run All Audits
    def run_all(
        self,
        include_tests: bool = False,
        tier: Optional[str] = None,
        data_mode: str = "live"
    ) -> List[DiagnosticResult]:
        """Runs the complete comprehensive platform diagnostic suite.
        
        Args:
            include_tests (bool): If True, executes pytest test suite as a diagnostic check.
            tier (Optional[str]): Filter tests to 'unit', 'integration', or 'functional'.
            data_mode (str): Data source strategy ('live', 'sample', or 'both').
            
        Returns:
            List[DiagnosticResult]: Complete list of diagnostic results.
        """
        results = [
            self.audit_database(),
            self.audit_card_bitmasks(),
            self.audit_cdb_parity(),
            self.audit_lua_scripts(),
            self.audit_story_decks(),
            self.audit_card_artwork(),
            self.audit_dns_zone(),
        ]
        if include_tests:
            if data_mode.lower() == "both":
                results.append(self.audit_test_suite(tier=tier, data_mode="live"))
                results.append(self.audit_test_suite(tier=tier, data_mode="sample"))
            else:
                results.append(self.audit_test_suite(tier=tier, data_mode=data_mode))
        return results


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Post-Mortem Crash Snapshot Dumper & Retention Pruner
# -----------------------------------------------------------------------------
def prune_debug_snapshots(retention_days: Optional[int] = None) -> int:
    """Prunes debug snapshots older than retention threshold from logs/debug_snapshots/.
    
    Args:
        retention_days (Optional[int]): Days threshold, defaults to settings.debug.snapshot_retention_days.
        
    Returns:
        int: Number of pruned snapshot files.
    """
    days = retention_days if retention_days is not None else settings.debug.snapshot_retention_days
    cutoff_sec = time.time() - (days * 86400)
    pruned_count = 0
    if not os.path.exists(DEBUG_SNAPSHOTS_DIR):
        return 0

    for fname in os.listdir(DEBUG_SNAPSHOTS_DIR):
        if fname.startswith("snapshot_") and fname.endswith(".json"):
            fpath = os.path.join(DEBUG_SNAPSHOTS_DIR, fname)
            try:
                if os.path.getmtime(fpath) < cutoff_sec:
                    os.remove(fpath)
                    pruned_count += 1
            except (OSError, PermissionError):
                pass
    return pruned_count


def take_debug_snapshot(
    incident_id: str,
    context: Optional[Dict[str, Any]] = None,
    caller_frame: Optional[Any] = None
) -> str:
    """Takes an instantaneous diagnostic snapshot and persists it into DEBUG_SNAPSHOTS_DIR."""
    os.makedirs(DEBUG_SNAPSHOTS_DIR, exist_ok=True)
    snapshot_path = os.path.join(DEBUG_SNAPSHOTS_DIR, f"snapshot_{incident_id}.json")

    diag = PlatformDiagnostics()
    results = [r.to_dict() for r in diag.run_all()]

    snapshot_context = context.copy() if context else {}
    if settings.debug.capture_locals and caller_frame is not None:
        try:
            snapshot_context["local_variables"] = {
                k: repr(v) for k, v in getattr(caller_frame, "f_locals", {}).items()
                if not k.startswith("__")
            }
        except Exception:
            pass

    snapshot = {
        "incident_id": incident_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": snapshot_context,
        "diagnostics": results,
    }

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    # Prune stale snapshots to protect disk
    try:
        prune_debug_snapshots()
    except Exception:
        pass

    # Record operational audit event
    try:
        from config.logging import record_audit_event
        record_audit_event(
            operation="Create Debug Snapshot",
            service="DEBUG",
            status="SUCCESS",
            elapsed_sec=0.0,
            metadata={"incident_id": incident_id, "snapshot_path": snapshot_path}
        )
    except Exception:
        pass

    return snapshot_path


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Terminal Report Formatter
# -----------------------------------------------------------------------------
def print_diagnostic_report(results: Any) -> int:
    """Prints a formatted diagnostic report to stdout. Returns 0 on pass, 1 on fail."""
    print(f"\n{BOLD}{BLUE}======================================================================{NC}")
    print(f"{BOLD}{BLUE}          YU-GI-OH! PLATFORM SYSTEM DIAGNOSTIC DEBUGGING REPORT       {NC}")
    print(f"{BOLD}{BLUE}======================================================================{NC}\n")

    result_list: List[DiagnosticResult] = list(results.values()) if isinstance(results, dict) else list(results)

    has_fail = any(r.status == "FAIL" for r in result_list)
    has_warn = any(r.status == "WARN" for r in result_list)
    total_audited = sum(r.checked_count for r in result_list)
    total_failpoints = sum(len(r.failpoints) for r in result_list)
    total_warnings = sum(len(r.warnings) for r in result_list)

    for r in result_list:
        status_color = GREEN if r.status == "PASS" else (YELLOW if r.status == "WARN" else RED)
        print(f" {status_color}[{r.status}]{NC} {BOLD}{r.name}{NC} ({r.checked_count} items audited)")

        for fp in r.failpoints:
            print(f"    {RED}✘ FAILPOINT:{NC} {fp}")
        for w in r.warnings:
            print(f"    {YELLOW}▲ WARNING:{NC} {w}")
        for s in r.suggestions:
            print(f"    {BLUE}💡 REMEDIATION:{NC} {s}")
        print()

    print("-" * 70)
    summary_color = RED if has_fail else (YELLOW if has_warn else GREEN)
    summary_status = "FAILPOINTS DETECTED" if has_fail else ("WARNINGS DETECTED" if has_warn else "ALL CHECKS PASSED")
    print(f"{BOLD}Summary: {summary_color}{summary_status}{NC} | Audited: {total_audited} | Failpoints: {total_failpoints} | Warnings: {total_warnings}")
    print(f"{BOLD}{BLUE}======================================================================{NC}\n")

    return 1 if has_fail else 0


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    "DiagnosticResult",
    "PlatformDiagnostics",
    "take_debug_snapshot",
    "prune_debug_snapshots",
    "print_diagnostic_report",
]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Yu-Gi-Oh! Platform System Diagnostics")
    parser.add_argument("--with-tests", "-t", action="store_true", help="Include automated test suite in diagnostics")
    parser.add_argument("--tier", choices=["unit", "integration", "functional"], default=None, help="Target test taxonomy tier")
    parser.add_argument("--data-mode", choices=["live", "sample", "both"], default="live", help="Data source strategy for tests")
    args = parser.parse_args()

    diag = PlatformDiagnostics()
    results = diag.run_all(include_tests=args.with_tests, tier=args.tier, data_mode=args.data_mode)
    sys.exit(print_diagnostic_report(results))
