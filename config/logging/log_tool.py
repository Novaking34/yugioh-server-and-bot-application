#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Log Inspector & Telemetry Management Tool
=============================================================================
A dedicated utility for querying, inspecting, filtering, and managing log
streams across all platform subsystems (web, bot, simulator, gui, tools, etc.).

Usage (CLI):
    python3 -m config.logging.log_tool stats
    python3 -m config.logging.log_tool tail --service web -n 30
    python3 -m config.logging.log_tool query --level ERROR --limit 20
    python3 -m config.logging.log_tool clean --confirm

Usage (Python API):
    from config.logging import get_log_stats, tail_log, query_logs
=============================================================================
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Optional

# Ensure repository root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import LOGS_DIR


# Terminal color constants
RESET = "\033[0m"
NC = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
GRAY = "\033[0;90m"


def get_log_stats() -> List[Dict[str, Any]]:
    """
    Scans the `logs/` directory and returns metadata, file size, line counts,
    and error counts for every log file.
    """
    stats = []
    if not os.path.exists(LOGS_DIR):
        return stats

    for fname in sorted(os.listdir(LOGS_DIR)):
        if not fname.endswith(".log"):
            continue

        fpath = os.path.join(LOGS_DIR, fname)
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
                    if " [ERROR] " in line or '"level": "ERROR"' in line or "CRITICAL" in line:
                        error_count += 1
                    elif " [WARNING] " in line or '"level": "WARNING"' in line:
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


def tail_log(service: str = "combined", lines: int = 50) -> List[str]:
    """
    Returns the last `lines` entries from the target service's log file.
    """
    if not os.path.exists(LOGS_DIR):
        return []

    service_lower = service.lower().replace("-", "_")
    target_file = os.path.join(LOGS_DIR, f"{service_lower}.log")

    if not os.path.exists(target_file):
        # Fall back to combined
        target_file = os.path.join(LOGS_DIR, "combined.log")
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


def query_logs(
    level: Optional[str] = None,
    service: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Searches across combined.log (or a specific service log) filtering by
    severity level, service identifier, or text keywords.
    """
    results: List[Dict[str, Any]] = []
    if not os.path.exists(LOGS_DIR):
        return results

    if service:
        fpath = os.path.join(LOGS_DIR, f"{service.lower()}.log")
        files_to_scan = [fpath] if os.path.exists(fpath) else []
    else:
        combined = os.path.join(LOGS_DIR, "combined.log")
        files_to_scan = [combined] if os.path.exists(combined) else []

    if not files_to_scan:
        return results

    level_upper = level.upper() if level else None
    kw_lower = keyword.lower() if keyword else None

    for target_path in files_to_scan:
        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    # Filter by level
                    if level_upper and f" [{level_upper}] " not in line and f'"level": "{level_upper}"' not in line:
                        continue

                    # Filter by keyword
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


def clean_logs(confirm: bool = False) -> Dict[str, Any]:
    """
    Safely purges or truncates old log files in `logs/`.
    Requires `confirm=True` to execute.
    """
    if not confirm:
        return {"status": "aborted", "message": "Confirmation required (pass --confirm)"}

    if not os.path.exists(LOGS_DIR):
        return {"status": "ok", "truncated_files": 0, "freed_bytes": 0}

    freed = 0
    truncated = 0
    for fname in os.listdir(LOGS_DIR):
        if fname.endswith(".log"):
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


def main():
    parser = argparse.ArgumentParser(
        description="Yu-Gi-Oh! Platform Logging Telemetry & Audit Utility"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # stats
    subparsers.add_parser("stats", help="Display storage statistics across all service log files")

    # tail
    tail_parser = subparsers.add_parser("tail", help="Display the most recent log entries")
    tail_parser.add_argument("-s", "--service", default="combined", help="Target service (e.g. web, bot, simulator, tools)")
    tail_parser.add_argument("-n", "--lines", type=int, default=30, help="Number of lines to display")

    # query
    query_parser = subparsers.add_parser("query", help="Filter and query logs by level or keyword")
    query_parser.add_argument("-l", "--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Log severity level")
    query_parser.add_argument("-s", "--service", help="Filter by specific service name")
    query_parser.add_argument("-k", "--keyword", help="Text keyword to match")
    query_parser.add_argument("--limit", type=int, default=50, help="Maximum entries to return")

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

        fmt = "{:<20} {:<10} {:<10} {:<10} {:<10} {:<20}"
        print(f"{BOLD}" + fmt.format("LOG FILE", "SIZE (KB)", "LINES", "ERRORS", "WARNINGS", "LAST MODIFIED") + f"{RESET}")
        print("-" * 80)
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
