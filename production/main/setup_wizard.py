#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform Manager - Host Server Setup Wizard Launcher
=============================================================================
Entry point wrapper delegating to `production.main.gui.setup_wizard`.
Maintained at `production/main/setup_wizard.py` for backward compatibility.
=============================================================================
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from production.main.gui.setup_wizard import (
    build_gui_wizard,
    run_cli_wizard,
    save_env_values,
    load_env_values,
    main,
)

__all__ = [
    "build_gui_wizard",
    "run_cli_wizard",
    "save_env_values",
    "load_env_values",
    "main",
]

if __name__ == "__main__":
    main()
