#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Custom Server, Story Platform & Simulator Application
=============================================================================
A native desktop control panel application that uses `manage.sh` as its base.
Provides point-and-click control over:
- Live Duel Simulator container operations (Start, Stop, Restart, Status)
- Web Catalog Dashboard (Runs server & opens http://localhost:8000 in browser)
- Docker Desktop GUI launcher
- Duelingbook Card Import pipeline (with native file chooser)
- Simulator Expansion synchronization (CDB & Lua Effect Scripts)
- Deck export to .ydk format
- Automated Pytest test suite & Lua syntax validation
- Real-time live console log output with multi-threaded non-blocking execution
=============================================================================
"""

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
    _BaseTk = tk.Tk
except ImportError:
    tk = None  # type: ignore
    ttk = None  # type: ignore
    filedialog = None  # type: ignore
    messagebox = None  # type: ignore
    TKINTER_AVAILABLE = False
    _BaseTk = object  # type: ignore
import subprocess
import threading
import os
import sys
import re
import webbrowser
import sqlite3
import shutil
from typing import Optional, Callable

# Centralized paths and logging
from config.paths import BASE_DIR, STORY_DB_PATH, ICON_PATH
from production.main.logger import get_logger, audit_operation

logger = get_logger("platform_gui", service="GUI")

MANAGE_PY = os.path.join(BASE_DIR, "manage.py")
MANAGE_SH = os.path.join(BASE_DIR, "manage.sh")

# Regex pattern to strip ANSI terminal escape sequences from shell output
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')



def clean_ansi(text: str) -> str:
    """Removes terminal escape codes for clean display in Tkinter."""
    return ANSI_ESCAPE.sub('', text)


class YugiohPlatformApp(_BaseTk):
    """
    Main desktop window application for managing the Yu-Gi-Oh! server platform.
    """

    def __init__(self):
        if not TKINTER_AVAILABLE:
            raise RuntimeError(
                "Tkinter is not installed or available on this system.\n"
                "- On Ubuntu/Debian: sudo apt-get install -y python3-tk\n"
                "- On headless servers/VPS: use the CLI tools (e.g. ./manage.sh setup --cli)"
            )
        super().__init__()

        self.title("Yu-Gi-Oh! Platform Manager")
        self.geometry("960x680")
        self.minsize(840, 560)

        # Dark theme color scheme
        self.bg_color = "#0d1117"
        self.surface_color = "#161b22"
        self.border_color = "#30363d"
        self.text_color = "#c9d1d9"
        self.accent_color = "#58a6ff"
        self.success_color = "#238636"
        self.warning_color = "#d29922"
        self.danger_color = "#da3633"

        self.configure(bg=self.bg_color)

        # Set application icon if present
        if os.path.exists(ICON_PATH):
            try:
                icon_img = tk.PhotoImage(file=ICON_PATH)
                self.iconphoto(False, icon_img)
            except Exception:
                pass

        self.web_process: Optional[subprocess.Popen] = None
        self.bot_process: Optional[subprocess.Popen] = None

        self._setup_styles()
        self._build_ui()
        self.refresh_quick_stats()

    def _setup_styles(self):
        """Configures ttk widget styles matching the dark Yu-Gi-Oh theme."""
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=self.bg_color, foreground=self.text_color)
        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.surface_color, relief="solid", borderwidth=1)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#f0f6fc", background=self.bg_color)
        style.configure("Subheader.TLabel", font=("Segoe UI", 9), foreground="#8b949e", background=self.bg_color)
        style.configure("Badge.TLabel", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background=self.surface_color, padding=4)

        # Button styles
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=6,
            background="#21262d",
            foreground="#f0f6fc"
        )
        style.map("Action.TButton", background=[("active", "#30363d"), ("pressed", "#1f6feb")])

        style.configure(
            "Success.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=6,
            background=self.success_color,
            foreground="#ffffff"
        )
        style.map("Success.TButton", background=[("active", "#2ea043")])

        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=6,
            background=self.danger_color,
            foreground="#ffffff"
        )
        style.map("Danger.TButton", background=[("active", "#f85149")])

    def _build_ui(self):
        """Constructs all panels, buttons, and console widgets."""
        # =====================================================================
        # 1. HEADER & STATUS BAR
        # =====================================================================
        header_frame = ttk.Frame(self, padding=16)
        header_frame.pack(fill=tk.X)

        title_box = ttk.Frame(header_frame)
        title_box.pack(side=tk.LEFT)

        ttk.Label(title_box, text="🌌 Yu-Gi-Oh! Platform Manager", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_box,
            text="Unified Live Duel Simulator, Web Catalog Dashboard & Duelingbook Sync",
            style="Subheader.TLabel"
        ).pack(anchor=tk.W, pady=(2, 0))

        # Status Badges
        self.stats_box = ttk.Frame(header_frame)
        self.wizard_btn = tk.Button(
            self.stats_box,
            text="🪄 Setup Wizard",
            command=self.open_setup_wizard,
            bg="#8b5cf6",
            fg="#ffffff",
            activebackground="#7c3aed",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=3
        )
        self.wizard_btn.pack(side=tk.RIGHT, padx=6)

        self.sim_status_badge = tk.Label(
            self.stats_box,
            text="Simulator: Checking...",
            bg="#21262d",
            fg="#8b949e",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            relief="flat"
        )
        self.sim_status_badge.pack(side=tk.RIGHT, padx=4)

        self.cards_badge = tk.Label(
            self.stats_box,
            text="Cards: ...",
            bg="#21262d",
            fg="#58a6ff",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            relief="flat"
        )
        self.cards_badge.pack(side=tk.RIGHT, padx=4)

        # =====================================================================
        # 2. MAIN BODY (LEFT CONTROLS, RIGHT CONSOLE)
        # =====================================================================
        body_frame = ttk.Frame(self, padding=12)
        body_frame.pack(fill=tk.BOTH, expand=True)

        # Left Column: Action Buttons
        controls_container = tk.Frame(body_frame, bg=self.surface_color, highlightbackground=self.border_color, highlightthickness=1)
        controls_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        controls_inner = ttk.Frame(controls_container, padding=14)
        controls_inner.pack(fill=tk.BOTH, expand=True)

        # Group 1: Live Duel Simulator
        ttk.Label(controls_inner, text="SIMULATOR ENGINE", font=("Segoe UI", 8, "bold"), foreground="#8b949e").pack(anchor=tk.W, pady=(0, 6))

        sim_btn_frame = ttk.Frame(controls_inner)
        sim_btn_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Button(sim_btn_frame, text="▶ Start", style="Success.TButton", command=lambda: self.run_cli(["start"])).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(sim_btn_frame, text="⏹ Stop", style="Danger.TButton", command=lambda: self.run_cli(["stop"])).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

        ttk.Button(controls_inner, text="🔄 Restart Simulator", style="Action.TButton", command=lambda: self.run_cli(["restart"])).pack(fill=tk.X, pady=(0, 14))

        # Group 2: Applications & Dashboards
        ttk.Label(controls_inner, text="APPLICATIONS & WEB", font=("Segoe UI", 8, "bold"), foreground="#8b949e").pack(anchor=tk.W, pady=(0, 6))

        ttk.Button(controls_inner, text="🌐 Open Web Catalog", style="Action.TButton", command=self.open_web_dashboard).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="🤖 Start Discord Bot", style="Action.TButton", command=self.start_discord_bot).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="☁️ Cloudflare HTTPS Tunnel", style="Action.TButton", command=lambda: self.run_cli(["tunnel", "--quick"])).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="🐳 Open Docker Desktop", style="Action.TButton", command=self.open_docker_desktop).pack(fill=tk.X, pady=(0, 14))

        # Group 3: Card Pipeline & Sync
        ttk.Label(controls_inner, text="EXPANSIONS & CARDS", font=("Segoe UI", 8, "bold"), foreground="#8b949e").pack(anchor=tk.W, pady=(0, 6))

        ttk.Button(controls_inner, text="🔄 Sync CDB & Lua", style="Action.TButton", command=lambda: self.run_cli(["sync"])).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="📥 Import Duelingbook JSON...", style="Action.TButton", command=self.import_json_dialog).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="🎴 Export .YDK Decks", style="Action.TButton", command=lambda: self.run_cli(["export-decks"])).pack(fill=tk.X, pady=(0, 14))

        # Group 4: Diagnostics & Testing
        ttk.Label(controls_inner, text="QUALITY & DIAGNOSTICS", font=("Segoe UI", 8, "bold"), foreground="#8b949e").pack(anchor=tk.W, pady=(0, 6))

        ttk.Button(controls_inner, text="🩺 Run Diagnostics", style="Action.TButton", command=lambda: self.run_cli(["diagnose"])).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="🧪 Run Unit Tests", style="Action.TButton", command=lambda: self.run_cli(["test"])).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="🔍 Validate Lua Scripts", style="Action.TButton", command=lambda: self.run_cli(["validate-lua"])).pack(fill=tk.X, pady=(0, 6))
        ttk.Button(controls_inner, text="📊 Refresh Status", style="Action.TButton", command=self.refresh_all_status).pack(fill=tk.X, pady=(0, 6))


        # Right Column: Real-Time Console Log
        console_container = tk.Frame(body_frame, bg=self.surface_color, highlightbackground=self.border_color, highlightthickness=1)
        console_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        console_header = tk.Frame(console_container, bg="#161b22", padx=10, pady=8)
        console_header.pack(fill=tk.X)

        tk.Label(console_header, text="CONSOLE OUTPUT", bg="#161b22", fg="#8b949e", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        clear_btn = tk.Button(
            console_header,
            text="Clear",
            bg="#21262d",
            fg="#c9d1d9",
            activebackground="#30363d",
            activeforeground="#ffffff",
            relief="flat",
            padx=8,
            pady=2,
            font=("Segoe UI", 8),
            command=self.clear_console
        )
        clear_btn.pack(side=tk.RIGHT)

        # Scrolled Text for Console
        self.console_text = tk.Text(
            console_container,
            bg="#090d13",
            fg="#c9d1d9",
            insertbackground="#ffffff",
            font=("Cascadia Code", 9),
            padx=10,
            pady=10,
            relief="flat",
            wrap=tk.WORD
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)

        self.log_message("=== Yu-Gi-Oh! Platform Manager Initialized ===")
        self.log_message("Base Engine: " + MANAGE_SH)
        self.log_message("Ready for operations. Click any action on the left to begin.")

    def log_message(self, message: str):
        """Appends a line to the console log widget with automatic scrolling."""
        self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)

    def clear_console(self):
        """Clears the console text widget."""
        self.console_text.delete("1.0", tk.END)

    def refresh_quick_stats(self):
        """Asynchronously updates the header status badges."""
        def worker():
            # Check container
            try:
                res = subprocess.run(
                    ["docker", "ps", "--filter", "name=ygo-simulator-server", "--format", "{{.Status}}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                is_running = "Up" in res.stdout
            except Exception:
                is_running = False

            # Check card count
            card_count = 0
            try:
                conn = sqlite3.connect(STORY_DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM custom_cards")
                card_count = cur.fetchone()[0]
                conn.close()
            except Exception:
                pass

            # Update UI on main thread
            self.after(0, lambda: self._apply_stats(is_running, card_count))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_stats(self, is_running: bool, card_count: int):
        """Applies status badge colors and labels."""
        if is_running:
            self.sim_status_badge.config(
                text="● Simulator: Active (Port 7911/7922)",
                bg="#238636",
                fg="#ffffff"
            )
        else:
            self.sim_status_badge.config(
                text="○ Simulator: Stopped",
                bg="#da3633",
                fg="#ffffff"
            )

        self.cards_badge.config(text=f"🃏 {card_count} Cards in Pool")

    def run_cli(self, args: list, on_complete: Optional[Callable] = None):
        """
        Executes a `manage.py` command in a non-blocking background thread
        and streams stdout/stderr live to the application console.
        Cross-platform compatible on Windows, macOS, and Linux.
        """
        cmd = [sys.executable, MANAGE_PY] + args
        logger.info(f"GUI initiating CLI operation: python manage.py {' '.join(args)}")

        def worker():
            self.after(0, lambda: self.log_message(f"\n$ python manage.py {' '.join(args)}"))
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=BASE_DIR
                )

                for line in iter(proc.stdout.readline, ''):
                    cleaned = clean_ansi(line).rstrip()
                    if cleaned:
                        self.after(0, lambda l=cleaned: self.log_message(l))

                proc.stdout.close()
                proc.wait()

                logger.info(f"CLI command 'python manage.py {' '.join(args)}' exited with code {proc.returncode}")
                self.after(0, lambda: self.log_message(f"[Process finished with exit code {proc.returncode}]"))
                self.after(0, self.refresh_quick_stats)

                if on_complete:
                    self.after(0, on_complete)

            except Exception as e:
                logger.error(f"GUI failed to execute command {' '.join(args)}: {e}", exc_info=True)
                self.after(0, lambda: self.log_message(f"[-] Execution error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def open_web_dashboard(self):
        """Starts the FastAPI Web Catalog server if not active, then opens the browser."""
        self.log_message("[*] Checking Web Catalog Dashboard at http://localhost:8000...")

        def check_and_launch():
            import urllib.request
            is_up = False
            try:
                with urllib.request.urlopen("http://localhost:8000", timeout=1) as resp:
                    if resp.status == 200:
                        is_up = True
            except Exception:
                is_up = False

            if not is_up:
                self.after(0, lambda: self.log_message("[*] Starting web server in background via uvicorn..."))
                subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "production.main.web.api_server:app", "--host", "0.0.0.0", "--port", "8000"],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                import time
                time.sleep(1.2)

            self.after(0, lambda: self.log_message("[+] Opening http://localhost:8000 in your default browser..."))
            webbrowser.open("http://localhost:8000")

        threading.Thread(target=check_and_launch, daemon=True).start()

    def start_discord_bot(self):
        """Starts the Discord Story Bot in a background thread."""
        self.run_cli(["bot"])

    def open_docker_desktop(self):
        """Launches the Docker Desktop GUI across Windows, macOS, or Linux."""
        self.log_message("[*] Launching Docker Desktop application...")
        desktop_bin = shutil.which("docker-desktop") or "/opt/docker-desktop/bin/docker-desktop"
        if os.path.exists(desktop_bin) or shutil.which("docker-desktop"):
            subprocess.Popen([desktop_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log_message("[+] Docker Desktop GUI launched.")
            logger.info("Launched Docker Desktop GUI.")
        else:
            self.log_message("[-] Docker Desktop binary not found in system PATH.")
            logger.warning("Docker Desktop binary not found.")

    def import_json_dialog(self):
        """Opens a file dialog to pick a Duelingbook JSON export and imports it."""
        file_path = filedialog.askopenfilename(
            title="Select Duelingbook Cards JSON Export",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=BASE_DIR
        )
        if file_path:
            self.run_cli(["import", file_path])

    def open_setup_wizard(self):
        """Opens the step-by-step Server Setup Wizard."""
        try:
            from production.main.setup_wizard import build_gui_wizard
            WizardClass = build_gui_wizard()
            WizardClass(self)
            logger.info("Opened Server Setup Wizard from GUI.")
        except Exception as e:
            logger.error(f"Error opening Setup Wizard: {e}", exc_info=True)
            self.log_message(f"[-] Error opening Setup Wizard: {e}")

    def refresh_all_status(self):
        """Refreshes status in console and header."""
        self.refresh_quick_stats()
        self.run_cli(["status"])


def main():
    if not TKINTER_AVAILABLE:
        print("[!] Error: Tkinter desktop GUI library is not installed on this system.")
        print("    - On Linux/Ubuntu: sudo apt-get install -y python3-tk")
        print("    - For headless environments, manage the server via CLI:")
        print("      ./manage.sh status | ./manage.sh setup --cli | ./manage.sh diagnose")
        sys.exit(1)
    app = YugiohPlatformApp()
    app.mainloop()


if __name__ == "__main__":
    main()
