#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Shared Expansions - One-Click Client Installer & Synchronizer
=============================================================================
For Players / Other Users:
This script installs the custom card expansion (CDB & Lua effect scripts)
and story decklists (.ydk) directly into your local EDOPro / Project Ignis
or YGOPro game client directory so you can duel on the server.

Usage:
    python3 sync_client.py
Or:
    ./install_client.sh
=============================================================================
"""

import os
import sys
import shutil
import argparse
from typing import List, Optional

# Root of the shared package
SHARED_DIR = os.path.dirname(os.path.abspath(__file__))
EXPANSIONS_DIR = os.path.join(SHARED_DIR, "expansions")
CDB_FILE = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR = os.path.join(EXPANSIONS_DIR, "scripts")
DECKS_DIR = os.path.join(SHARED_DIR, "decks")

# Common default installation paths across platforms
CANDIDATE_PATHS = [
    # Linux
    os.path.expanduser("~/.local/share/EDOPro"),
    os.path.expanduser("~/EDOPro"),
    os.path.expanduser("~/.config/EDOPro"),
    "/opt/edopro",
    # macOS
    os.path.expanduser("~/Library/Application Support/EDOPro"),
    "/Applications/EDOPro.app/Contents/Resources",
    # Windows (WSL / cross-drive if mounted)
    "/mnt/c/Project Ignis/EDOPro",
    "/mnt/c/EDOPro",
    os.path.expandvars(r"C:\Project Ignis\EDOPro") if sys.platform == "win32" else "",
    os.path.expandvars(r"C:\EDOPro") if sys.platform == "win32" else "",
]


def find_game_directory() -> Optional[str]:
    """Scan candidate locations for an existing EDOPro/YGOPro installation."""
    for p in CANDIDATE_PATHS:
        if p and os.path.isdir(p):
            # Check for characteristic folders
            if os.path.isdir(os.path.join(p, "expansions")) or os.path.isdir(os.path.join(p, "deck")):
                return p
    return None


def install_to_client(client_dir: str):
    """Copies CDB, Lua scripts, and decks into the specified game client directory."""
    print(f"\n[*] Target Game Client: {client_dir}")

    # 1. Target folders
    target_expansions = os.path.join(client_dir, "expansions")
    target_scripts = os.path.join(target_expansions, "scripts")
    target_decks = os.path.join(client_dir, "deck")

    os.makedirs(target_scripts, exist_ok=True)
    os.makedirs(target_decks, exist_ok=True)

    # 2. Copy CDB
    if os.path.exists(CDB_FILE):
        dest_cdb = os.path.join(target_expansions, "custom_cards.cdb")
        shutil.copy2(CDB_FILE, dest_cdb)
        size_kb = os.path.getsize(dest_cdb) / 1024
        print(f"  [+] Installed custom_cards.cdb ({size_kb:.1f} KB) -> {dest_cdb}")
    else:
        print(f"  [-] Warning: custom_cards.cdb not found in {EXPANSIONS_DIR}")

    # 3. Copy Lua Effect Scripts
    if os.path.exists(SCRIPTS_DIR):
        scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")]
        for s in scripts:
            shutil.copy2(os.path.join(SCRIPTS_DIR, s), os.path.join(target_scripts, s))
        print(f"  [+] Installed {len(scripts)} Lua effect scripts -> {target_scripts}/")
    else:
        print(f"  [-] Warning: scripts directory not found in {EXPANSIONS_DIR}")

    # 4. Copy Decklists
    if os.path.exists(DECKS_DIR):
        decks = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")]
        for d in decks:
            shutil.copy2(os.path.join(DECKS_DIR, d), os.path.join(target_decks, d))
        print(f"  [+] Installed {len(decks)} sample/story decks -> {target_decks}/")

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! Custom cards and decks have been installed.")
    print("=" * 65)
    print("How to Duel:")
    print("1. Open your EDOPro / YGOPro client.")
    print("2. Navigate to: Multiplayer -> Duel Online.")
    print("3. Choose: Direct Connect / IP Connection:")
    print("     - Host: <Server IP or localhost>")
    print("     - Port: 7911")
    print("4. Select your custom deck and begin dueling!")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Install custom cards, scripts, and decks into your Yu-Gi-Oh! game client."
    )
    parser.add_argument(
        "--path", "-p",
        help="Path to your EDOPro / Project Ignis or YGOPro folder."
    )
    args = parser.parse_args()

    client_path = args.path
    if not client_path:
        detected = find_game_directory()
        if detected:
            print(f"[+] Detected game client at: {detected}")
            try:
                ans = input("Install custom expansions to this location? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = "y"
            if ans in ("", "y", "yes"):
                client_path = detected

    if not client_path:
        print("[-] Could not auto-detect your EDOPro/YGOPro directory.")
        try:
            client_path = input("Please enter the full path to your game client folder: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInstallation aborted.")
            sys.exit(1)

    client_path = os.path.expanduser(client_path)
    if not os.path.isdir(client_path):
        print(f"[-] Error: Directory does not exist: {client_path}")
        sys.exit(1)

    install_to_client(client_path)


if __name__ == "__main__":
    main()
