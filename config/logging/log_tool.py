#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.logging.log_tool
Architecture: Platform Observability CLI & Telemetry Inspection Engine
Domain: Log Stream Aggregation, Querying, Audit Ledger Inspection & Storage Hygiene
Description:
    Authoritative administrative utility for inspecting, querying, and managing
    log files and audit ledgers across all platform services (FastAPI web catalog,
    modular Discord bot, live ocgcore simulator, CDB compiler, and migration tools).

Features:
    1. Multi-Target Storage Statistics:
       - Computes file sizes, line counts, error frequencies, and warnings.
    2. Dynamic Tail Streamer:
       - Displays the most recent N log lines for any service or combined timeline.
    3. Multi-Criteria Log Query Engine:
       - Filters records across combined.log, errors.log, or specific service logs
         by severity level, subsystem, or keyword regex.
    4. Authoritative Audit Ledger Inspector:
       - Parses and queries logs/audit.jsonl records by operation, service, status,
         or correlation trace_id.
    5. Safe Storage Truncation:
       - Truncates log files with required confirmation flag to prevent disk saturation.

Usage (CLI):
    python3 -m config.logging.log_tool stats
    python3 -m config.logging.log_tool tail --service web -n 30
    python3 -m config.logging.log_tool query --level ERROR --limit 20
    python3 -m config.logging.log_tool audit --status FAILED
    python3 -m config.logging.log_tool clean --confirm

Usage (Python API):
    from config.logging import get_log_stats, tail_log, query_logs, query_audit_logs, clean_logs
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions, Imports & Styling Primitives)
# =============================================================================

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Optional

# Ensure repository root is in sys.path and prevent package shadowing
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.dirname(_CURR_DIR)
_ROOT_DIR = os.path.dirname(_CONFIG_DIR)
if sys.path and sys.path[0] == _CONFIG_DIR:
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from config.paths import (
    LOGS_DIR,
    COMBINED_LOG_PATH,
    ERRORS_LOG_PATH,
    AUDIT_LOG_PATH,
)

# ANSI Terminal Color Constants
RESET = "\033[0m"
NC = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
GRAY = "\033[0;90m"
MAGENTA = "\033[0;35m"


# =============================================================================
# BLOCK 3: BODY BLOCK (Core Inspection & Telemetry Implementations)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Log Directory Statistics Scanner
# -----------------------------------------------------------------------------
def get_log_stats() -> List[Dict[str, Any]]:
    """Scans the `logs/` directory and returns metadata, file size, line counts,
    and error counts for every log and audit file.

    Returns:
        List[Dict[str, Any]]: Per-file statistics dictionary.
    """
    stats: List[Dict[str, Any]] = []
    if not os.path.exists(LOGS_DIR):
        return stats

    for fname in sorted(os.listdir(LOGS_DIR)):
        if not (fname.endswith(".log") or fname.endswith(".jsonl")):
            continue

        fpath = os.path.join(LOGS_DIR, fname)
        if not os.path.isfile(fpath):
            continue

        size_bytes = os.path.getsize(fpath)
        mtime = os.path.getmtime(fpath)
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))

        line_count = 0
        error_count = 0
        warning_count = 0

        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line_count += 1
                    if " [ERROR] " in line or '"level": "ERROR"' in line or "CRITICAL" in line or '"status": "FAILED"' in line:
                        error_count += 1
                    elif " [WARNING] " in line or '"level": "WARNING"' in line or '"status": "WARN"' in line:
                        warning_count += 1
        except Exception:
            pass

        stats.append({
            "filename": fname,
            "path": fpath,
            "size_kb": round(size_bytes / 1024, 2),
            "line_count": line_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "last_modified": mtime_str,
        })

    return stats


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Log Tail Stream Reader
# -----------------------------------------------------------------------------
def tail_log(service: str = "combined", lines: int = 50) -> List[str]:
    """Returns the last `lines` entries from the target service's log file.

    Args:
        service (str): Service name ('web', 'bot', 'simulator', 'combined', 'errors', 'audit').
        lines (int): Number of most recent lines to read.

    Returns:
        List[str]: Buffer containing the trailing log lines.
    """
    if not os.path.exists(LOGS_DIR):
        return []

    service_lower = service.lower().replace("-", "_")
    if service_lower == "audit":
        target_file = AUDIT_LOG_PATH
    elif service_lower == "errors":
        target_file = ERRORS_LOG_PATH
    else:
        target_file = os.path.join(LOGS_DIR, f"{service_lower}.log")

    if not os.path.exists(target_file):
        # Fall back to master combined log
        target_file = COMBINED_LOG_PATH
        if not os.path.exists(target_file):
            return []

    buffer: List[str] = []
    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            buffer = all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        buffer.append(f"[-] Error reading {target_file}: {e}\n")

    return buffer


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Multi-Criteria Log Query Search Engine
# -----------------------------------------------------------------------------
def query_logs(
    level: Optional[str] = None,
    service: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Searches across combined.log (or a specific service log) filtering by
    severity level, service identifier, or text keywords.

    Args:
        level (Optional[str]): Severity level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        service (Optional[str]): Service name to scope search.
        keyword (Optional[str]): Substring keyword to match against message.
        limit (int): Maximum records to return.

    Returns:
        List[Dict[str, Any]]: Matching records with origin file and raw text.
    """
    results: List[Dict[str, Any]] = []
    if not os.path.exists(LOGS_DIR):
        return results

    if service:
        service_clean = service.lower().replace("-", "_")
        fpath = os.path.join(LOGS_DIR, f"{service_clean}.log")
        files_to_scan = [fpath] if os.path.exists(fpath) else []
    else:
        files_to_scan = [COMBINED_LOG_PATH] if os.path.exists(COMBINED_LOG_PATH) else []

    if not files_to_scan:
        return results

    level_upper = level.upper() if level else None
    kw_lower = keyword.lower() if keyword else None

    for target_path in files_to_scan:
        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    # Filter by severity level
                    if level_upper and f" [{level_upper}] " not in line and f'"level": "{level_upper}"' not in line:
                        continue

                    # Filter by search keyword
                    if kw_lower and kw_lower not in line.lower():
                        continue

                    results.append({
                        "file": os.path.basename(target_path),
                        "raw": line.strip(),
                    })
                    if len(results) >= limit:
                        break
        except Exception:
            pass

    return results


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Authoritative Audit Ledger Inspector
# -----------------------------------------------------------------------------
def query_audit_logs(
    operation: Optional[str] = None,
    service: Optional[str] = None,
    status: Optional[str] = None,
    trace_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Queries the append-only audit ledger (logs/audit.jsonl) with filtering.

    Args:
        operation (Optional[str]): Operational mutation name.
        service (Optional[str]): Subsystem name.
        status (Optional[str]): Execution outcome ('SUCCESS' or 'FAILED').
        trace_id (Optional[str]): Correlation trace ID.
        limit (int): Maximum matching events to return.

    Returns:
        List[Dict[str, Any]]: Parsed audit records.
    """
    results: List[Dict[str, Any]] = []
    if not os.path.exists(AUDIT_LOG_PATH):
        return results

    op_lower = operation.lower() if operation else None
    svc_lower = service.lower() if service else None
    status_upper = status.upper() if status else None

    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if op_lower and op_lower not in record.get("operation", "").lower():
                    continue
                if svc_lower and svc_lower != record.get("service", "").lower():
                    continue
                if status_upper and status_upper != record.get("status", "").upper():
                    continue
                if trace_id and trace_id != record.get("trace_id"):
                    continue

                results.append(record)
                if len(results) >= limit:
                    break
    except Exception:
        pass

    return results


# -----------------------------------------------------------------------------
# Sub-Block 3.5: Log Truncation & Storage Hygiene Tool
# -----------------------------------------------------------------------------
def clean_logs(confirm: bool = False) -> Dict[str, Any]:
    """Safely purges or truncates old log files in `logs/` to free storage.
    Requires `confirm=True` to execute.

    Args:
        confirm (bool): Safety confirmation switch.

    Returns:
        Dict[str, Any]: Execution status, truncated file count, and freed storage.
    """
    if not confirm:
        return {"status": "aborted", "message": "Confirmation required (pass --confirm)"}

    if not os.path.exists(LOGS_DIR):
        return {"status": "ok", "truncated_files": 0, "freed_bytes": 0}

    freed = 0
    truncated = 0
    for fname in os.listdir(LOGS_DIR):
        if fname.endswith(".log") or fname.endswith(".jsonl"):
            fpath = os.path.join(LOGS_DIR, fname)
            try:
                size = os.path.getsize(fpath)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.truncate(0)
                freed += size
                truncated += 1
            except Exception:
                pass

    return {
        "status": "ok",
        "truncated_files": truncated,
        "freed_kb": round(freed / 1024, 2),
    }


# =============================================================================
# BLOCK 4: CLOSING BLOCK (CLI Parser, Exports & Router)
# =============================================================================

__all__ = [
    "get_log_stats",
    "tail_log",
    "query_logs",
    "query_audit_logs",
    "clean_logs",
]


def main() -> None:
    """CLI execution dispatcher for platform logging management."""
    parser = argparse.ArgumentParser(
        description="Yu-Gi-Oh! Platform Logging Telemetry & Audit Utility"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # stats
    subparsers.add_parser("stats", help="Display storage statistics across all service log files")

    # tail
    tail_parser = subparsers.add_parser("tail", help="Display the most recent log entries")
    tail_parser.add_argument("-s", "--service", default="combined", help="Target service (e.g. web, bot, simulator, tools, errors, audit)")
    tail_parser.add_argument("-n", "--lines", type=int, default=30, help="Number of lines to display")

    # query
    query_parser = subparsers.add_parser("query", help="Filter and query logs by level or keyword")
    query_parser.add_argument("-l", "--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Log severity level")
    query_parser.add_argument("-s", "--service", help="Filter by specific service name")
    query_parser.add_argument("-k", "--keyword", help="Text keyword to match")
    query_parser.add_argument("--limit", type=int, default=50, help="Maximum entries to return")

    # audit
    audit_parser = subparsers.add_parser("audit", help="Inspect operational mutation audit ledger (audit.jsonl)")
    audit_parser.add_argument("-o", "--operation", help="Filter by operation name")
    audit_parser.add_argument("-s", "--service", help="Filter by service name")
    audit_parser.add_argument("--status", choices=["SUCCESS", "FAILED"], help="Filter by status")
    audit_parser.add_argument("-t", "--trace-id", help="Filter by trace ID")
    audit_parser.add_argument("--limit", type=int, default=50, help="Maximum audit records to return")

    # clean
    clean_parser = subparsers.add_parser("clean", help="Safely truncate all log files")
    clean_parser.add_argument("--confirm", action="store_true", help="Confirm log truncation")

    args = parser.parse_args()

    if args.command == "stats":
        stats = get_log_stats()
        print(f"\n{BOLD}{BLUE}======================================================================{NC}")
        print(f"{BOLD}{BLUE}         YU-GI-OH! PLATFORM LOG TELEMETRY & STORAGE AUDIT            {NC}")
        print(f"{BOLD}{BLUE}======================================================================{NC}\n")
        if not stats:
            print(f" {YELLOW}[!] No log files found in {LOGS_DIR}{NC}\n")
            return

        fmt = "{:<22} {:<10} {:<10} {:<10} {:<10} {:<20}"
        print(f"{BOLD}" + fmt.format("LOG FILE", "SIZE (KB)", "LINES", "ERRORS", "WARNINGS", "LAST MODIFIED") + f"{RESET}")
        print("-" * 84)
        for s in stats:
            err_color = RED if s["error_count"] > 0 else GREEN
            warn_color = YELLOW if s["warning_count"] > 0 else GRAY
            print(fmt.format(
                s["filename"],
                str(s["size_kb"]),
                str(s["line_count"]),
                f"{err_color}{s['error_count']}{RESET}",
                f"{warn_color}{s['warning_count']}{RESET}",
                s["last_modified"],
            ))
        print(f"\n{BOLD}{BLUE}======================================================================{NC}\n")

    elif args.command == "tail":
        entries = tail_log(service=args.service, lines=args.lines)
        print(f"\n{CYAN}[*] Tail of {args.service.upper()} log ({len(entries)} lines):{RESET}")
        print("-" * 80)
        for line in entries:
            sys.stdout.write(line)
        print("-" * 80 + "\n")

    elif args.command == "query":
        results = query_logs(level=args.level, service=args.service, keyword=args.keyword, limit=args.limit)
        print(f"\n{CYAN}[*] Query found {len(results)} matching entries:{RESET}")
        print("-" * 80)
        for r in results:
            print(f"{GRAY}[{r['file']}]{RESET} {r['raw']}")
        print("-" * 80 + "\n")

    elif args.command == "audit":
        audit_records = query_audit_logs(
            operation=args.operation,
            service=args.service,
            status=args.status,
            trace_id=args.trace_id,
            limit=args.limit
        )
        print(f"\n{MAGENTA}[*] Audit Ledger found {len(audit_records)} records:{RESET}")
        print("-" * 80)
        for rec in audit_records:
            status_color = GREEN if rec.get("status") == "SUCCESS" else RED
            trace = f" [{rec.get('trace_id')}]" if rec.get("trace_id") else ""
            print(f"{GRAY}{rec.get('timestamp')}{RESET} {status_color}[{rec.get('status')}]{RESET} [{rec.get('service')}]{trace} {rec.get('operation')} ({rec.get('elapsed_sec')}s)")
            if rec.get("error"):
                print(f"  {RED}Error: {rec.get('error')}{RESET}")
        print("-" * 80 + "\n")

    elif args.command == "clean":
        res = clean_logs(confirm=args.confirm)
        if res.get("status") == "ok":
            print(f"{GREEN}[+] Successfully truncated {res['truncated_files']} log files ({res['freed_kb']} KB freed).{RESET}")
        else:
            print(f"{RED}[-] {res.get('message')}{RESET}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
