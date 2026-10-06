@echo off
REM =============================================================================
REM BLOCK 1: METADATA BLOCK
REM =============================================================================
REM Module: manage.bat
REM Architecture: Imperative Windows Host Wrapper
REM Domain: Environment Resolution & Operational Entry (Windows)
REM Description: Windows batch controller and launcher wrapper for manage.py.
REM              Resolves Python runtime environment and passes all commands
REM              transparently to the Python master controller.
REM
REM Invariants:
REM   - Resolves paths relative to batch script directory (%~dp0).
REM   - Prioritizes virtualenv (venv\Scripts\python.exe) over system Python.
REM   - Returns deterministic process error levels to caller.
REM
REM Common Commands:
REM   manage.bat status       - Display live platform, DB, and container status
REM   manage.bat sync         - Synchronize custom card database & Lua scripts
REM   manage.bat package      - Build client zip & server tarball release packages
REM   manage.bat app          - Launch the Desktop GUI Platform Manager
REM   manage.bat web          - Launch the FastAPI Web Catalog on localhost:8000
REM   manage.bat bot          - Launch the Discord Story & Duel Bot
REM   manage.bat test         - Run the Pytest test suite
REM =============================================================================

REM =============================================================================
REM BLOCK 2: OPENING BLOCK (Environment Configuration & Path Definitions)
REM =============================================================================
title Yu-Gi-Oh! Platform Manager
setlocal enabledelayedexpansion

REM Resolve project root directory from batch file location
set "BASE_DIR=%~dp0"
set "VENV_PYTHON=%BASE_DIR%venv\Scripts\python.exe"

REM =============================================================================
REM BLOCK 3: BODY BLOCK (Interpreter Detection & Verification)
REM =============================================================================
if exist "%VENV_PYTHON%" (
    set "RUN_PYTHON=%VENV_PYTHON%"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "RUN_PYTHON=python"
    ) else (
        echo [-] Error: Python was not found in PATH or in the venv\ directory.
        echo     Please install Python 3.9+ from https://www.python.org/
        pause
        exit /b 1
    )
)

REM =============================================================================
REM BLOCK 4: CLOSING BLOCK (Command Execution & Process Exit)
REM =============================================================================
"%RUN_PYTHON%" "%BASE_DIR%manage.py" %*
exit /b %ERRORLEVEL%
