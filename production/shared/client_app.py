#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Player Client Manager (GUI)
=============================================================================
A native desktop application for players to:
- Detect their local EDOPro / Project Ignis or YGOPro installation
- Install/Update custom card expansions (CDB & Lua scripts) with 1 click
- Install pre-made character & story decks (.ydk)
- Copy server connection details (IP: 7911) or launch game client directly
- Browse custom cards and lore in the web catalog
Cross-platform compatible on Windows, macOS, and Linux.
=============================================================================
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import shutil
import threading
import webbrowser
import subprocess
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPANSIONS_DIR = os.path.join(BASE_DIR, "expansions")
CDB_FILE = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR = os.path.join(EXPANSIONS_DIR, "scripts")
DECKS_DIR = os.path.join(BASE_DIR, "decks")
GUIDE_FILE = os.path.join(BASE_DIR, "CLIENT_GUIDE.md")

# Default server host configuration (can be changed in UI)
DEFAULT_SERVER_HOST = "localhost"
DEFAULT_SERVER_PORT = "7911"
DEFAULT_WEB_PORT = "8000"


class PlayerClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yu-Gi-Oh! Expansion Manager & Duel Connector")
        self.geometry("780x560")
        self.minsize(700, 480)

        # Dark theme colors
        self.bg_color = "#0d1117"
        self.surface_color = "#161b22"
        self.border_color = "#30363d"
        self.text_color = "#c9d1d9"
        self.accent_color = "#58a6ff"
        self.success_color = "#238636"
        self.warn_color = "#d29922"

        self.configure(bg=self.bg_color)
        self.client_dir = tk.StringVar(value="")
        self.server_ip = tk.StringVar(value=DEFAULT_SERVER_HOST)
        self.server_port = tk.StringVar(value=DEFAULT_SERVER_PORT)

        self._setup_styles()
        self._build_ui()
        self._detect_initial_path()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=self.bg_color, foreground=self.text_color)
        style.configure("Surface.TFrame", background=self.surface_color)
        style.configure("TLabel", background=self.surface_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.accent_color)
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#8b949e")
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=self.accent_color, foreground="#ffffff")
        style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), background=self.success_color, foreground="#ffffff")

    def _build_ui(self):
        # 1. Header Frame
        header = ttk.Frame(self, style="Surface.TFrame", padding=15)
        header.pack(fill=tk.X, padx=15, pady=(15, 10))

        title_lbl = ttk.Label(header, text="🌌 Yu-Gi-Oh! Custom Card Expansion Client", style="Header.TLabel")
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(header, text="Sync custom card expansions & connect to live duels seamlessly.", style="Sub.TLabel")
        sub_lbl.pack(anchor=tk.W, pady=(2, 0))

        # 2. Game Client Detection Frame
        client_frame = ttk.Frame(self, style="Surface.TFrame", padding=12)
        client_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(client_frame, text="🎮 EDOPro / Game Client Directory:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        
        path_box = ttk.Frame(client_frame, style="Surface.TFrame")
        path_box.pack(fill=tk.X, pady=(5, 5))

        path_entry = tk.Entry(
            path_box, textvariable=self.client_dir,
            bg="#0d1117", fg="#ffffff", insertbackground="#ffffff",
            relief=tk.FLAT, font=("Consolas", 10), highlightthickness=1, highlightbackground=self.border_color
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)

        browse_btn = tk.Button(
            path_box, text="Browse...", command=self._browse_directory,
            bg="#21262d", fg=self.text_color, activebackground=self.accent_color,
            relief=tk.FLAT, font=("Segoe UI", 9, "bold"), padx=10
        )
        browse_btn.pack(side=tk.RIGHT)

        # 3. Server Connection Settings Frame
        net_frame = ttk.Frame(self, style="Surface.TFrame", padding=12)
        net_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(net_frame, text="🌐 Duel Server Connection Details:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)

        net_sub = ttk.Frame(net_frame, style="Surface.TFrame")
        net_sub.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(net_sub, text="Host / IP:").pack(side=tk.LEFT, padx=(0, 5))
        host_entry = tk.Entry(
            net_sub, textvariable=self.server_ip, width=20,
            bg="#0d1117", fg="#ffffff", insertbackground="#ffffff",
            relief=tk.FLAT, font=("Consolas", 10), highlightthickness=1, highlightbackground=self.border_color
        )
        host_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=2)

        ttk.Label(net_sub, text="Port:").pack(side=tk.LEFT, padx=(0, 5))
        port_entry = tk.Entry(
            net_sub, textvariable=self.server_port, width=8,
            bg="#0d1117", fg="#ffffff", insertbackground="#ffffff",
            relief=tk.FLAT, font=("Consolas", 10), highlightthickness=1, highlightbackground=self.border_color
        )
        port_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=2)

        copy_btn = tk.Button(
            net_sub, text="📋 Copy Connection Info", command=self._copy_connection_info,
            bg="#21262d", fg=self.text_color, activebackground=self.accent_color,
            relief=tk.FLAT, font=("Segoe UI", 9), padx=8
        )
        copy_btn.pack(side=tk.LEFT)

        # 4. Action Buttons Bar
        btn_frame = ttk.Frame(self, style="Surface.TFrame", padding=12)
        btn_frame.pack(fill=tk.X, padx=15, pady=5)

        sync_btn = tk.Button(
            btn_frame, text="⚡ 1-Click Install to Game", command=self._sync_expansions_thread,
            bg=self.success_color, fg="#ffffff", activebackground="#2ea043",
            relief=tk.FLAT, font=("Segoe UI", 10, "bold"), padx=12, pady=6
        )
        sync_btn.pack(side=tk.LEFT, padx=(0, 10))

        web_btn = tk.Button(
            btn_frame, text="📖 Open Web Catalog", command=self._open_web_catalog,
            bg="#21262d", fg=self.accent_color, activebackground=self.accent_color,
            relief=tk.FLAT, font=("Segoe UI", 10, "bold"), padx=12, pady=6
        )
        web_btn.pack(side=tk.LEFT, padx=(0, 10))

        folder_btn = tk.Button(
            btn_frame, text="📁 Open Shared Folder", command=self._open_shared_folder,
            bg="#21262d", fg=self.text_color, activebackground=self.accent_color,
            relief=tk.FLAT, font=("Segoe UI", 10), padx=10, pady=6
        )
        folder_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 5. Console / Status Output Box
        console_frame = ttk.Frame(self, style="Surface.TFrame", padding=10)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        self.console = tk.Text(
            console_frame, bg="#05070a", fg="#c9d1d9",
            insertbackground="#ffffff", font=("Consolas", 9),
            relief=tk.FLAT, wrap=tk.WORD, highlightthickness=1,
            highlightbackground=self.border_color
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        self.log_message("[+] Player Expansion Manager ready.")
        self.log_message(f"[*] Package location: {BASE_DIR}")
        self._check_package_status()

    def log_message(self, msg: str):
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)

    def _check_package_status(self):
        if os.path.exists(CDB_FILE):
            size_kb = os.path.getsize(CDB_FILE) / 1024
            self.log_message(f"   • Custom Card Database: custom_cards.cdb ({size_kb:.1f} KB)")
        else:
            self.log_message("   • [!] Warning: custom_cards.cdb is missing from expansions/")

        if os.path.exists(SCRIPTS_DIR):
            scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")]
            self.log_message(f"   • Lua Effect Scripts: {len(scripts)} scripts ready.")

        if os.path.exists(DECKS_DIR):
            decks = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")]
            self.log_message(f"   • Character Decks: {len(decks)} decklists ready.")

    def _detect_initial_path(self):
        # Import candidate detection logic from sync_client
        try:
            import sync_client
            detected = sync_client.find_game_directory()
            if detected:
                self.client_dir.set(detected)
                self.log_message(f"[+] Auto-detected EDOPro game directory: {detected}")
            else:
                self.log_message("[!] EDOPro not auto-detected. Please click 'Browse...' to select your game folder.")
        except Exception:
            pass

    def _browse_directory(self):
        chosen = filedialog.askdirectory(title="Select your EDOPro or YGOPro folder", initialdir=os.path.expanduser("~"))
        if chosen:
            self.client_dir.set(chosen)
            self.log_message(f"[+] Selected game directory: {chosen}")

    def _copy_connection_info(self):
        info = f"Host: {self.server_ip.get().strip()} | Port: {self.server_port.get().strip()}"
        self.clipboard_clear()
        self.clipboard_append(info)
        self.log_message(f"[+] Copied to clipboard: {info}")
        messagebox.showinfo("Copied", f"Connection details copied to clipboard:\n\n{info}\n\nPaste into EDOPro -> Multiplayer -> Direct Connect.")

    def _open_web_catalog(self):
        host = self.server_ip.get().strip() or "localhost"
        url = f"http://{host}:{DEFAULT_WEB_PORT}"
        self.log_message(f"[*] Opening Web Card Catalog at {url}...")
        webbrowser.open(url)

    def _open_shared_folder(self):
        if sys.platform == "win32":
            os.startfile(BASE_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", BASE_DIR])
        else:
            subprocess.Popen(["xdg-open", BASE_DIR])

    def _sync_expansions_thread(self):
        cdir = self.client_dir.get().strip()
        if not cdir or not os.path.isdir(cdir):
            messagebox.showerror("Error", "Please select a valid EDOPro/YGOPro game client directory first.")
            return

        def worker():
            self.log_message(f"\n[*] Starting synchronization to {cdir}...")
            try:
                import sync_client
                sync_client.install_to_client(cdir)
                self.log_message("[+] Synchronization completed successfully!")
                self.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Cards, scripts, and decks have been installed into:\n{cdir}\n\nYou can now open EDOPro and duel!"
                ))
            except Exception as e:
                self.log_message(f"[-] Error installing expansions: {e}")
                self.after(0, lambda: messagebox.showerror("Sync Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()


def main():
    app = PlayerClientApp()
    app.mainloop()


if __name__ == "__main__":
    main()
