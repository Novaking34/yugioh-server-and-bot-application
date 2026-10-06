#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Player Client Expansion Installer & Synchronization Engine
=============================================================================
Core logic for synchronizing custom card expansions (CDB database and Lua effect
scripts) and pre-built character/story decklists (.ydk) with local game clients.

Supported Game Clients:
- EDOPro / Project Ignis (Windows, Linux, macOS, Steam Deck / Proton)
- YGOPro / KoishiPro / Dawn of a New Era
- Cross-platform Wine and Flatpak installations

Operational Modes:
1. Local Bundle Install (Offline / Default):
   Installs files directly from the packaged `expansions/` and `decks/` folders.
2. Remote HTTP/HTTPS Sync:
   Fetches the latest `custom_cards.cdb`, `scripts.zip`, and `.ydk` decklists
   from the live Web Catalog REST API without needing a full archive download.
=============================================================================
"""

import os
import sys
import json
import shutil
import argparse
import urllib.request
import urllib.error
import zipfile
import io
from typing import List, Dict, Any, Optional

# Canonical directory detection
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_DIR = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PACKAGE_DIR))

# Import authoritative client configuration
try:
    from .client_config import (
        CLIENT_CONFIG,
        CLIENT_SETTINGS,
        resolve_config_manifest,
        load_client_config,
    )
except ImportError:
    from client_config import (
        CLIENT_CONFIG,
        CLIENT_SETTINGS,
        resolve_config_manifest,
        load_client_config,
    )


# Resolve local expansion and deck paths (bundled package vs live repository)
EXPANSIONS_DIR = os.path.join(_PACKAGE_DIR, "expansions")
if not os.path.isdir(EXPANSIONS_DIR):
    repo_exp = os.path.join(_PROJECT_ROOT, "data", "expansions")
    if os.path.isdir(repo_exp):
        EXPANSIONS_DIR = repo_exp

CDB_FILE = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR = os.path.join(EXPANSIONS_DIR, "scripts")

DECKS_DIR = os.path.join(_PACKAGE_DIR, "decks")
if not os.path.isdir(DECKS_DIR):
    repo_decks = os.path.join(_PROJECT_ROOT, "data", "decks")
    if os.path.isdir(repo_decks):
        DECKS_DIR = repo_decks

# Common installation paths across Linux, Windows, macOS, Wine, and Steam Deck
CANDIDATE_PATHS: List[str] = [
    # Linux (Native, Flatpak, Snap, Wine)
    os.path.expanduser("~/.local/share/EDOPro"),
    os.path.expanduser("~/EDOPro"),
    os.path.expanduser("~/.config/EDOPro"),
    os.path.expanduser("~/.var/app/org.projectignis.EDOPro/data/EDOPro"),
    "/opt/edopro",
    "/opt/EDOPro",
    # macOS (Application Support & App Bundle Resources)
    os.path.expanduser("~/Library/Application Support/EDOPro"),
    "/Applications/EDOPro.app/Contents/Resources",
    # Windows native & WSL cross-drive mounts
    os.path.expandvars(r"C:\Project Ignis\EDOPro") if sys.platform == "win32" else "",
    os.path.expandvars(r"C:\EDOPro") if sys.platform == "win32" else "",
    os.path.expandvars(r"%LOCALAPPDATA%\Project Ignis\EDOPro") if sys.platform == "win32" else "",
    "/mnt/c/Project Ignis/EDOPro",
    "/mnt/c/EDOPro",
    # Steam Deck / Proton
    os.path.expanduser("~/.steam/steam/steamapps/compatdata/EDOPro/pfx/drive_c/Project Ignis/EDOPro"),
]


def find_game_directory() -> Optional[str]:
    """Scan standard filesystem locations for an existing EDOPro or YGOPro installation.
    
    Returns:
        Optional[str]: Verified game client directory path, or None if not found.
    """
    for path in CANDIDATE_PATHS:
        if path and os.path.isdir(path):
            # Verify characteristic directories or executables
            has_expansions = os.path.isdir(os.path.join(path, "expansions"))
            has_deck = os.path.isdir(os.path.join(path, "deck"))
            has_executable = (
                os.path.isfile(os.path.join(path, "EDOPro"))
                or os.path.isfile(os.path.join(path, "EDOPro.exe"))
                or os.path.isfile(os.path.join(path, "ygopro.exe"))
            )
            if (has_expansions and has_deck) or has_executable:
                return os.path.abspath(path)
    return None


def sync_from_remote(server_url: str, client_dir: str) -> bool:
    """Download CDB, Lua scripts zip, and decks directly from a remote Web Catalog server.
    
    Args:
        server_url (str): Base HTTP/HTTPS URL of the Web Catalog server.
        client_dir (str): Absolute filesystem path to the target game client directory.
        
    Returns:
        bool: True if synchronization succeeded completely, False otherwise.
    """
    server_url = server_url.rstrip("/")
    manifest_url = f"{server_url}/api/shared/manifest"
    print(f"\n[*] Connecting to remote server at: {manifest_url}...")

    try:
        headers = {"User-Agent": "YGO-Client-Sync/2.0 (The-Great-Kasutamaiza)"}
        req = urllib.request.Request(manifest_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[-] Failed to fetch manifest from {server_url}: {e}")
        return False

    print(f"[+] Connected! Remote card pool version: {manifest.get('version', '1.0.0')}")
    print(f"    Custom Cards Count : {manifest.get('card_count', 'N/A')}")
    print(f"    Lua Scripts Count  : {manifest.get('script_count', 'N/A')}")

    target_expansions = os.path.join(client_dir, "expansions")
    target_scripts = os.path.join(target_expansions, "scripts")
    target_decks = os.path.join(client_dir, "deck")
    os.makedirs(target_scripts, exist_ok=True)
    os.makedirs(target_decks, exist_ok=True)

    # 1. Download compiled custom_cards.cdb
    cdb_endpoint = manifest.get("cdb_download_url", "/api/shared/cdb")
    cdb_url = f"{server_url}{cdb_endpoint}"
    print(f"[*] Downloading custom_cards.cdb from: {cdb_url}...")
    dest_cdb = os.path.join(target_expansions, "custom_cards.cdb")
    try:
        req_cdb = urllib.request.Request(cdb_url, headers=headers)
        with urllib.request.urlopen(req_cdb, timeout=15) as resp, open(dest_cdb, "wb") as f_out:
            shutil.copyfileobj(resp, f_out)
        size_kb = os.path.getsize(dest_cdb) / 1024
        print(f"  [+] Saved {dest_cdb} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"  [-] Failed to download CDB: {e}")
        return False

    # 2. Download and extract Lua scripts zip archive
    scripts_endpoint = manifest.get("scripts_zip_url", "/api/shared/scripts_zip")
    scripts_url = f"{server_url}{scripts_endpoint}"
    print(f"[*] Downloading Lua effect scripts from: {scripts_url}...")
    try:
        req_scripts = urllib.request.Request(scripts_url, headers=headers)
        with urllib.request.urlopen(req_scripts, timeout=20) as resp:
            zip_bytes = resp.read()
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            zf.extractall(target_scripts)
            print(f"  [+] Extracted {len(zf.namelist())} Lua effect scripts to: {target_scripts}/")
    except Exception as e:
        print(f"  [-] Failed to download Lua scripts zip: {e}")
        return False

    # 3. Download pre-made story and archetype decklists
    decks_endpoint = manifest.get("decks_download_url", "/api/shared/decks")
    decks_api = f"{server_url}{decks_endpoint}"
    try:
        req_decks = urllib.request.Request(decks_api, headers=headers)
        with urllib.request.urlopen(req_decks, timeout=12) as resp:
            decks_list = json.loads(resp.read().decode("utf-8"))
        for d in decks_list:
            d_url = f"{server_url}{d['download_url']}"
            d_dest = os.path.join(target_decks, d["filename"])
            req_d = urllib.request.Request(d_url, headers=headers)
            with urllib.request.urlopen(req_d, timeout=10) as d_resp, open(d_dest, "wb") as d_out:
                shutil.copyfileobj(d_resp, d_out)
        print(f"  [+] Downloaded {len(decks_list)} story decks to: {target_decks}/")
    except Exception as e:
        print(f"  [!] Note: Could not fetch remote decklists: {e}")

    print_success_banner(CLIENT_CONFIG)
    return True


def install_to_client(client_dir: str, server_url: Optional[str] = None) -> bool:
    """Install CDB, Lua effect scripts, and decklists into a target game client.
    
    If `server_url` is provided, fetches the assets over HTTPS.
    Otherwise, installs bundled assets from the local package distribution.
    
    Args:
        client_dir (str): Absolute filesystem path to the target game client directory.
        server_url (Optional[str]): Optional remote server URL for online sync.
        
    Returns:
        bool: True if installation succeeded, False otherwise.
    """
    if server_url:
        return sync_from_remote(server_url, client_dir)

    print(f"\n[*] Target Game Client: {client_dir}")

    target_expansions = os.path.join(client_dir, "expansions")
    target_scripts = os.path.join(target_expansions, "scripts")
    target_decks = os.path.join(client_dir, "deck")

    os.makedirs(target_scripts, exist_ok=True)
    os.makedirs(target_decks, exist_ok=True)

    # 1. Install custom_cards.cdb
    if os.path.isfile(CDB_FILE):
        dest_cdb = os.path.join(target_expansions, "custom_cards.cdb")
        shutil.copy2(CDB_FILE, dest_cdb)
        size_kb = os.path.getsize(dest_cdb) / 1024
        print(f"  [+] Installed custom_cards.cdb ({size_kb:.1f} KB) -> {dest_cdb}")
    else:
        print(f"  [-] Warning: custom_cards.cdb not found in {EXPANSIONS_DIR}")

    # 2. Install Lua effect scripts
    if os.path.isdir(SCRIPTS_DIR):
        scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")]
        for s in scripts:
            shutil.copy2(os.path.join(SCRIPTS_DIR, s), os.path.join(target_scripts, s))
        print(f"  [+] Installed {len(scripts)} Lua effect scripts -> {target_scripts}/")
    else:
        print(f"  [-] Warning: scripts directory not found in {EXPANSIONS_DIR}")

    # 3. Install pre-made story and archetype decklists
    if os.path.isdir(DECKS_DIR):
        decks = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")]
        for d in decks:
            shutil.copy2(os.path.join(DECKS_DIR, d), os.path.join(target_decks, d))
        print(f"  [+] Installed {len(decks)} sample/story decks -> {target_decks}/")

    print_success_banner(CLIENT_CONFIG)
    return True


def print_success_banner(cfg: Dict[str, Any]) -> None:
    """Print formatted connection instructions and server endpoints."""
    host = cfg.get("server_host", "thelandofkustomazi.com")
    port = cfg.get("server_port", 7911)
    fallback = cfg.get("fallback_host", "thelandofkustomazi.duckdns.org")
    web_url = cfg.get("web_catalog_url", "https://thelandofkustomazi.com")

    print("\n" + "=" * 68)
    print("🎉 SUCCESS! Custom cards and decks have been successfully installed.")
    print("=" * 68)
    print("How to Duel Online:")
    print("  1. Open your EDOPro / Project Ignis or YGOPro client.")
    print("  2. Select: Multiplayer -> Duel Online.")
    print("  3. Choose: Direct Connect (or IP Connection):")
    print(f"       • Primary Host  : {host}")
    print(f"       • Duel Port     : {port}")
    print(f"       • Fallback Host : {fallback}")
    print("  4. Enter a room name to host, or leave blank to join an open match.")
    print(f"  5. Browse custom card lore & archetypes at: {web_url}")
    print("=" * 68 + "\n")


def main() -> None:
    """CLI argument parser and main interactive execution flow."""
    parser = argparse.ArgumentParser(
        description="Install custom cards, scripts, and decks into your Yu-Gi-Oh! game client."
    )
    parser.add_argument(
        "--path", "-p",
        help="Path to your EDOPro / Project Ignis or YGOPro directory."
    )
    parser.add_argument(
        "--server", "-s",
        help="Remote Web Catalog URL to synchronize cards over HTTPS (e.g. https://thelandofkustomazi.com)."
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

    # If --server is provided, or if the user wants remote sync
    server_target = args.server
    success = install_to_client(client_path, server_url=server_target)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
