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


def sync_from_remote(server_url: str, client_dir: str):
    """Downloads CDB, scripts zip, and decks directly from a remote web catalog server."""
    import urllib.request
    import json
    import zipfile
    import io

    server_url = server_url.rstrip("/")
    manifest_url = f"{server_url}/api/shared/manifest"
    print(f"\n[*] Connecting to remote server at {manifest_url}...")

    try:
        req = urllib.request.Request(manifest_url, headers={"User-Agent": "YGO-Client-Sync/1.2"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] Failed to fetch manifest from {server_url}: {e}")
        return False

    print(f"[+] Connected! Remote card manifest: version {manifest.get('version')}")

    target_expansions = os.path.join(client_dir, "expansions")
    target_scripts = os.path.join(target_expansions, "scripts")
    target_decks = os.path.join(client_dir, "deck")
    os.makedirs(target_scripts, exist_ok=True)
    os.makedirs(target_decks, exist_ok=True)

    # 1. Download CDB
    cdb_url = f"{server_url}{manifest.get('cdb_download_url', '/api/shared/cdb')}"
    print(f"[*] Downloading custom_cards.cdb from {cdb_url}...")
    dest_cdb = os.path.join(target_expansions, "custom_cards.cdb")
    urllib.request.urlretrieve(cdb_url, dest_cdb)
    size_kb = os.path.getsize(dest_cdb) / 1024
    print(f"  [+] Saved {dest_cdb} ({size_kb:.1f} KB)")

    # 2. Download and extract Lua scripts zip
    scripts_url = f"{server_url}{manifest.get('scripts_zip_url', '/api/shared/scripts_zip')}"
    print(f"[*] Downloading Lua effect scripts from {scripts_url}...")
    with urllib.request.urlopen(scripts_url, timeout=15) as resp:
        zip_data = resp.read()
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zf.extractall(target_scripts)
        print(f"  [+] Extracted {len(zf.namelist())} Lua scripts to {target_scripts}/")

    # 3. Download decklists
    decks_api = f"{server_url}{manifest.get('decks_download_url', '/api/shared/decks')}"
    try:
        with urllib.request.urlopen(decks_api, timeout=10) as resp:
            decks_list = json.loads(resp.read().decode("utf-8"))
        for d in decks_list:
            d_url = f"{server_url}{d['download_url']}"
            d_dest = os.path.join(target_decks, d['filename'])
            urllib.request.urlretrieve(d_url, d_dest)
        print(f"  [+] Downloaded {len(decks_list)} decks to {target_decks}/")
    except Exception as e:
        print(f"  [!] Note: could not fetch remote deck list: {e}")

    print("\n" + "=" * 65)
    print("🎉 SUCCESS! Remote custom card pool has been synchronized.")
    print("=" * 65)
    return True


def install_to_client(client_dir: str, server_url: Optional[str] = None):
    """Copies CDB, Lua scripts, and decks from local shared package or remote server."""
    if server_url:
        return sync_from_remote(server_url, client_dir)

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
