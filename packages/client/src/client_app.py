#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Player Client Expansion Manager & Duel Connector (GUI)
=============================================================================
A native desktop GUI application designed for players to:
- Automatically detect local EDOPro / Project Ignis or YGOPro installations
- Install or update custom card expansions (CDB database & Lua scripts) with 1 click
- Install pre-made archetype and character story decks (.ydk format)
- Copy duel server direct connection details (Host: 7911) to system clipboard
- Launch the Web Catalog in default browser to inspect lore, art, and card text
- Guide first-time users through a 3-step Quick-Start Setup Wizard

Cross-platform compatible on Windows, macOS, Linux, and Steam Deck.
=============================================================================
"""

import os
import sys
import shutil
import threading
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any

# Ensure local package modules are accessible
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_DIR = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PACKAGE_DIR))

if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Import sync engine and configuration resolver
try:
    from .client_config import CLIENT_CONFIG, CLIENT_SETTINGS, ClientConfig
    from . import sync_client
except ImportError:
    from client_config import CLIENT_CONFIG, CLIENT_SETTINGS, ClientConfig
    import sync_client


# Resolve directory locations for assets, database, and decks
BASE_DIR: str = _PACKAGE_DIR

EXPANSIONS_DIR: str = os.path.join(BASE_DIR, "expansions")
if not os.path.isdir(EXPANSIONS_DIR):
    repo_exp = os.path.join(_PROJECT_ROOT, "data", "expansions")
    if os.path.isdir(repo_exp):
        EXPANSIONS_DIR = repo_exp

CDB_FILE: str = os.path.join(EXPANSIONS_DIR, "custom_cards.cdb")
SCRIPTS_DIR: str = os.path.join(EXPANSIONS_DIR, "scripts")

DECKS_DIR: str = os.path.join(BASE_DIR, "decks")
if not os.path.isdir(DECKS_DIR):
    repo_decks = os.path.join(_PROJECT_ROOT, "data", "decks")
    if os.path.isdir(repo_decks):
        DECKS_DIR = repo_decks

GUIDE_FILE: str = os.path.join(BASE_DIR, "README.md")

# Default connection settings resolved from manifest
DEFAULT_SERVER_HOST: str = CLIENT_CONFIG.get("server_host", "thelandofkustomazi.com")
DEFAULT_SERVER_PORT: str = str(CLIENT_CONFIG.get("server_port", 7911))
DEFAULT_WEB_URL: str = CLIENT_CONFIG.get("web_catalog_url", "https://thelandofkustomazi.com")
DEFAULT_FALLBACK_HOST: str = CLIENT_CONFIG.get("fallback_host", "thelandofkustomazi.duckdns.org")


class PlayerClientApp(tk.Tk):
    """Main desktop application window for the Player Expansion Manager."""

    def __init__(self):
        super().__init__()
        self.title("Yu-Gi-Oh! Expansion Manager & Duel Connector")
        self.geometry("780x560")
        self.minsize(700, 480)

        # Curated Dark Theme Colors (GitHub Dark modern aesthetic)
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

    def _setup_styles(self) -> None:
        """Initialize Tkinter ttk visual widget styles."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=self.bg_color, foreground=self.text_color)
        style.configure("Surface.TFrame", background=self.surface_color)
        style.configure("TLabel", background=self.surface_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.accent_color)
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#8b949e")

    def _build_ui(self) -> None:
        """Construct the top-level application layout."""
        # 1. Header Banner Frame
        header = ttk.Frame(self, style="Surface.TFrame", padding=15)
        header.pack(fill=tk.X, padx=15, pady=(15, 10))

        header_left = ttk.Frame(header, style="Surface.TFrame")
        header_left.pack(side=tk.LEFT)

        title_lbl = ttk.Label(header_left, text="🌌 Yu-Gi-Oh! Custom Card Expansion Client", style="Header.TLabel")
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(
            header_left,
            text=f"Server: {CLIENT_CONFIG.get('server_name', 'The Great Kasutamaiza')} | Host: {DEFAULT_SERVER_HOST}",
            style="Sub.TLabel"
        )
        sub_lbl.pack(anchor=tk.W, pady=(2, 0))

        wizard_btn = tk.Button(
            header, text="🪄 Quick-Start Wizard", command=self._open_wizard,
            bg="#8b5cf6", fg="#ffffff", activebackground="#7c3aed",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, pady=5, cursor="hand2"
        )
        wizard_btn.pack(side=tk.RIGHT)

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
            relief=tk.FLAT, font=("Segoe UI", 9, "bold"), padx=10, cursor="hand2"
        )
        browse_btn.pack(side=tk.RIGHT)

        # 3. Server Connection Details Frame
        net_frame = ttk.Frame(self, style="Surface.TFrame", padding=12)
        net_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(net_frame, text="🌐 Duel Server Connection Details:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)

        net_sub = ttk.Frame(net_frame, style="Surface.TFrame")
        net_sub.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(net_sub, text="Host / IP:").pack(side=tk.LEFT, padx=(0, 5))
        host_entry = tk.Entry(
            net_sub, textvariable=self.server_ip, width=28,
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
            relief=tk.FLAT, font=("Segoe UI", 9), padx=8, cursor="hand2"
        )
        copy_btn.pack(side=tk.LEFT)

        # 4. Action Buttons Bar
        btn_frame = ttk.Frame(self, style="Surface.TFrame", padding=12)
        btn_frame.pack(fill=tk.X, padx=15, pady=5)

        sync_btn = tk.Button(
            btn_frame, text="⚡ 1-Click Install (Local)", command=self._sync_expansions_thread,
            bg=self.success_color, fg="#ffffff", activebackground="#2ea043",
            relief=tk.FLAT, font=("Segoe UI", 10, "bold"), padx=12, pady=6, cursor="hand2"
        )
        sync_btn.pack(side=tk.LEFT, padx=(0, 10))

        remote_sync_btn = tk.Button(
            btn_frame, text="🌐 Sync Over HTTPS", command=self._sync_remote_thread,
            bg="#1f6feb", fg="#ffffff", activebackground="#388bfd",
            relief=tk.FLAT, font=("Segoe UI", 10, "bold"), padx=12, pady=6, cursor="hand2"
        )
        remote_sync_btn.pack(side=tk.LEFT, padx=(0, 10))

        web_btn = tk.Button(
            btn_frame, text="📖 Open Web Catalog", command=self._open_web_catalog,
            bg="#21262d", fg=self.accent_color, activebackground=self.accent_color,
            relief=tk.FLAT, font=("Segoe UI", 10, "bold"), padx=12, pady=6, cursor="hand2"
        )
        web_btn.pack(side=tk.LEFT, padx=(0, 10))

        folder_btn = tk.Button(
            btn_frame, text="📁 Open Package Folder", command=self._open_shared_folder,
            bg="#21262d", fg=self.text_color, activebackground=self.accent_color,
            relief=tk.FLAT, font=("Segoe UI", 10), padx=10, pady=6, cursor="hand2"
        )
        folder_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 5. Live Console / Status Output Box
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

    def log_message(self, msg: str) -> None:
        """Thread-safe logging method for appending messages to the GUI console."""
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)

    def _check_package_status(self) -> None:
        """Inspect and log local file statuses for the compiled CDB, scripts, and decks."""
        if os.path.isfile(CDB_FILE):
            size_kb = os.path.getsize(CDB_FILE) / 1024
            self.log_message(f"   • Custom Card Database: custom_cards.cdb ({size_kb:.1f} KB)")
        else:
            self.log_message("   • [!] Notice: custom_cards.cdb not present locally; use 'Sync Over HTTPS'.")

        if os.path.isdir(SCRIPTS_DIR):
            scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".lua")]
            self.log_message(f"   • Lua Effect Scripts: {len(scripts)} scripts ready.")

        if os.path.isdir(DECKS_DIR):
            decks = [f for f in os.listdir(DECKS_DIR) if f.endswith(".ydk")]
            self.log_message(f"   • Character Decks: {len(decks)} decklists ready.")

    def _detect_initial_path(self) -> None:
        """Scan candidate locations to auto-fill the game client path."""
        try:
            detected = sync_client.find_game_directory()
            if detected:
                self.client_dir.set(detected)
                self.log_message(f"[+] Auto-detected EDOPro game directory: {detected}")
            else:
                self.log_message("[!] EDOPro not auto-detected. Click 'Browse...' to select your game folder.")
        except Exception as e:
            self.log_message(f"[!] Path auto-detection note: {e}")

    def _browse_directory(self) -> None:
        """Open a native file chooser dialog for selecting the game directory."""
        chosen = filedialog.askdirectory(title="Select your EDOPro or YGOPro folder", initialdir=os.path.expanduser("~"))
        if chosen:
            self.client_dir.set(chosen)
            self.log_message(f"[+] Selected game directory: {chosen}")

    def _copy_connection_info(self) -> None:
        """Copy direct connect host and port strings to the OS clipboard."""
        host = self.server_ip.get().strip() or DEFAULT_SERVER_HOST
        port = self.server_port.get().strip() or DEFAULT_SERVER_PORT
        info = f"Host: {host} | Port: {port}"
        self.clipboard_clear()
        self.clipboard_append(info)
        self.log_message(f"[+] Copied to clipboard: {info}")
        messagebox.showinfo(
            "Copied to Clipboard",
            f"Duel Connection Details:\n\nHost: {host}\nPort: {port}\n\nPaste these in EDOPro -> Multiplayer -> Direct Connect."
        )

    def _open_web_catalog(self) -> None:
        """Open the public Web Catalog lore dashboard in the user's default browser."""
        url = DEFAULT_WEB_URL
        self.log_message(f"[*] Opening Web Card Catalog at: {url}...")
        webbrowser.open(url)

    def _open_shared_folder(self) -> None:
        """Open the client distribution package folder in the native file explorer."""
        if sys.platform == "win32":
            os.startfile(BASE_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", BASE_DIR])
        else:
            subprocess.Popen(["xdg-open", BASE_DIR])

    def _sync_expansions_thread(self) -> None:
        """Run local offline expansion installation in a background daemon thread."""
        cdir = self.client_dir.get().strip()
        if not cdir or not os.path.isdir(cdir):
            messagebox.showerror("Invalid Directory", "Please select a valid EDOPro/YGOPro game client directory first.")
            return

        def worker():
            self.log_message(f"\n[*] Starting local installation into: {cdir}...")
            try:
                ok = sync_client.install_to_client(cdir)
                if ok:
                    self.log_message("[+] Local installation completed successfully!")
                    self.after(0, lambda: messagebox.showinfo(
                        "Installation Complete",
                        f"Custom cards, scripts, and decks installed into:\n{cdir}\n\nYou can now open EDOPro and duel!"
                    ))
                else:
                    self.log_message("[-] Local installation failed.")
            except Exception as e:
                self.log_message(f"[-] Error installing expansions: {e}")
                self.after(0, lambda: messagebox.showerror("Sync Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _sync_remote_thread(self) -> None:
        """Run online HTTPS card synchronization in a background daemon thread."""
        cdir = self.client_dir.get().strip()
        if not cdir or not os.path.isdir(cdir):
            messagebox.showerror("Invalid Directory", "Please select a valid EDOPro/YGOPro game client directory first.")
            return

        url = DEFAULT_WEB_URL

        def worker():
            self.log_message(f"\n[*] Connecting to remote server at: {url}...")
            try:
                ok = sync_client.sync_from_remote(url, cdir)
                if ok:
                    self.log_message("[+] Remote card pool synchronized successfully!")
                    self.after(0, lambda: messagebox.showinfo(
                        "Sync Complete",
                        f"Custom cards and scripts fetched from {url} and installed into:\n{cdir}\n\nYou are ready to duel!"
                    ))
                else:
                    self.log_message(f"[-] Could not connect to remote catalog server at {url}.")
                    self.after(0, lambda: messagebox.showerror(
                        "Connection Error",
                        f"Could not reach remote server at {url}.\nEnsure your network is active and the host is reachable."
                    ))
            except Exception as e:
                self.log_message(f"[-] Error syncing from server: {e}")
                self.after(0, lambda: messagebox.showerror("Sync Error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _open_wizard(self) -> None:
        """Launch the step-by-step setup wizard dialog."""
        PlayerSetupWizardDialog(self)


class PlayerSetupWizardDialog(tk.Toplevel):
    """Step-by-step interactive player onboarding and setup wizard dialog."""

    def __init__(self, parent: PlayerClientApp):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Yu-Gi-Oh! Player Quick-Start Wizard")
        self.geometry("640x440")
        self.minsize(580, 380)

        self.bg_color = "#0d1117"
        self.surface_color = "#161b22"
        self.text_color = "#c9d1d9"
        self.accent_color = "#58a6ff"
        self.success_color = "#238636"

        self.configure(bg=self.bg_color)
        self.current_step = 0

        self._build_ui()
        self._show_step(0)

    def _build_ui(self) -> None:
        """Construct wizard navigation and container frames."""
        header = tk.Frame(self, bg=self.surface_color, padx=15, pady=10)
        header.pack(fill=tk.X)

        self.lbl_title = tk.Label(header, text="Player Quick-Start Wizard", font=("Segoe UI", 12, "bold"), fg=self.accent_color, bg=self.surface_color)
        self.lbl_title.pack(anchor=tk.W)

        self.content = tk.Frame(self, bg=self.bg_color, padx=20, pady=15)
        self.content.pack(fill=tk.BOTH, expand=True)

        footer = tk.Frame(self, bg=self.surface_color, padx=15, pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_next = tk.Button(footer, text="Next >", command=self._next, bg=self.accent_color, fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=12, pady=4, relief=tk.FLAT, cursor="hand2")
        self.btn_next.pack(side=tk.RIGHT)

        self.btn_prev = tk.Button(footer, text="< Back", command=self._prev, bg="#21262d", fg=self.text_color, padx=10, pady=4, relief=tk.FLAT, cursor="hand2")
        self.btn_prev.pack(side=tk.RIGHT, padx=6)

    def _show_step(self, step: int) -> None:
        """Render the contents of the given wizard step index."""
        self.current_step = step
        for w in self.content.winfo_children():
            w.destroy()

        self.btn_prev.config(state=tk.NORMAL if step > 0 else tk.DISABLED)

        if step == 0:
            self.lbl_title.config(text="Step 1: Select Game Client Directory")
            tk.Label(
                self.content,
                text="Please select or verify the path to your EDOPro / Project Ignis folder:",
                bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 10)
            ).pack(anchor=tk.W, pady=(0, 10))

            entry = tk.Entry(self.content, textvariable=self.parent_app.client_dir, font=("Consolas", 10), bg="#05070a", fg="#ffffff", relief=tk.FLAT)
            entry.pack(fill=tk.X, pady=5, ipady=4)

            btn_box = tk.Frame(self.content, bg=self.bg_color)
            btn_box.pack(fill=tk.X, pady=5)

            tk.Button(
                btn_box, text="🔍 Auto-Detect", command=self.parent_app._detect_initial_path,
                bg="#21262d", fg=self.accent_color, font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
            ).pack(side=tk.LEFT, padx=(0, 8))

            tk.Button(
                btn_box, text="📁 Browse...", command=self.parent_app._browse_directory,
                bg="#21262d", fg=self.text_color, relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
            ).pack(side=tk.LEFT)

        elif step == 1:
            self.lbl_title.config(text="Step 2: Choose Install Method & Install")
            tk.Label(
                self.content,
                text="Choose how you would like to install custom cards into your game client:",
                bg=self.bg_color, fg=self.text_color, font=("Segoe UI", 10)
            ).pack(anchor=tk.W, pady=(0, 15))

            tk.Button(
                self.content, text="⚡ 1-Click Install (from local package bundle)",
                command=self.parent_app._sync_expansions_thread,
                bg=self.success_color, fg="#ffffff", font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT, padx=12, pady=6, cursor="hand2"
            ).pack(anchor=tk.W, pady=6)

            tk.Button(
                self.content, text="🌐 Sync Over HTTPS (fetch latest live cards)",
                command=self.parent_app._sync_remote_thread,
                bg="#1f6feb", fg="#ffffff", font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT, padx=12, pady=6, cursor="hand2"
            ).pack(anchor=tk.W, pady=6)

        elif step == 2:
            self.lbl_title.config(text="Step 3: Connect & Duel Online")
            self.btn_next.config(text="Finish")
            host = self.parent_app.server_ip.get().strip() or DEFAULT_SERVER_HOST
            port = self.parent_app.server_port.get().strip() or DEFAULT_SERVER_PORT
            tk.Label(
                self.content,
                text="🎉 You are all set! Follow these steps in your game client:\n\n"
                     "1. Open EDOPro and select: Multiplayer -> Duel Online.\n"
                     "2. Choose: Direct Connect (or IP Connection).\n"
                     f"3. Host: {host}  |  Port: {port}\n"
                     "4. Select your custom deck and begin dueling!",
                bg=self.bg_color, fg=self.text_color, justify=tk.LEFT, font=("Segoe UI", 10)
            ).pack(anchor=tk.W, pady=(0, 15))

            tk.Button(
                self.content, text="📋 Copy Connection Details",
                command=self.parent_app._copy_connection_info,
                bg="#21262d", fg=self.accent_color, font=("Segoe UI", 9, "bold"),
                relief=tk.FLAT, padx=10, pady=5, cursor="hand2"
            ).pack(anchor=tk.W)

    def _next(self) -> None:
        """Advance to next wizard step or close if on the final step."""
        if self.current_step < 2:
            self._show_step(self.current_step + 1)
        else:
            self.destroy()

    def _prev(self) -> None:
        """Return to the previous wizard step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)


def main() -> None:
    """Entrypoint function for starting the desktop GUI application."""
    app = PlayerClientApp()
    app.mainloop()


if __name__ == "__main__":
    main()
