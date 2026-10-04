#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Custom Server, Story Platform & Simulator - Master Controller
=============================================================================
Primary command-line interface (CLI) and orchestration engine for managing:
- Live Duel Simulator (Docker Compose) container lifecycle and network sockets
- Story database records (custom cards, lore sagas, duelists, decks)
- Binary CDB compilation and Lua effect script generation for EDOPro/YGOPro
- Duelingbook JSON card imports and character deck exports (.ydk)
- Automated testing (Pytest) and Lua effect script bytecode validation (luac)
- Service launchers (FastAPI web portal, modular Discord bot, desktop GUI)
- Cloudflare Tunnel connections and dynamic DNS synchronizers
- Release packaging and distribution bundling (.zip and .tar.gz in dist/)
- Automated platform environment installation and schema migrations

Usage:
    ./manage.sh [command] [args...]
    python3 manage.py [command] [args...]
    ygo-manage [command] [args...]
=============================================================================
"""

import sys
import os
import subprocess
import sqlite3
import argparse
import socket
import hashlib
from typing import List, Optional

# Ensure the repository root directory is present in sys.path for internal imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Centralized Path Definitions from config.paths
from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, DECKS_DIR,
    TOOLS_DIR, TESTS_DIR, APP_PY_PATH, BOT_DIR, SCHEMA_PATH,
    SEED_SCRIPT_PATH, PROD_MAIN_DIR, EXPANSIONS_DIR,
    PACKAGES_DIR, SERVER_PACKAGE_DIR, CLIENT_PACKAGE_DIR, DIST_DIR,
    ensure_directories
)

# Terminal ANSI Color & Text Formatting Constants
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m" # Reset / No Color


def print_header(title: str) -> None:
    """Print a visually distinct section header in bold blue.
    
    Args:
        title (str): Text to display inside the section header.
    """
    print(f"\n{BOLD}{BLUE}=== {title} ==={NC}")


def is_port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a TCP network port is currently open and listening.
    
    Args:
        host (str): Target hostname or IP address (e.g. '127.0.0.1').
        port (int): Target TCP port number (e.g. 8000, 7911).
        timeout (float): Connection timeout in seconds.
        
    Returns:
        bool: True if the connection was accepted, False otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def compute_sha256(file_path: str) -> str:
    """Compute the hexadecimal SHA-256 checksum of a file.
    
    Args:
        file_path (str): Absolute or relative path to the target file.
        
    Returns:
        str: 64-character hexadecimal SHA-256 digest string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


# =============================================================================
# SECTION 1: System Status & Diagnostic Inspector
# =============================================================================

def cmd_status() -> None:
    """Inspect and report the live status of all services, data stores, and containers.
    
    Checks:
    1. Live Simulator Container: Queries docker ps for ygo-simulator-server.
    2. Story Database: Queries SQLite for custom cards, factions, characters, and decks.
    3. Expansions Pool: Checks compiled custom_cards.cdb, Lua scripts, and story .ydk decks.
    4. Service Health: Checks Web Catalog (port 8000), Duel Engine (port 7911), and Room Manager (port 7922).
    5. Environment & Credentials: Verifies tokens for Discord bot, DuckDNS, and Cloudflare.
    """
    print(f"{BOLD}=== 🌌 Yu-Gi-Oh! Story & Simulator Platform Status ==={NC}")

    # 1. Live Simulator Container Status
    print(f"\n{BLUE}>> Live Duel Simulator Container (docker compose):{NC}")
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", "name=ygo-simulator-server", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, check=False
        )
        if res.stdout.strip():
            print(res.stdout.strip())
        else:
            print(f"   • {YELLOW}Container not running.{NC} Run: ./manage.sh start")
    except Exception as e:
        print(f"   • {RED}Docker check unavailable:{NC} {e}")

    # 2. Network Services Listener Health
    print(f"\n{BLUE}>> Local Service Port Health:{NC}")
    sim_port_open = is_port_listening("127.0.0.1", 7911)
    room_port_open = is_port_listening("127.0.0.1", 7922)
    web_port_open = is_port_listening("127.0.0.1", 8000)

    print(f"   • Duel Simulator (TCP 7911)  : {'[ACTIVE]' if sim_port_open else '[OFFLINE]'}")
    print(f"   • Web Room Manager (TCP 7922): {'[ACTIVE]' if room_port_open else '[OFFLINE]'}")
    print(f"   • Web Catalog API (TCP 8000) : {'[ACTIVE]' if web_port_open else '[OFFLINE]'}")

    # 3. Database Statistics
    print(f"\n{BLUE}>> Story Database Statistics ({os.path.relpath(STORY_DB_PATH, BASE_DIR)}):{NC}")
    if os.path.exists(STORY_DB_PATH):
        try:
            conn = sqlite3.connect(STORY_DB_PATH)
            cur = conn.cursor()
            cards_count = cur.execute("SELECT COUNT(*) FROM custom_cards").fetchone()[0]
            factions_count = cur.execute("SELECT COUNT(*) FROM factions").fetchone()[0]
            chars_count = cur.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
            decks_count = cur.execute("SELECT COUNT(*) FROM decks").fetchone()[0]
            player_decks_count = cur.execute("SELECT COUNT(DISTINCT user_id) FROM player_decks").fetchone()[0]
            conn.close()

            print(f"   • Custom Cards in Pool : {cards_count}")
            print(f"   • Factions / Archetypes: {factions_count}")
            print(f"   • Story Duelists       : {chars_count}")
            print(f"   • Pre-made Story Decks : {decks_count}")
            print(f"   • Active Player Decks  : {player_decks_count}")
        except Exception as e:
            print(f"   • {RED}Error querying database:{NC} {e}")
    else:
        print(f"   • {YELLOW}Database file not found at {STORY_DB_PATH}. Run: ./manage.sh install{NC}")

    # 4. Expansions & Shared Distribution Status
    print(f"\n{BLUE}>> Shared Client Distribution Status (production/shared):{NC}")
    if os.path.exists(CDB_OUTPUT_PATH):
        size_kb = os.path.getsize(CDB_OUTPUT_PATH) / 1024
        print(f"   • Compiled CDB: {os.path.relpath(CDB_OUTPUT_PATH, BASE_DIR)} ({size_kb:.1f} KB)")
    else:
        print(f"   • {YELLOW}Compiled CDB not found. Run: ./manage.sh sync{NC}")

    if os.path.exists(SCRIPTS_DIR):
        lua_files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")]
        print(f"   • Lua Effect Scripts: {len(lua_files)} files in {os.path.relpath(SCRIPTS_DIR, BASE_DIR)}/")
    else:
        print(f"   • {YELLOW}Lua scripts directory not found.{NC}")

    if os.path.exists(DECKS_DIR):
        ydk_files = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")]
        print(f"   • Shared Story Decks: {len(ydk_files)} .ydk files in {os.path.relpath(DECKS_DIR, BASE_DIR)}/")

    # 5. Environment & Credentials Configuration
    env_file = os.path.join(BASE_DIR, ".env")
    print(f"\n{BLUE}>> Environment Configuration (.env):{NC}")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()
        has_bot = bool("DISCORD_BOT_TOKEN=" in content and 'DISCORD_BOT_TOKEN=""' not in content)
        has_duck = bool("DUCKDNS_TOKEN=" in content and 'DUCKDNS_TOKEN=""' not in content)
        has_cf = bool("CLOUDFLARE_TUNNEL_TOKEN=" in content and 'CLOUDFLARE_TUNNEL_TOKEN=""' not in content)
        print(f"   • Discord Bot Token     : {'[CONFIGURED]' if has_bot else '[MISSING]'}")
        print(f"   • DuckDNS Dynamic Token : {'[CONFIGURED]' if has_duck else '[NOT SET]'}")
        print(f"   • Cloudflare Tunnel Token: {'[CONFIGURED]' if has_cf else '[NOT SET]'}")
    else:
        print(f"   • {YELLOW}.env file not found. Copy from .env.example or run ./manage.sh install{NC}")

    # 6. Release Distribution Archives in dist/
    if os.path.exists(DIST_DIR):
        archives = [f for f in os.listdir(DIST_DIR) if f.endswith((".zip", ".tar.gz"))]
        if archives:
            print(f"\n{BLUE}>> Built Release Packages (dist/):{NC}")
            for a in archives:
                a_path = os.path.join(DIST_DIR, a)
                a_size = os.path.getsize(a_path) / 1024
                print(f"   • {a} ({a_size:.1f} KB)")

    print()


# =============================================================================
# SECTION 2: Docker Container Management (Simulator Engine)
# =============================================================================

def cmd_start() -> int:
    """Start the live ocgcore simulator container using Docker Compose.
    
    Returns:
        int: Subprocess returncode (0 on success).
    """
    print(f"{BLUE}[*] Starting Yu-Gi-Oh! Live Duel Simulator container...{NC}")
    res = subprocess.run(["docker", "compose", "up", "-d"], cwd=BASE_DIR)
    if res.returncode == 0:
        print(f"{GREEN}[+] Duel Simulator active and listening on:{NC}")
        print("    - Game Client TCP: localhost:7911 (or your LAN/VPN IP for EDOPro / YGOPro)")
        print("    - Web Room Manager: http://localhost:7922")
    else:
        print(f"{RED}[-] Failed to start simulator container. Ensure Docker daemon is running.{NC}")
    return res.returncode


def cmd_stop() -> int:
    """Stop the live ocgcore simulator container using Docker Compose.
    
    Returns:
        int: Subprocess returncode (0 on success).
    """
    print(f"{YELLOW}[*] Stopping Yu-Gi-Oh! Live Duel Simulator container...{NC}")
    res = subprocess.run(["docker", "compose", "down"], cwd=BASE_DIR)
    if res.returncode == 0:
        print(f"{GREEN}[+] Simulator stopped successfully.{NC}")
    return res.returncode


def cmd_restart() -> int:
    """Restart the live ocgcore simulator container using Docker Compose.
    
    Returns:
        int: Subprocess returncode (0 on success).
    """
    print(f"{BLUE}[*] Restarting Yu-Gi-Oh! Live Duel Simulator container...{NC}")
    res = subprocess.run(["docker", "compose", "restart"], cwd=BASE_DIR)
    if res.returncode == 0:
        print(f"{GREEN}[+] Simulator restarted successfully.{NC}")
    return res.returncode


# =============================================================================
# SECTION 3: Database & Simulator Expansion Synchronization
# =============================================================================

def cmd_sync() -> None:
    """Rebuild the shared custom_cards.cdb SQLite database and regenerate Lua scripts.
    
    Reads from the live story database (ygo_story.db) and compiles:
    1. custom_cards.cdb binary SQLite database matching ocgcore specifications.
    2. Lua effect scripts (c<id>.lua) for all registered custom cards.
    """
    print(f"{BLUE}[*] Synchronizing Story Database with Simulator CDB and Lua scripts...{NC}")
    ensure_directories()
    sys.path.insert(0, TOOLS_DIR)

    from cdb_builder import build_cdb
    from lua_generator import generate_all_scripts

    card_count = build_cdb()
    script_count = generate_all_scripts()
    print(f"{GREEN}[+] Sync complete: {card_count} cards compiled to CDB, {script_count} Lua scripts generated.{NC}")


# =============================================================================
# SECTION 4: Card Importing & Deck Exporting Pipelines
# =============================================================================

def cmd_import(file_path: str) -> None:
    """Import custom cards from a Duelingbook JSON export file into database and CDB.
    
    Args:
        file_path (str): Path to the Duelingbook JSON export file.
    """
    if not file_path:
        print(f"{RED}[-] Error: Please specify the path to a Duelingbook JSON export file.{NC}")
        print("    Usage: ./manage.sh import /path/to/cards.json")
        sys.exit(1)
    if not os.path.exists(file_path):
        print(f"{RED}[-] Error: File not found: {file_path}{NC}")
        sys.exit(1)

    print(f"{BLUE}[*] Importing Duelingbook cards from {file_path}...{NC}")
    sys.path.insert(0, TOOLS_DIR)
    from duelingbook_importer import import_from_json_file
    imported_ids = import_from_json_file(file_path, sync_simulator=True)
    print(f"{GREEN}[+] Imported and synchronized {len(imported_ids)} custom cards!{NC}")


def cmd_export_decks() -> None:
    """Export all pre-made character story decks to standard .ydk deck files."""
    print(f"{BLUE}[*] Exporting character story decks to {os.path.relpath(DECKS_DIR, BASE_DIR)}/...{NC}")
    sys.path.insert(0, TOOLS_DIR)
    from export_deck import export_all_decks
    export_all_decks()
    print(f"{GREEN}[+] Story deck export completed.{NC}")


def cmd_export_player(user_id: str) -> None:
    """Export a specific player's custom deck to a standard .ydk deck file.
    
    Args:
        user_id (str): Discord user identifier of the player.
    """
    if not user_id:
        print(f"{RED}[-] Error: Please specify a Discord User ID.{NC}")
        print("    Usage: ./manage.sh export-player <discord_user_id>")
        sys.exit(1)
    print(f"{BLUE}[*] Exporting player deck for user {user_id}...{NC}")
    sys.path.insert(0, TOOLS_DIR)
    from export_deck import export_player_deck
    res = export_player_deck(user_id)
    if res:
        print(f"{GREEN}[+] Exported successfully to {res}{NC}")
    else:
        print(f"{YELLOW}[!] No cards found in player deck for user {user_id}.{NC}")


# =============================================================================
# SECTION 5: Automated Testing & Lua Syntax Validation
# =============================================================================

def cmd_test(extra_args: Optional[List[str]] = None) -> int:
    """Execute the Pytest test suite on development/tests.
    
    Args:
        extra_args (Optional[List[str]]): Additional arguments forwarded to pytest.
        
    Returns:
        int: Pytest exit code (0 for all tests passing).
    """
    print(f"{BLUE}[*] Running Unit Test Suite with Pytest...{NC}")
    pytest_bin = os.path.join(BASE_DIR, "venv", "bin", "pytest")
    if not os.path.exists(pytest_bin):
        pytest_bin = "pytest"
    args = [pytest_bin, "-v", TESTS_DIR] + (extra_args or [])
    res = subprocess.run(args, cwd=BASE_DIR)
    return res.returncode


def cmd_validate_lua() -> int:
    """Validate syntax of all generated Lua card scripts using luac compiler.
    
    Returns:
        int: 0 if all scripts are syntactically valid, non-zero on errors.
    """
    print(f"{BLUE}[*] Validating all generated Lua effect scripts...{NC}")
    lua_files = [
        os.path.join(SCRIPTS_DIR, f)
        for f in os.listdir(SCRIPTS_DIR)
        if f.endswith(".lua")
    ] if os.path.exists(SCRIPTS_DIR) else []

    if not lua_files:
        print(f"{YELLOW}[!] No Lua scripts found in {SCRIPTS_DIR}. Run: ./manage.sh sync{NC}")
        return 0

    luac_path = subprocess.run(["which", "luac"], capture_output=True, text=True).stdout.strip()
    if luac_path:
        res = subprocess.run([luac_path, "-p"] + lua_files, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"{GREEN}[+] All {len(lua_files)} Lua scripts passed syntax validation without errors!{NC}")
            return 0
        else:
            print(f"{RED}[-] Lua syntax errors detected:\n{res.stderr}{NC}")
            return res.returncode
    else:
        print(f"{YELLOW}[!] luac compiler not found on host. Verifying non-emptiness of scripts...{NC}")
        valid = sum(1 for f in lua_files if os.path.getsize(f) > 50)
        print(f"{GREEN}[+] Verified {valid}/{len(lua_files)} Lua scripts exist and have content.{NC}")
        print("    (To install luac: sudo apt-get install lua5.3)")
        return 0


# =============================================================================
# SECTION 6: Service & Application Launchers
# =============================================================================

def cmd_web() -> None:
    """Launch the FastAPI Web Catalog Dashboard & REST API server on port 8000."""
    print(f"{BLUE}[*] Launching Web Catalog & Lore Dashboard on http://localhost:8000...{NC}")
    uvicorn_bin = os.path.join(BASE_DIR, "venv", "bin", "uvicorn")
    if not os.path.exists(uvicorn_bin):
        uvicorn_bin = "uvicorn"
    os.execv(
        uvicorn_bin,
        [uvicorn_bin, "production.main.web.api_server:app", "--app-dir", BASE_DIR, "--host", "0.0.0.0", "--port", "8000", "--reload"]
    )


def cmd_bot() -> None:
    """Launch The Great Kasutamaiza modular Discord Story & Duel Bot."""
    print(f"{BLUE}[*] Starting Modular Yu-Gi-Oh! Story & Duel Discord Bot...{NC}")
    python_bin = os.path.join(BASE_DIR, "venv", "bin", "python3")
    if not os.path.exists(python_bin):
        python_bin = sys.executable
    bot_script = os.path.join(BOT_DIR, "bot.py")
    os.execv(python_bin, [python_bin, "-u", bot_script])


def cmd_app() -> None:
    """Launch the native Desktop GUI Platform Manager."""
    print(f"{BLUE}[*] Launching Yu-Gi-Oh! Platform Manager Desktop Application...{NC}")
    python_bin = os.path.join(BASE_DIR, "venv", "bin", "python3")
    if not os.path.exists(python_bin):
        python_bin = sys.executable
    os.execv(python_bin, [python_bin, APP_PY_PATH])


def cmd_tunnel(extra: Optional[List[str]] = None) -> None:
    """Launch or manage the Cloudflare HTTPS Tunnel for remote card syncing.
    
    Args:
        extra (Optional[List[str]]): Additional arguments forwarded to setup_cloudflare_tunnel script.
    """
    scripts_dir = os.path.join(SERVER_PACKAGE_DIR, "scripts")
    if sys.platform == "win32":
        tunnel_script = os.path.join(scripts_dir, "setup_cloudflare_tunnel.bat")
        if not os.path.exists(tunnel_script):
            tunnel_script = os.path.join(PROD_MAIN_DIR, "setup_cloudflare_tunnel.bat")
    else:
        tunnel_script = os.path.join(scripts_dir, "setup_cloudflare_tunnel.sh")
        if not os.path.exists(tunnel_script):
            tunnel_script = os.path.join(PROD_MAIN_DIR, "setup_cloudflare_tunnel.sh")

    if not os.path.exists(tunnel_script):
        print(f"{RED}[-] Error: Cloudflare Tunnel script not found at {tunnel_script}.{NC}")
        sys.exit(1)

    args = [tunnel_script] + (extra or [])
    if sys.platform == "win32":
        res = subprocess.run(args)
        sys.exit(res.returncode)
    else:
        os.execv(tunnel_script, args)


# =============================================================================
# SECTION 7: Distribution Packaging & Release Bundler
# =============================================================================

def cmd_package() -> None:
    """Build standalone, self-contained distribution packages in dist/.
    
    Generates:
    1. dist/ygo-client-package.zip: Player distribution package containing
       one-click installers (Windows/Linux), launchers, sync engine, compiled
       custom_cards.cdb, all Lua effect scripts, decks, and documentation.
    2. dist/ygo-server-package.tar.gz: Host server deployment package containing
       cloud automation scripts, systemd units, Docker Compose manifest, DuckDNS
       updater, and DNS zone configurations.
    3. dist/SHA256SUMS.txt: Checksum file for package verification.
    """
    import zipfile
    import tarfile

    print(f"{BOLD}{BLUE}====================================================================={NC}")
    print(f"{BOLD}{BLUE}  📦 Yu-Gi-Oh! Platform Packaging & Distribution Release Builder      ${NC}")
    print(f"{BOLD}{BLUE}====================================================================={NC}\n")
    ensure_directories()

    # Step 1: Ensure expansions and decks are freshly compiled
    cmd_sync()
    cmd_export_decks()

    os.makedirs(DIST_DIR, exist_ok=True)
    client_zip_path = os.path.join(DIST_DIR, "ygo-client-package.zip")
    server_tar_path = os.path.join(DIST_DIR, "ygo-server-package.tar.gz")
    checksums_path = os.path.join(DIST_DIR, "SHA256SUMS.txt")

    # Step 2: Build Player Client Package (.zip)
    print(f"\n{BLUE}[*] Packaging Player Client Distribution -> {os.path.relpath(client_zip_path, BASE_DIR)}...{NC}")
    with zipfile.ZipFile(client_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add client installer files from packages/client/ (excluding bytecode caches)
        for root, dirs, files in os.walk(CLIENT_PACKAGE_DIR):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in sorted(files):
                if file.endswith((".pyc", ".pyo")):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.join("ygo-client-package", os.path.relpath(file_path, CLIENT_PACKAGE_DIR))
                zf.write(file_path, arcname)

        # Add compiled custom card expansions (CDB and Lua scripts)
        if os.path.exists(EXPANSIONS_DIR):
            for root, dirs, files in os.walk(EXPANSIONS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join("ygo-client-package", "expansions", os.path.relpath(file_path, EXPANSIONS_DIR))
                    zf.write(file_path, arcname)

        # Add pre-made story and character decks (.ydk)
        if os.path.exists(DECKS_DIR):
            for root, dirs, files in os.walk(DECKS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join("ygo-client-package", "decks", os.path.relpath(file_path, DECKS_DIR))
                    zf.write(file_path, arcname)

    client_size_mb = os.path.getsize(client_zip_path) / (1024 * 1024)
    client_sha = compute_sha256(client_zip_path)
    print(f"{GREEN}[+] Client package built: {client_zip_path} ({client_size_mb:.2f} MB){NC}")
    print(f"    SHA-256: {client_sha}")

    # Step 3: Build Host Server Package (.tar.gz)
    print(f"\n{BLUE}[*] Packaging Host Server Deployment -> {os.path.relpath(server_tar_path, BASE_DIR)}...{NC}")
    with tarfile.open(server_tar_path, "w:gz", dereference=True) as tf:
        tf.add(SERVER_PACKAGE_DIR, arcname="ygo-server-package")

    server_size_kb = os.path.getsize(server_tar_path) / 1024
    server_sha = compute_sha256(server_tar_path)
    print(f"{GREEN}[+] Server package built: {server_tar_path} ({server_size_kb:.1f} KB){NC}")
    print(f"    SHA-256: {server_sha}")

    # Step 4: Write Checksum File
    with open(checksums_path, "w", encoding="utf-8") as f:
        f.write(f"{client_sha}  ygo-client-package.zip\n")
        f.write(f"{server_sha}  ygo-server-package.tar.gz\n")
    print(f"{GREEN}[+] Checksums written to {os.path.relpath(checksums_path, BASE_DIR)}{NC}")

    print(f"\n{BOLD}{GREEN}====================================================================={NC}")
    print(f"{BOLD}{GREEN}  🎉 RELEASE PACKAGING COMPLETE!                                     ${NC}")
    print(f"{BOLD}{GREEN}====================================================================={NC}")
    print(f"  • {BOLD}Player Client Archive:{NC}  {client_zip_path}")
    print(f"    Distribution: Share with players (unzip and run install_client.bat or install_client.sh)")
    print(f"  • {BOLD}Host Server Archive:{NC}    {server_tar_path}")
    print(f"    Deployment:   Deploy on any Ubuntu/Debian VPS (extract and run sudo ./deploy_oracle_cloud.sh)")
    print(f"  • {BOLD}Verification:{NC}          {checksums_path}\n")


# =============================================================================
# SECTION 8: Platform Installation & Environment Initializer
# =============================================================================

def cmd_install() -> None:
    """Initialize directory layout, database schema, story seeds, CDB, and Lua scripts."""
    print(f"{BOLD}{BLUE}[*] Initializing Yu-Gi-Oh! Platform Environment...{NC}")
    ensure_directories()
    print(f"{GREEN}[+] Directory structure verified.{NC}")

    # Check and initialize database
    if not os.path.exists(STORY_DB_PATH):
        print(f"{BLUE}[*] Initializing database from schema and seeding initial story data...{NC}")
        sys.path.insert(0, os.path.join(BASE_DIR, "development", "database"))
        import seed_story_data
        seed_story_data.initialize_database()
        print(f"{GREEN}[+] Database initialized successfully.{NC}")
    else:
        print(f"{GREEN}[+] Story database already present.{NC}")

    # Rebuild custom_cards.cdb and Lua scripts
    cmd_sync()
    cmd_export_decks()

    print(f"\n{BOLD}{GREEN}[🎉] Installation & Setup Complete!{NC}")
    print("You can now manage the platform using:")
    print("  ./manage.sh start      # Starts live duel simulator (Port 7911 / 7922)")
    print("  ./manage.sh web        # Starts web catalog dashboard (Port 8000)")
    print("  ./manage.sh bot        # Starts Discord bot")
    print("  ./manage.sh tunnel     # Launches Cloudflare HTTPS Tunnel for Web Catalog")
    print("  ./manage.sh package    # Bundles client (.zip) and server (.tar.gz) release packages")
    print("  ./manage.sh app        # Starts Desktop GUI Platform Manager")
    print("  ./manage.sh status     # Checks comprehensive platform status")


def cmd_diagnose(extra_args: Optional[List[str]] = None) -> int:
    """Run comprehensive platform diagnostic auditor and failpoint inspector."""
    print_header("Platform Diagnostics & Failpoint Auditor")
    from development.tools.debug_diagnostics import PlatformDiagnostics, print_diagnostic_report
    diag = PlatformDiagnostics()
    results = diag.run_all()
    return print_diagnostic_report(results)


def cmd_logs(extra_args: Optional[List[str]] = None) -> None:
    """Inspect and manage multi-target platform logs via config.logging.log_tool."""
    from config.logging import log_tool
    sys.argv = ["log_tool"] + (extra_args if extra_args else ["stats"])
    log_tool.main()


def cmd_tracker(extra_args: Optional[List[str]] = None) -> None:
    """Manage master card tracker, Google Sheets export, and artwork downloads."""
    from development.tools import tracker_sync
    sys.argv = ["tracker_sync"] + (extra_args if extra_args else ["verify"])
    tracker_sync.main()


def cmd_sync_vm(extra_args: Optional[List[str]] = None) -> int:
    """Synchronizes code, database, and bot services to the live Oracle Cloud VM."""
    script_path = os.path.join(BASE_DIR, "scripts", "sync_oracle_vm.sh")
    if not os.path.exists(script_path):
        print(f"{RED}[!] Script not found at: {script_path}{NC}")
        return 1
    cmd = [script_path] + (extra_args or [])
    res = subprocess.run(cmd, cwd=BASE_DIR)
    return res.returncode


# =============================================================================
# SECTION 9: CLI Argument Parser & Router
# =============================================================================

def main() -> None:
    """Master command-line entry point and dispatch router."""
    parser = argparse.ArgumentParser(
        description="Yu-Gi-Oh! Story & Simulator Platform Master Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Platform Commands:
  status                Display container, database, port, and expansion status
  start                 Start live simulator container (Port 7911 / 7922)
  stop                  Stop live simulator container
  restart               Restart live simulator container
  sync                  Rebuild simulator custom_cards.cdb and Lua effect scripts
  sync-vm [msg...]      Sync code & services to Oracle Cloud VM (147.224.147.30)
  diagnose [args...]    Run system diagnostics and failpoint inspection tool
  logs [subcommand...]  Inspect logs (stats, tail -s <service>, query, clean)
  tracker [action...]   Manage Google Sheets tracker (upgrade, import, download-images, verify)
  import <file.json>    Import Duelingbook JSON cards into database and simulator
  export-decks          Export character story decks to standard .ydk format
  export-player <uid>   Export a Discord player's active deck to .ydk format
  test [args...]        Run the comprehensive Pytest test suite
  validate-lua          Verify syntax of all generated Lua scripts
  web                   Start local web card catalog & dashboard (Port 8000)
  bot                   Launch modular Discord story & duel bot
  tunnel [options...]   Launch Cloudflare HTTPS Tunnel for Web Catalog & Sync
  package               Build standalone distribution packages in dist/
  app                   Launch native desktop control panel application
  install               Initialize directory layout, database, CDB, and Lua scripts
        """
    )
    parser.add_argument("command", nargs="?", default="status", help="Command to execute")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Additional arguments for the command")

    if len(sys.argv) == 1:
        cmd_status()
        return

    cmd = sys.argv[1]
    extra = sys.argv[2:]

    if cmd == "status":
        cmd_status()
    elif cmd == "start":
        sys.exit(cmd_start())
    elif cmd == "stop":
        sys.exit(cmd_stop())
    elif cmd == "restart":
        sys.exit(cmd_restart())
    elif cmd == "sync":
        cmd_sync()
    elif cmd in ("sync-vm", "sync_vm", "deploy-vm", "deploy"):
        sys.exit(cmd_sync_vm(extra))
    elif cmd in ("diagnose", "diag", "debug"):
        sys.exit(cmd_diagnose(extra))
    elif cmd in ("logs", "log"):
        cmd_logs(extra)
    elif cmd in ("tracker", "sheets"):
        cmd_tracker(extra)
    elif cmd == "import":
        cmd_import(extra[0] if extra else "")
    elif cmd == "export-decks":
        cmd_export_decks()
    elif cmd == "export-player":
        cmd_export_player(extra[0] if extra else "")
    elif cmd == "test":
        sys.exit(cmd_test(extra))
    elif cmd == "validate-lua":
        sys.exit(cmd_validate_lua())
    elif cmd == "web":
        cmd_web()
    elif cmd == "bot":
        cmd_bot()
    elif cmd == "tunnel":
        cmd_tunnel(extra)
    elif cmd in ("package", "bundle", "dist"):
        cmd_package()
    elif cmd in ("app", "gui"):
        cmd_app()
    elif cmd in ("install", "setup"):
        cmd_install()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
