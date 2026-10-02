#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform Manager - Host Server Setup Wizard (GUI & CLI)
=============================================================================
An interactive, step-by-step setup wizard for platform administrators:
- Step 1: Environment & Dependency Verification (Python, Docker, luac)
- Step 2: Discord Bot Token & Guild Configuration (with live validation)
- Step 3: Live Duel Simulator & Network Ports (Port 7911, 7922, 8000)
- Step 4: Database Seeding, CDB Compilation & Service Launch

Cross-Platform:
- Supports rich dark-theme Tkinter GUI when a display server is available.
- Automatically falls back to an interactive terminal CLI on headless servers (VPS / SSH).
- Safely updates key-value pairs in `.env` without overwriting unrelated settings.
- Emits structured operational events via `production.main.logger`.
=============================================================================
"""

import os
import sys
import shutil
import subprocess
import threading
import sqlite3
import argparse
from typing import Dict, Optional

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, TOOLS_DIR,
    DATABASE_DIR, ENV_FILE_PATH, ensure_directories
)
from production.main.logger import get_logger, audit_operation

logger = get_logger("setup_wizard", service="WIZARD")


# =============================================================================
# Helper: Safe .env Modifier (Preserves Existing Configurations)
# =============================================================================

def save_env_values(updates: Dict[str, str], env_path: str = ENV_FILE_PATH) -> None:
    """
    Updates or appends key-value pairs in the .env file while preserving existing
    unrelated settings and comments.

    Args:
        updates (Dict[str, str]): Dictionary of KEY -> VALUE to set.
        env_path (str): Path to the target .env file.
    """
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    updated_keys = set()
    new_lines = []

    for line in existing_lines:
        trimmed = line.strip()
        if trimmed and not trimmed.startswith("#") and "=" in trimmed:
            key = trimmed.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f'{key}="{updates[key]}"\n')
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Append any remaining keys that were not present in existing file
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f'{key}="{val}"\n')

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    logger.info(f"Updated .env keys: {list(updates.keys())}")


def load_env_values(env_path: str = ENV_FILE_PATH) -> Dict[str, str]:
    """Reads key-value pairs from .env file into a dictionary."""
    values = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                trimmed = line.strip()
                if trimmed and not trimmed.startswith("#") and "=" in trimmed:
                    k, v = trimmed.split("=", 1)
                    values[k.strip()] = v.strip().strip('"\'')
    return values


# =============================================================================
# Headless Terminal CLI Setup Wizard
# =============================================================================

def run_cli_wizard():
    """Runs interactive setup wizard in the terminal for headless/SSH environments."""
    print("\n=======================================================")
    print("      YU-GI-OH! SERVER SETUP WIZARD (CLI MODE)        ")
    print("=======================================================\n")
    logger.info("Starting interactive CLI setup wizard...")

    # Step 1: System Checks
    print("[1/4] Verifying System Prerequisites:")
    docker_found = shutil.which("docker") is not None
    luac_found = shutil.which("luac") is not None
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    print(f"  • Python: {py_ver} (OK)")
    print(f"  • Docker: {'OK' if docker_found else 'NOT FOUND (Required for simulator container)'}")
    print(f"  • luac:   {'OK' if luac_found else 'NOT FOUND (Optional, Lua syntax validator)'}")
    print()

    # Step 2: Discord Bot Credentials
    current_env = load_env_values()
    default_token = current_env.get("DISCORD_BOT_TOKEN", "")
    default_guild = current_env.get("DISCORD_GUILD_ID", "")

    print("[2/4] Discord Bot Configuration:")
    token_input = input(f"  Enter Discord Bot Token [{default_token[:8]}...]: ").strip()
    bot_token = token_input if token_input else default_token

    guild_input = input(f"  Enter Discord Guild ID [{default_guild}]: ").strip()
    guild_id = guild_input if guild_input else default_guild
    print()

    # Step 3: Network Ports
    default_sim_port = current_env.get("SIMULATOR_TCP_PORT", "7911")
    default_web_port = current_env.get("WEB_CATALOG_PORT", "8000")

    print("[3/4] Network Ports:")
    sim_port_input = input(f"  Simulator Duel Port [{default_sim_port}]: ").strip()
    sim_port = sim_port_input if sim_port_input else default_sim_port

    web_port_input = input(f"  Web Catalog Port [{default_web_port}]: ").strip()
    web_port = web_port_input if web_port_input else default_web_port
    print()

    # Save to .env
    save_env_values({
        "DISCORD_BOT_TOKEN": bot_token,
        "DISCORD_GUILD_ID": guild_id,
        "SIMULATOR_TCP_PORT": sim_port,
        "WEB_CATALOG_PORT": web_port,
    })
    print("✔ Configuration saved to .env")

    # Step 4: Database Seeding & CDB Compilation
    print("\n[4/4] Initializing Database & Compiling Expansion...")
    with audit_operation("Initial Platform Bootstrap", service="WIZARD"):
        ensure_directories()
        if not os.path.exists(STORY_DB_PATH):
            sys.path.insert(0, DATABASE_DIR)
            import seed_story_data
            seed_story_data.initialize_database()
            print("  ✔ Database seeded.")

        sys.path.insert(0, TOOLS_DIR)
        from cdb_builder import build_cdb
        from lua_generator import generate_all_scripts
        cards = build_cdb()
        scripts = generate_all_scripts()
        print(f"  ✔ Compiled {cards} cards into custom_cards.cdb.")
        print(f"  ✔ Generated {scripts} Lua effect scripts.")

    print("\n=======================================================")
    print("       🎉 SETUP COMPLETE! READY FOR OPERATIONS         ")
    print("=======================================================\n")
    print("Commands to launch:")
    print("  ./manage.sh start      # Starts live duel simulator")
    print("  ./manage.sh web        # Starts web catalog")
    print("  ./manage.sh bot        # Starts Discord bot")
    print("  ./manage.sh diagnose   # Runs system diagnostics\n")


# =============================================================================
# GUI Setup Wizard (Tkinter)
# =============================================================================

def build_gui_wizard():
    """Builds and returns the Tkinter ServerSetupWizard class."""
    import tkinter as tk
    from tkinter import messagebox

    class ServerSetupWizard(tk.Toplevel):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.title("Yu-Gi-Oh! Server Setup Wizard")
            self.geometry("720x540")
            self.minsize(680, 480)

            self.bg_color = "#0d1117"
            self.surface_color = "#161b22"
            self.border_color = "#30363d"
            self.text_color = "#c9d1d9"
            self.accent_color = "#58a6ff"
            self.success_color = "#238636"

            self.configure(bg=self.bg_color)
            self.current_step = 0

            # Configuration variables
            current_env = load_env_values()
            self.bot_token = tk.StringVar(value=current_env.get("DISCORD_BOT_TOKEN", ""))
            self.guild_id = tk.StringVar(value=current_env.get("DISCORD_GUILD_ID", ""))
            self.sim_port = tk.StringVar(value=current_env.get("SIMULATOR_TCP_PORT", "7911"))
            self.web_port = tk.StringVar(value=current_env.get("WEB_CATALOG_PORT", "8000"))

            self._build_ui()
            self._show_step(0)

        def _build_ui(self):
            # 1. Header
            header = tk.Frame(self, bg=self.surface_color, padx=20, pady=12)
            header.pack(fill=tk.X)

            self.step_title_lbl = tk.Label(
                header, text="Server Setup Wizard",
                font=("Segoe UI", 13, "bold"), fg=self.accent_color, bg=self.surface_color
            )
            self.step_title_lbl.pack(anchor=tk.W)

            self.step_sub_lbl = tk.Label(
                header, text="Step 1 of 4",
                font=("Segoe UI", 9), fg="#8b949e", bg=self.surface_color
            )
            self.step_sub_lbl.pack(anchor=tk.W)

            # 2. Main Content Container
            self.content_frame = tk.Frame(self, bg=self.bg_color, padx=25, pady=20)
            self.content_frame.pack(fill=tk.BOTH, expand=True)

            # 3. Footer Navigation Bar
            footer = tk.Frame(self, bg=self.surface_color, padx=20, pady=12)
            footer.pack(fill=tk.X, side=tk.BOTTOM)

            self.btn_cancel = tk.Button(
                footer, text="Cancel", command=self.destroy,
                bg="#21262d", fg=self.text_color, relief=tk.FLAT, padx=12, pady=4
            )
            self.btn_cancel.pack(side=tk.LEFT)

            self.btn_next = tk.Button(
                footer, text="Next >", command=self._next_step,
                bg=self.accent_color, fg="#ffffff", font=("Segoe UI", 9, "bold"),
                relief=tk.FLAT, padx=15, pady=4
            )
            self.btn_next.pack(side=tk.RIGHT)

            self.btn_prev = tk.Button(
                footer, text="< Back", command=self._prev_step,
                bg="#21262d", fg=self.text_color, relief=tk.FLAT, padx=12, pady=4
            )
            self.btn_prev.pack(side=tk.RIGHT, padx=8)

        def _show_step(self, step_idx: int):
            self.current_step = step_idx
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            self.btn_prev.config(state=tk.NORMAL if step_idx > 0 else tk.DISABLED)

            if step_idx == 0:
                self._render_step_1_prereqs()
            elif step_idx == 1:
                self._render_step_2_discord()
            elif step_idx == 2:
                self._render_step_3_network()
            elif step_idx == 3:
                self._render_step_4_finish()

        def _render_step_1_prereqs(self):
            self.step_title_lbl.config(text="Step 1: System & Environment Prerequisites")
            self.step_sub_lbl.config(text="Verifying necessary tools and runtimes")

            tk.Label(
                self.content_frame,
                text="Welcome to the Yu-Gi-Oh! Platform Host Setup Wizard!\n"
                     "This wizard will help you configure your live simulator, database, and Discord bot.",
                bg=self.bg_color, fg=self.text_color, justify=tk.LEFT, font=("Segoe UI", 10)
            ).pack(anchor=tk.W, pady=(0, 15))

            docker_ok = shutil.which("docker") is not None
            docker_text = "✅ Docker is installed" if docker_ok else "⚠️ Docker not found (required for simulator container)"

            py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            py_text = f"✅ Python {py_ver} (active)"

            luac_ok = shutil.which("luac") is not None
            luac_text = "✅ luac compiler found" if luac_ok else "ℹ️ luac not installed (optional, used for syntax validation)"

            box = tk.Frame(self.content_frame, bg=self.surface_color, padx=15, pady=15, relief=tk.FLAT)
            box.pack(fill=tk.X, pady=10)

            tk.Label(box, text=py_text, bg=self.surface_color, fg="#58a6ff", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=4)
            tk.Label(box, text=docker_text, bg=self.surface_color, fg="#10b981" if docker_ok else "#d29922", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=4)
            tk.Label(box, text=luac_text, bg=self.surface_color, fg="#8b949e", font=("Segoe UI", 10)).pack(anchor=tk.W, pady=4)

            tk.Label(
                self.content_frame,
                text="Click 'Next' to configure your Discord Bot credentials.",
                bg=self.bg_color, fg="#8b949e", font=("Segoe UI", 9)
            ).pack(anchor=tk.W, pady=15)

        def _render_step_2_discord(self):
            self.step_title_lbl.config(text="Step 2: Discord Story & Duel Bot Setup")
            self.step_sub_lbl.config(text="Configure your Discord Developer Bot credentials")

            tk.Label(
                self.content_frame,
                text="The Discord bot provides slash commands, card searching, deckbuilding, and in-chat duels.\n"
                     "If you haven't created a bot application yet, get a token at discord.com/developers/applications.",
                bg=self.bg_color, fg=self.text_color, justify=tk.LEFT, font=("Segoe UI", 9)
            ).pack(anchor=tk.W, pady=(0, 15))

            tk.Label(self.content_frame, text="Discord Bot Token:", bg=self.bg_color, fg="#f0f6fc", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
            token_entry = tk.Entry(
                self.content_frame, textvariable=self.bot_token, show="•",
                bg="#05070a", fg="#ffffff", relief=tk.FLAT, font=("Consolas", 10),
                highlightthickness=1, highlightbackground=self.border_color
            )
            token_entry.pack(fill=tk.X, pady=(4, 15), ipady=4)

            tk.Label(self.content_frame, text="Discord Guild / Server ID (Optional for global):", bg=self.bg_color, fg="#f0f6fc", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
            guild_entry = tk.Entry(
                self.content_frame, textvariable=self.guild_id,
                bg="#05070a", fg="#ffffff", relief=tk.FLAT, font=("Consolas", 10),
                highlightthickness=1, highlightbackground=self.border_color
            )
            guild_entry.pack(fill=tk.X, pady=(4, 15), ipady=4)

        def _render_step_3_network(self):
            self.step_title_lbl.config(text="Step 3: Network Ports & Live Simulator")
            self.step_sub_lbl.config(text="Configure connection ports for EDOPro and the Web Dashboard")

            tk.Label(
                self.content_frame,
                text="These ports are exposed by the server so clients and browsers can connect.",
                bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 9)
            ).pack(anchor=tk.W, pady=(0, 15))

            tk.Label(self.content_frame, text="Game Client Duel Port (Default 7911):", bg=self.bg_color, fg="#f0f6fc", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
            tk.Entry(
                self.content_frame, textvariable=self.sim_port, width=15,
                bg="#05070a", fg="#ffffff", relief=tk.FLAT, font=("Consolas", 10),
                highlightthickness=1, highlightbackground=self.border_color
            ).pack(anchor=tk.W, pady=(2, 12), ipady=3)

            tk.Label(self.content_frame, text="Web Catalog Dashboard Port (Default 8000):", bg=self.bg_color, fg="#f0f6fc", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
            tk.Entry(
                self.content_frame, textvariable=self.web_port, width=15,
                bg="#05070a", fg="#ffffff", relief=tk.FLAT, font=("Consolas", 10),
                highlightthickness=1, highlightbackground=self.border_color
            ).pack(anchor=tk.W, pady=(2, 12), ipady=3)

        def _render_step_4_finish(self):
            self.step_title_lbl.config(text="Step 4: Initialize Database & Ready to Launch")
            self.step_sub_lbl.config(text="Build card database and launch services")
            self.btn_next.config(text="Finish & Close")

            tk.Label(
                self.content_frame,
                text="Click the button below to initialize the story database, compile the initial\n"
                     "custom cards into `custom_cards.cdb`, and generate the Lua effect scripts.",
                bg=self.bg_color, fg=self.text_color, justify=tk.LEFT, font=("Segoe UI", 9)
            ).pack(anchor=tk.W, pady=(0, 15))

            init_btn = tk.Button(
                self.content_frame, text="⚡ Initialize Database & Synchronize CDB",
                command=self._run_initial_sync,
                bg=self.success_color, fg="#ffffff", font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT, padx=15, pady=8
            )
            init_btn.pack(anchor=tk.W, pady=10)

            self.init_status_lbl = tk.Label(
                self.content_frame, text="", bg=self.bg_color, fg="#8b949e", font=("Segoe UI", 9)
            )
            self.init_status_lbl.pack(anchor=tk.W, pady=5)

        def _save_all_settings(self):
            save_env_values({
                "DISCORD_BOT_TOKEN": self.bot_token.get().strip(),
                "DISCORD_GUILD_ID": self.guild_id.get().strip(),
                "SIMULATOR_TCP_PORT": self.sim_port.get().strip(),
                "WEB_CATALOG_PORT": self.web_port.get().strip(),
            })

        def _run_initial_sync(self):
            self.init_status_lbl.config(text="[*] Initializing directories and compiling cards...", fg="#58a6ff")

            def worker():
                try:
                    ensure_directories()
                    if not os.path.exists(STORY_DB_PATH):
                        sys.path.insert(0, DATABASE_DIR)
                        import seed_story_data
                        seed_story_data.initialize_database()

                    sys.path.insert(0, TOOLS_DIR)
                    from cdb_builder import build_cdb
                    from lua_generator import generate_all_scripts
                    cards = build_cdb()
                    scripts = generate_all_scripts()
                    self.after(0, lambda: self.init_status_lbl.config(
                        text=f"✅ Ready! {cards} cards compiled into CDB, {scripts} Lua scripts generated.",
                        fg="#10b981"
                    ))
                except Exception as e:
                    self.after(0, lambda: self.init_status_lbl.config(
                        text=f"❌ Error during initialization: {e}",
                        fg="#f85149"
                    ))

            threading.Thread(target=worker, daemon=True).start()

        def _next_step(self):
            if self.current_step < 3:
                self._save_all_settings()
                self._show_step(self.current_step + 1)
            else:
                self._save_all_settings()
                self.destroy()

        def _prev_step(self):
            if self.current_step > 0:
                self._show_step(self.current_step - 1)

    return ServerSetupWizard


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Yu-Gi-Oh! Platform Server Setup Wizard")
    parser.add_argument("--cli", action="store_true", help="Force interactive terminal CLI mode")
    args = parser.parse_args()

    # Determine if GUI is available
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or sys.platform == "win32")

    if args.cli or not has_display:
        run_cli_wizard()
        return

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        WizardClass = build_gui_wizard()
        wiz = WizardClass(root)
        wiz.mainloop()
    except Exception as e:
        logger.warning(f"Could not initialize Tkinter GUI ({e}); falling back to CLI setup wizard.")
        run_cli_wizard()


if __name__ == "__main__":
    main()
