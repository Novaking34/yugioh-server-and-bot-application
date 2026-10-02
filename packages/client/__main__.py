#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Player Client Package CLI & GUI Launcher
=============================================================================
Enables direct package execution via Python:
    python3 -m packages.client          # Launches Player GUI
    python3 -m packages.client --sync   # Runs CLI Synchronizer
=============================================================================
"""

import sys
import os

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(_PACKAGE_DIR, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--sync", "-s", "--install", "-i"):
        import sync_client
        sys.argv.pop(1)
        sync_client.main()
    else:
        import client_app
        client_app.main()
