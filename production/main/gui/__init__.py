"""
=============================================================================
Yu-Gi-Oh! Platform - Graphical User Interface Subsystem (production.main.gui)
=============================================================================
Encapsulates administrative desktop applications and setup wizards:
- `YugiohPlatformApp`: Main desktop Platform Manager control panel.
- `ServerSetupWizard`: Interactive Tkinter configuration wizard.
- `run_cli_wizard`: Interactive terminal CLI wizard for headless servers.
- `build_gui_wizard`: Factory returning the Tkinter setup wizard class.
- `save_env_values`, `load_env_values`: Non-destructive .env persistence.
=============================================================================
"""

from .app import YugiohPlatformApp
from .setup_wizard import (
    build_gui_wizard,
    run_cli_wizard,
    save_env_values,
    load_env_values,
)

__all__ = [
    "YugiohPlatformApp",
    "build_gui_wizard",
    "run_cli_wizard",
    "save_env_values",
    "load_env_values",
]
