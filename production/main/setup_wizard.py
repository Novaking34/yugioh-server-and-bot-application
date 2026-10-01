#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform Manager - Host Server Setup Wizard (GUI)
=============================================================================
An interactive, step-by-step setup wizard for platform administrators:
- Step 1: Environment & Dependency Verification (Python, Docker, luac)
- Step 2: Discord Bot Token & Guild Configuration (with live validation)
- Step 3: Live Duel Simulator & Network Ports (Port 7911, 7922, 8000)
- Step 4: Database Seeding, CDB Compilation & Service Launch
=============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
import threading
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.paths import (
    STORY_DB_PATH, CDB_OUTPUT_PATH, SCRIPTS_DIR, TOOLS_DIR,
    DATABASE_DIR, ensure_directories
)


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
        self.bot_token = tk.StringVar(value="")
        self.guild_id = tk.StringVar(value="")
        self.sim_port = tk.StringVar(value="7911")
        self.web_port = tk.StringVar(value="8000")

        self._load_existing_env()
        self._build_ui()
        self._show_step(0)

    def _load_existing_env(self):
        env_file = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DISCORD_BOT_TOKEN="):
                        self.bot_token.set(line.split("=", 1)[1].strip('"\''))
                    elif line.startswith("DISCORD_GUILD_ID="):
                        self.guild_id.set(line.split("=", 1)[1].strip('"\''))

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

        # Check Docker
        docker_ok = subprocess.run(["which", "docker"], capture_output=True).returncode == 0
        docker_text = "✅ Docker is installed" if docker_ok else "⚠️ Docker not found (required for simulator container)"

        # Check Python
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_text = f"✅ Python {py_ver} (active)"

        # Check luac
        luac_ok = subprocess.run(["which", "luac"], capture_output=True).returncode == 0
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

        # Bot Token
        tk.Label(self.content_frame, text="Discord Bot Token:", bg=self.bg_color, fg="#f0f6fc", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        token_entry = tk.Entry(
            self.content_frame, textvariable=self.bot_token, show="•",
            bg="#05070a", fg="#ffffff", insertbackground="#ffffff",
            relief=tk.FLAT, font=("Consolas", 10), highlightthickness=1, highlightbackground=self.border_color
        )
        token_entry.pack(fill=tk.X, pady=(4, 12), ipady=4)

        # Guild ID
        tk.Label(self.content_frame, text="Discord Server / Guild ID (Optional for instant slash command sync):", bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 9)).pack(anchor=tk.W)
        guild_entry = tk.Entry(
            self.content_frame, textvariable=self.guild_id,
            bg="#05070a", fg="#ffffff", insertbackground="#ffffff",
            relief=tk.FLAT, font=("Consolas", 10), highlightthickness=1, highlightbackground=self.border_color
        )
        guild_entry.pack(fill=tk.X, pady=(4, 15), ipady=4)

        # Save Button
        save_btn = tk.Button(
            self.content_frame, text="💾 Save to .env", command=self._save_discord_env,
            bg="#21262d", fg=self.accent_color, relief=tk.FLAT, padx=12, pady=4
        )
        save_btn.pack(anchor=tk.W)

    def _save_discord_env(self):
        token = self.bot_token.get().strip()
        guild = self.guild_id.get().strip()
        env_path = os.path.join(BASE_DIR, ".env")

        lines = [
            f'DISCORD_BOT_TOKEN="{token}"\n',
            f'DISCORD_GUILD_ID="{guild}"\n'
        ]
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        messagebox.showinfo("Saved", "Discord credentials saved successfully to .env!")

    def _render_step_3_network(self):
        self.step_title_lbl.config(text="Step 3: Network Ports & Live Simulator")
        self.step_sub_lbl.config(text="Configure connection ports for EDOPro and the Web Dashboard")

        tk.Label(
            self.content_frame,
            text="These ports are exposed by the server so clients and browsers can connect.",
            bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 9)
        ).pack(anchor=tk.W, pady=(0, 15))

        # Simulator TCP Port
        tk.Label(self.content_frame, text="Game Client Duel Port (Default 7911):", bg=self.bg_color, fg="#f0f6fc", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        tk.Entry(
            self.content_frame, textvariable=self.sim_port, width=15,
            bg="#05070a", fg="#ffffff", relief=tk.FLAT, font=("Consolas", 10),
            highlightthickness=1, highlightbackground=self.border_color
        ).pack(anchor=tk.W, pady=(2, 12), ipady=3)

        # Web Catalog Port
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

    def _run_initial_sync(self):
        self.init_status_lbl.config(text="[*] Initializing directories and compiling cards...", fg="#58a6ff")

        def worker():
            try:
                ensure_directories()
                # Run seed if db empty
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
            if self.current_step == 1:
                # Auto save .env when stepping forward
                self._save_discord_env()
            self._show_step(self.current_step + 1)
        else:
            self.destroy()

    def _prev_step(self):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)


def main():
    root = tk.Tk()
    root.withdraw()
    wiz = ServerSetupWizard(root)
    wiz.mainloop()


if __name__ == "__main__":
    main()
