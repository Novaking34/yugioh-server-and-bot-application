#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Custom Server, Story Platform & Simulator Master Controller
=============================================================================
Python-based Master Controller and orchestration engine.
Handles:
- Live Duel Simulator (docker compose) container management
- Database statistics & card catalog synchronization
- CDB compilation & Lua effect script scaffolding
- Duelingbook JSON card imports
- Character and player deck exports (.ydk)
- Pytest test execution & Lua syntax validation
- Launchers for Web Dashboard, Discord Bot, and Desktop GUI Manager
=============================================================================
"""

import sys
import os
import subprocess
import sqlite3
import argparse
from typing import List, Optional

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, DECKS_DIR,
    TOOLS_DIR, TESTS_DIR, APP_PY_PATH, BOT_DIR, SCHEMA_PATH,
    SEED_SCRIPT_PATH, PROD_MAIN_DIR, EXPANSIONS_DIR,
    PACKAGES_DIR, SERVER_PACKAGE_DIR, CLIENT_PACKAGE_DIR, DIST_DIR,
    ensure_directories
)

# Terminal color constants
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"


def print_header(title: str):
    print(f"\n{BOLD}{BLUE}=== {title} ==={NC}")


def cmd_status():
    """Display comprehensive status of all platform services and data stores."""
    print(f"{BOLD}=== 🌌 Yu-Gi-Oh! Story & Simulator Platform Status ==={NC}")

    # 1. Live Simulator Container
    print(f"\n{BLUE}>> Live Duel Simulator Container (docker-compose):{NC}")
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", "name=ygo-simulator-server", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, check=False
        )
        if res.stdout.strip():
            print(res.stdout.strip())
        else:
            print("   • Container not running. Run: ./manage.sh start")
    except Exception as e:
        print(f"   • Docker check unavailable: {e}")

    # 2. Database statistics
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
            print(f"   • Error querying database: {e}")
    else:
        print(f"   • Database file not found at {STORY_DB_PATH}. Run: ./manage.sh install")

    # 3. Expansions & Shared Distribution Status
    print(f"\n{BLUE}>> Shared Client Distribution Status (production/shared):{NC}")
    if os.path.exists(CDB_OUTPUT_PATH):
        size_kb = os.path.getsize(CDB_OUTPUT_PATH) / 1024
        print(f"   • Compiled CDB: {os.path.relpath(CDB_OUTPUT_PATH, BASE_DIR)} ({size_kb:.1f} KB)")
    else:
        print(f"   • Compiled CDB not found. Run: ./manage.sh sync")

    if os.path.exists(SCRIPTS_DIR):
        lua_files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")]
        print(f"   • Lua Effect Scripts: {len(lua_files)} files in {os.path.relpath(SCRIPTS_DIR, BASE_DIR)}/")
    else:
        print("   • Lua scripts directory not found.")

    if os.path.exists(DECKS_DIR):
        ydk_files = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")]
        print(f"   • Shared Story Decks: {len(ydk_files)} .ydk files in {os.path.relpath(DECKS_DIR, BASE_DIR)}/")
    print()


def cmd_start():
    """Start the live simulator container via docker compose."""
    print(f"{BLUE}[*] Starting Yu-Gi-Oh! Live Duel Simulator container...{NC}")
    res = subprocess.run(["docker", "compose", "up", "-d"], cwd=BASE_DIR)
    if res.returncode == 0:
        print(f"{GREEN}[+] Duel Simulator active and listening on:{NC}")
        print("    - Game Client TCP: localhost:7911 (or your LAN/VPN IP for EDOPro / YGOPro)")
        print("    - Web Room Manager: http://localhost:7922")
    return res.returncode


def cmd_stop():
    """Stop the live simulator container."""
    print(f"{YELLOW}[*] Stopping Yu-Gi-Oh! Live Duel Simulator container...{NC}")
    res = subprocess.run(["docker", "compose", "down"], cwd=BASE_DIR)
    if res.returncode == 0:
        print(f"{GREEN}[+] Simulator stopped successfully.{NC}")
    return res.returncode


def cmd_restart():
    """Restart the live simulator container."""
    print(f"{BLUE}[*] Restarting Yu-Gi-Oh! Live Duel Simulator container...{NC}")
    res = subprocess.run(["docker", "compose", "restart"], cwd=BASE_DIR)
    if res.returncode == 0:
        print(f"{GREEN}[+] Simulator restarted successfully.{NC}")
    return res.returncode


def cmd_sync():
    """Rebuild the shared simulator CDB and regenerate all Lua effect scripts."""
    print(f"{BLUE}[*] Synchronizing Story Database with Simulator CDB and Lua scripts...{NC}")
    ensure_directories()
    sys.path.insert(0, TOOLS_DIR)

    from cdb_builder import build_cdb
    from lua_generator import generate_all_scripts

    card_count = build_cdb()
    script_count = generate_all_scripts()
    print(f"{GREEN}[+] Sync complete: {card_count} cards compiled to CDB, {script_count} Lua scripts generated.{NC}")


def cmd_import(file_path: str):
    """Import Duelingbook JSON cards."""
    if not file_path:
        print(f"{RED}[-] Error: Please specify the path to a Duelingbook JSON export.{NC}")
        sys.exit(1)
    if not os.path.exists(file_path):
        print(f"{RED}[-] Error: File not found: {file_path}{NC}")
        sys.exit(1)

    print(f"{BLUE}[*] Importing Duelingbook cards from {file_path}...{NC}")
    sys.path.insert(0, TOOLS_DIR)
    from duelingbook_importer import import_from_json_file
    imported_ids = import_from_json_file(file_path, sync_simulator=True)
    print(f"{GREEN}[+] Imported and synchronized {len(imported_ids)} custom cards!{NC}")


def cmd_export_decks():
    """Export all story character decks to .ydk files."""
    print(f"{BLUE}[*] Exporting character story decks to {os.path.relpath(DECKS_DIR, BASE_DIR)}/...{NC}")
    sys.path.insert(0, TOOLS_DIR)
    from export_deck import export_all_decks
    export_all_decks()
    print(f"{GREEN}[+] Deck export completed.{NC}")


def cmd_export_player(user_id: str):
    """Export a specific player's deck to .ydk file."""
    if not user_id:
        print(f"{RED}[-] Error: Please specify a Discord User ID.{NC}")
        sys.exit(1)
    print(f"{BLUE}[*] Exporting player deck for user {user_id}...{NC}")
    sys.path.insert(0, TOOLS_DIR)
    from export_deck import export_player_deck
    res = export_player_deck(user_id)
    if res:
        print(f"{GREEN}[+] Exported successfully to {res}{NC}")
    else:
        print(f"{YELLOW}[!] No cards found for user {user_id}.{NC}")


def cmd_test():
    """Run pytest test suite on development/tests."""
    print(f"{BLUE}[*] Running Unit Test Suite with Pytest...{NC}")
    pytest_bin = os.path.join(BASE_DIR, "venv", "bin", "pytest")
    if not os.path.exists(pytest_bin):
        pytest_bin = "pytest"
    res = subprocess.run([pytest_bin, "-v", TESTS_DIR], cwd=BASE_DIR)
    return res.returncode


def cmd_validate_lua():
    """Validate Lua effect scripts syntax."""
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
            print(f"{RED}[-] Syntax errors found:\n{res.stderr}{NC}")
            return res.returncode
    else:
        print(f"{YELLOW}[!] luac compiler not found on host. Verifying file sizes and non-emptiness...{NC}")
        valid = 0
        for f in lua_files:
            if os.path.getsize(f) > 50:
                valid += 1
        print(f"{GREEN}[+] Verified {valid}/{len(lua_files)} Lua scripts exist and have content.{NC}")
        print("    (To install luac: sudo apt-get install lua5.3)")
        return 0


def cmd_web():
    """Launch FastAPI Web Catalog Dashboard & REST API."""
    print(f"{BLUE}[*] Launching Web Catalog & Lore Dashboard on http://localhost:8000...{NC}")
    uvicorn_bin = os.path.join(BASE_DIR, "venv", "bin", "uvicorn")
    if not os.path.exists(uvicorn_bin):
        uvicorn_bin = "uvicorn"
    os.execv(
        uvicorn_bin,
        [uvicorn_bin, "production.main.web.api_server:app", "--app-dir", BASE_DIR, "--host", "0.0.0.0", "--port", "8000", "--reload"]
    )


def cmd_bot():
    """Launch modular Discord Story & Duel Bot."""
    print(f"{BLUE}[*] Starting Modular Yu-Gi-Oh! Story & Duel Discord Bot...{NC}")
    python_bin = os.path.join(BASE_DIR, "venv", "bin", "python3")
    if not os.path.exists(python_bin):
        python_bin = sys.executable
    bot_script = os.path.join(BOT_DIR, "bot.py")
    os.execv(python_bin, [python_bin, "-u", bot_script])


def cmd_app():
    """Launch Desktop GUI Control Panel."""
    print(f"{BLUE}[*] Launching Yu-Gi-Oh! Platform Manager Desktop Application...{NC}")
    python_bin = os.path.join(BASE_DIR, "venv", "bin", "python3")
    if not os.path.exists(python_bin):
        python_bin = sys.executable
    os.execv(python_bin, [python_bin, APP_PY_PATH])


def cmd_install():
    """Initialize directory structure, database, expansions, and sample decks."""
    print(f"{BOLD}{BLUE}[*] Initializing Yu-Gi-Oh! Platform Environment...{NC}")
    ensure_directories()
    print(f"{GREEN}[+] Directory structure verified.{NC}")

    # Check database
    if not os.path.exists(STORY_DB_PATH):
        print(f"{BLUE}[*] Initializing database from schema and seeding initial story data...{NC}")
        sys.path.insert(0, os.path.join(BASE_DIR, "development", "database"))
        import seed_story_data
        seed_story_data.initialize_database()
        print(f"{GREEN}[+] Database initialized successfully.{NC}")
    else:
        print(f"{GREEN}[+] Story database already present.{NC}")

    # Rebuild CDB and Lua
    cmd_sync()
    cmd_export_decks()
    print(f"\n{BOLD}{GREEN}[🎉] Installation & Setup Complete!{NC}")
    print("You can now start services using:")
    print("  ./manage.sh start      # Starts live duel simulator")
    print("  ./manage.sh web        # Starts web catalog at http://localhost:8000")
    print("  ./manage.sh bot        # Starts Discord bot")
    print("  ./manage.sh tunnel     # Launches Cloudflare HTTPS Tunnel for Web Catalog")
    print("  ./manage.sh package    # Bundles client (.zip) and server (.tar.gz) release packages")
    print("  ./manage.sh app        # Starts Desktop GUI")
    print("  ./manage.sh status     # Checks status")


def cmd_tunnel(extra: Optional[List[str]] = None):
    """Launch or manage Cloudflare Tunnel for secure remote card syncing."""
    tunnel_script = os.path.join(SERVER_PACKAGE_DIR, "setup_cloudflare_tunnel.sh")
    if not os.path.exists(tunnel_script):
        tunnel_script = os.path.join(PROD_MAIN_DIR, "setup_cloudflare_tunnel.sh")
    if not os.path.exists(tunnel_script):
        print(f"{RED}[-] Error: Cloudflare Tunnel script not found at {tunnel_script}{NC}")
        sys.exit(1)
    args = [tunnel_script] + (extra or [])
    os.execv(tunnel_script, args)


def cmd_package():
    """Build standalone installation packages (.zip and .tar.gz) in dist/."""
    import zipfile
    import tarfile

    print(f"{BOLD}{BLUE}=== 📦 Yu-Gi-Oh! Platform Packaging & Distribution Builder ==={NC}\n")
    ensure_directories()

    # 1. First ensure CDB and decks are freshly compiled
    cmd_sync()
    cmd_export_decks()

    os.makedirs(DIST_DIR, exist_ok=True)
    client_zip_path = os.path.join(DIST_DIR, "ygo-client-package.zip")
    server_tar_path = os.path.join(DIST_DIR, "ygo-server-package.tar.gz")

    # 2. Build Client Package (.zip)
    print(f"\n{BLUE}[*] Packaging Player Client Distribution -> {os.path.relpath(client_zip_path, BASE_DIR)}...{NC}")
    with zipfile.ZipFile(client_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add client files from packages/client/
        for root, dirs, files in os.walk(CLIENT_PACKAGE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join("ygo-client-package", os.path.relpath(file_path, CLIENT_PACKAGE_DIR))
                zf.write(file_path, arcname)

        # Add compiled expansions/
        if os.path.exists(EXPANSIONS_DIR):
            for root, dirs, files in os.walk(EXPANSIONS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join("ygo-client-package", "expansions", os.path.relpath(file_path, EXPANSIONS_DIR))
                    zf.write(file_path, arcname)

        # Add decks/
        if os.path.exists(DECKS_DIR):
            for root, dirs, files in os.walk(DECKS_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join("ygo-client-package", "decks", os.path.relpath(file_path, DECKS_DIR))
                    zf.write(file_path, arcname)

    client_size_mb = os.path.getsize(client_zip_path) / (1024 * 1024)
    print(f"{GREEN}[+] Client package built: {client_zip_path} ({client_size_mb:.2f} MB){NC}")

    # 3. Build Server Package (.tar.gz)
    print(f"\n{BLUE}[*] Packaging Host Server Deployment -> {os.path.relpath(server_tar_path, BASE_DIR)}...{NC}")
    with tarfile.open(server_tar_path, "w:gz") as tf:
        tf.add(SERVER_PACKAGE_DIR, arcname="ygo-server-package")

    server_size_kb = os.path.getsize(server_tar_path) / 1024
    print(f"{GREEN}[+] Server package built: {server_tar_path} ({server_size_kb:.1f} KB){NC}")

    print(f"\n{BOLD}{GREEN}🎉 Release packages created successfully in dist/:{NC}")
    print(f"  • {BOLD}Player Client:{NC} {client_zip_path}")
    print(f"    (Extract and run install_client.bat or install_client.sh)")
    print(f"  • {BOLD}Host Server:{NC}   {server_tar_path}")
    print(f"    (Extract and run sudo ./deploy_oracle_cloud.sh on any Ubuntu/Debian server)\n")


def main():
    parser = argparse.ArgumentParser(
        description="Yu-Gi-Oh! Story & Simulator Platform Master Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status                Display container, database, and card expansion status
  start                 Start live simulator container (Port 7911 / 7922)
  stop                  Stop live simulator container
  restart               Restart live simulator container
  sync                  Rebuild simulator custom_cards.cdb and Lua effect scripts
  import <file.json>    Import Duelingbook JSON cards into database and simulator
  export-decks          Export character decks to standard .ydk format
  export-player <uid>   Export a Discord player's active deck to .ydk format
  test                  Run the comprehensive Pytest test suite
  validate-lua          Verify syntax of all generated Lua scripts
  web                   Start local web card catalog & dashboard (Port 8000)
  bot                   Launch modular Discord story & duel bot
  tunnel                Launch Cloudflare HTTPS Tunnel for Web Catalog & Sync
  package               Build standalone installation packages in dist/
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
    elif cmd == "import":
        cmd_import(extra[0] if extra else "")
    elif cmd == "export-decks":
        cmd_export_decks()
    elif cmd == "export-player":
        cmd_export_player(extra[0] if extra else "")
    elif cmd == "test":
        sys.exit(cmd_test())
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
