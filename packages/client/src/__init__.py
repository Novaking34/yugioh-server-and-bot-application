"""
=============================================================================
Yu-Gi-Oh! Player Client Subsystem Source Package
=============================================================================
Provides client-side tools for players:
- `client_app`: Desktop GUI Expansion Manager and connection helper
- `sync_client`: Cross-platform CLI synchronizer and EDOPro path detector
=============================================================================
"""

from .sync_client import (
    CLIENT_CONFIG,
    resolve_config_manifest,
    find_game_directory,
    sync_from_remote,
    install_to_client,
)

from .client_app import (
    PlayerClientApp,
    PlayerSetupWizardDialog,
    main as run_client_gui,
)

__all__ = [
    "CLIENT_CONFIG",
    "resolve_config_manifest",
    "find_game_directory",
    "sync_from_remote",
    "install_to_client",
    "PlayerClientApp",
    "PlayerSetupWizardDialog",
    "run_client_gui",
]
