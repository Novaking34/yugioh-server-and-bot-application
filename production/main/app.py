#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform Manager - Desktop GUI Control Panel Launcher
=============================================================================
Entry point wrapper delegating to `production.main.gui.app`.
Maintained at `production/main/app.py` for backward compatibility with:
- `manage.py app` / `./manage.sh app` / `manage.bat app`
- Platform path definitions (`config.paths.APP_PY_PATH`)
=============================================================================
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from production.main.gui.app import YugiohPlatformApp, main

__all__ = ["YugiohPlatformApp", "main"]

if __name__ == "__main__":
    main()
